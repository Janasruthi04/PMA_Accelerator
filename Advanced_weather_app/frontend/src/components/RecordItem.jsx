import React, { useState } from "react";

export default function RecordItem({ rec, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [location, setLocation] = useState(rec.location);
  const [start, setStart] = useState(rec.start_date);
  const [end, setEnd] = useState(rec.end_date);

  const save = () => {
    onUpdate(rec.id, { location, start_date: start, end_date: end });
    setEditing(false);
  };

  return (
    <div className="item">
      <div style={{maxWidth: "70%"}}>
        <div style={{fontWeight:600}}>{rec.location}</div>
        <div className="small">
          {rec.start_date} → {rec.end_date} &nbsp; • &nbsp;
          <span className="badge">{rec.avg_temperature_c}°C</span> &nbsp;
          <span>{rec.description}</span>
        </div>
        <div className="small">
          Lat/Lon: {rec.latitude?.toFixed?.(3)}, {rec.longitude?.toFixed?.(3)}
        </div>
        {editing && (
          <div className="row" style={{marginTop:8}}>
            <input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Location"/>
            <input type="date" value={start} onChange={e=>setStart(e.target.value)}/>
            <input type="date" value={end} onChange={e=>setEnd(e.target.value)}/>
            <button onClick={save}>Save</button>
            <button onClick={()=>setEditing(false)}>Cancel</button>
          </div>
        )}
      </div>
      <div className="actions">
        <button onClick={()=>setEditing(true)}>Edit</button>
        <button onClick={()=>onDelete(rec.id)}>Delete</button>
        <a href={`https://www.google.com/maps?q=${rec.latitude},${rec.longitude}`} target="_blank" rel="noreferrer">
          <button>Map</button>
        </a>
      </div>
    </div>
  );
}
