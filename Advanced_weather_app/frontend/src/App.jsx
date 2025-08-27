import React, { useEffect, useState } from "react";
import { api } from "./api";
import RecordItem from "./components/RecordItem";

export default function App(){
  const [form, setForm] = useState({ location: "", start_date: "", end_date: "" });
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try{
      const j = await api.list();
      setRows(j.data);
    }catch(e){ setError(String(e.message || e)); }
  };

  useEffect(()=>{ load(); }, []);

  const add = async () => {
    setError(""); setNotice("");
    if(!form.location || !form.start_date || !form.end_date){
      setError("Please fill location and both dates.");
      return;
    }
    try{
      const j = await api.create(form);
      setRows([j.data, ...rows]);
      setNotice(`Added: ${j.data.location}`);
      setForm({ location: "", start_date: "", end_date: "" });
    }catch(e){ setError(String(e.message || e)); }
  };

  const update = async (id, payload) => {
    setError(""); setNotice("");
    try{
      const j = await api.update(id, payload);
      setRows(rows.map(r => r.id === id ? j.data : r));
      setNotice("Record updated.");
    }catch(e){ setError(String(e.message || e)); }
  };

  const remove = async (id) => {
    setError(""); setNotice("");
    try{
      await api.remove(id);
      setRows(rows.filter(r => r.id !== id));
      setNotice("Deleted.");
    }catch(e){ setError(String(e.message || e)); }
  };

  return (
    <div style={{maxWidth:900, margin:"0 auto"}}>
      <h1>Advanced Weather App</h1>

      {error && <div className="err">{error}</div>}
      {notice && <div className="success">{notice}</div>}

      <div className="card">
        <div className="row">
          <div className="stack" style={{flex:1}}>
            <label>Location</label>
            <input value={form.location} placeholder="City, Zip, Landmark..."
                   onChange={e=>setForm({...form, location: e.target.value})}/>
          </div>
          <div className="stack" style={{flex:1}}>
            <label>Start Date</label>
            <input type="date" value={form.start_date}
                   onChange={e=>setForm({...form, start_date:e.target.value})}/>
          </div>
          <div className="stack" style={{flex:1}}>
            <label>End Date</label>
            <input type="date" value={form.end_date}
                   onChange={e=>setForm({...form, end_date:e.target.value})}/>
          </div>
        </div>
        <div className="row">
          <button onClick={add}>Add Weather</button>
          <button onClick={()=>api.export("csv")}>Export CSV</button>
          <button onClick={()=>api.export("json")}>Export JSON</button>
          <button onClick={()=>api.export("md")}>Export MD</button>
        </div>
      </div>

      <div className="list">
        {rows.map(rec => (
          <RecordItem key={rec.id} rec={rec} onUpdate={update} onDelete={remove}/>
        ))}
      </div>
    </div>
  );
}
