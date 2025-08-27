import os
import math
from datetime import datetime
from typing import Optional, Tuple

import requests
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

from models import Base, WeatherRecord
import export_utils

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*").split(",")}})

DB_URL = "sqlite:///weather.db"
engine = create_engine(DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# ----------------------- Helpers -----------------------

def parse_date(s: str) -> datetime.date:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        raise ValueError("Date must be YYYY-MM-DD")

def validate_date_range(start_s: str, end_s: str) -> Tuple[datetime.date, datetime.date]:
    start = parse_date(start_s)
    end = parse_date(end_s)
    if start > end:
        raise ValueError("start_date cannot be after end_date")
    return start, end

def geocode_location(query: str) -> Optional[dict]:
    # Open-Meteo Geocoding API — supports fuzzy search, no key required
    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = requests.get(url, params={"name": query, "count": 1})
    if resp.status_code != 200:
        return None
    data = resp.json()
    results = data.get("results") or []
    return results[0] if results else None

def fetch_range_avg_temp(lat: float, lon: float, start_date: str, end_date: str) -> Tuple[Optional[float], Optional[str]]:
    # Daily min/max; compute average of daily means
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        return None, None
    j = resp.json()
    daily = j.get("daily", {})
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    if not tmax or not tmin or len(tmax) != len(tmin):
        return None, None
    means = [(hi + lo) / 2.0 for hi, lo in zip(tmax, tmin)]
    avg = sum(means) / len(means)
    # optional short description
    desc = f"avg of daily means over {len(means)} day(s)"
    return round(avg, 1), desc

def bad_request(msg: str, status=400):
    return jsonify({"ok": False, "error": msg}), status

# ----------------------- Routes -----------------------

@app.get("/api/health")
def health():
    return {"ok": True, "service": "weather-api"}

@app.get("/api/records")
def list_records():
    with SessionLocal() as s:
        rows = s.execute(select(WeatherRecord).order_by(WeatherRecord.id.desc())).scalars().all()
        return jsonify({"ok": True, "data": [r.to_dict() for r in rows]})

@app.post("/api/records")
def create_record():
    body = request.get_json(silent=True) or {}
    location = (body.get("location") or "").strip()
    start_s = body.get("start_date")
    end_s = body.get("end_date")
    if not location:
        return bad_request("location is required")
    try:
        start, end = validate_date_range(start_s, end_s)
    except ValueError as e:
        return bad_request(str(e))

    geo = geocode_location(location)
    if not geo:
        return bad_request("location not found via geocoding")

    lat, lon = geo["latitude"], geo["longitude"]
    avg, desc = fetch_range_avg_temp(lat, lon, start.isoformat(), end.isoformat())
    if avg is None:
        return bad_request("unable to retrieve weather for that date range")

    rec = WeatherRecord(
        location=f"{geo.get('name')}, {geo.get('country_code')}",
        start_date=start,
        end_date=end,
        avg_temperature_c=avg,
        description=desc,
        latitude=lat,
        longitude=lon,
    )
    with SessionLocal() as s:
        s.add(rec)
        s.commit()
        s.refresh(rec)
        return jsonify({"ok": True, "data": rec.to_dict()}), 201

@app.put("/api/records/<int:rec_id>")
def update_record(rec_id: int):
    body = request.get_json(silent=True) or {}
    new_location = (body.get("location") or "").strip() if "location" in body else None
    new_start = body.get("start_date")
    new_end = body.get("end_date")

    with SessionLocal() as s:
        rec = s.get(WeatherRecord, rec_id)
        if not rec:
            return bad_request("record not found", 404)

        # decide what changed
        if new_start or new_end:
            try:
                start, end = validate_date_range(new_start or rec.start_date.isoformat(),
                                                 new_end or rec.end_date.isoformat())
            except ValueError as e:
                return bad_request(str(e))
        else:
            start, end = rec.start_date, rec.end_date

        if new_location:
            loc_query = new_location
        else:
            loc_query = rec.location

        geo = geocode_location(loc_query)
        if not geo:
            return bad_request("location not found via geocoding")

        lat, lon = geo["latitude"], geo["longitude"]
        avg, desc = fetch_range_avg_temp(lat, lon, start.isoformat(), end.isoformat())
        if avg is None:
            return bad_request("unable to retrieve weather for that date range")

        rec.location = f"{geo.get('name')}, {geo.get('country_code')}"
        rec.start_date = start
        rec.end_date = end
        rec.avg_temperature_c = avg
        rec.description = desc
        rec.latitude = lat
        rec.longitude = lon

        s.add(rec)
        s.commit()
        s.refresh(rec)
        return jsonify({"ok": True, "data": rec.to_dict()})

@app.delete("/api/records/<int:rec_id>")
def delete_record(rec_id: int):
    with SessionLocal() as s:
        rec = s.get(WeatherRecord, rec_id)
        if not rec:
            return bad_request("record not found", 404)
        s.delete(rec)
        s.commit()
        return jsonify({"ok": True})

@app.get("/api/export")
def export_records():
    fmt = (request.args.get("format") or "csv").lower()
    with SessionLocal() as s:
        rows = s.execute(select(WeatherRecord).order_by(WeatherRecord.id.asc())).scalars().all()

    if fmt == "json":
        blob = export_utils.to_json_bytes(rows)
        mime, ext = "application/json", "json"
    elif fmt in ("md", "markdown"):
        blob = export_utils.to_md_bytes(rows)
        mime, ext = "text/markdown", "md"
    else:
        blob = export_utils.to_csv_bytes(rows)
        mime, ext = "text/csv", "csv"

    filename = f"weather_export.{ext}"
    path = os.path.join(os.getcwd(), filename)
    with open(path, "wb") as f:
        f.write(blob)
    return send_file(path, mimetype=mime, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))
    app.run(host="127.0.0.1", port=port)
