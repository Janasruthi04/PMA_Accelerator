# Advanced Weather App (Full-Stack)

A small full‑stack project that demonstrates CRUD with persistence, validation,
API integration (Open‑Meteo geocoding + weather), and data export.

## Tech
- Backend: Flask, SQLAlchemy (SQLite DB), python‑dotenv, requests, Flask‑CORS
- Frontend: React (create‑react‑app structure), fetch API
- Free Weather API: https://open-meteo.com (no key required)

## Quick start

### 1) Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # optional: edit PORT, CORS, etc.
python app.py
```
Backend runs at `http://127.0.0.1:5000` by default.

### 2) Frontend
```bash
cd ../frontend
npm install
npm start
```
Front-end expects the backend at `http://127.0.0.1:5000`. To change, set `REACT_APP_API_BASE`
in `frontend/.env`.

## Endpoints (Backend)

- `GET    /api/records` — list all records
- `POST   /api/records` — create (body: location, start_date, end_date)
- `PUT    /api/records/<id>` — update location and/or dates
- `DELETE /api/records/<id>` — delete record
- `GET    /api/export?format=csv|json|md` — export all records

### Example create payload
```json
{
  "location": "Delhi",
  "start_date": "2025-08-24",
  "end_date": "2025-08-25"
}
```

## Notes
- Date validation ensures `YYYY-MM-DD` and `start_date <= end_date`.
- Location is validated via Open‑Meteo Geocoding (supports fuzzy queries).
- Temperatures are computed as the mean of each day’s min & max over the range.
- All server errors are returned as JSON with a helpful message.
