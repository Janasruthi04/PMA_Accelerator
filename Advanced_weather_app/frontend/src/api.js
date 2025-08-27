const BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:5000";

async function http(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const ct = res.headers.get("content-type") || "";
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      if (ct.includes("application/json")) {
        const j = await res.json();
        msg = j.error || msg;
      } else {
        msg = await res.text();
      }
    } catch {}
    throw new Error(msg);
  }
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export const api = {
  list: () => http("GET", "/api/records"),
  create: (payload) => http("POST", "/api/records", payload),
  update: (id, payload) => http("PUT", `/api/records/${id}`, payload),
  remove: (id) => http("DELETE", `/api/records/${id}`),
  export: (format) => window.open(`${BASE}/api/export?format=${format || "csv"}`, "_blank"),
};
