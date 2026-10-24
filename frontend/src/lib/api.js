// Talks to backend/api/main.py (FastAPI). See README section 5 for the contract.
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`${options?.method || "GET"} ${path} failed: ${res.status}`);
  }
  return res.json();
}

/** POST /scan {url} -> ScanResult */
export function postScan(url) {
  return request("/scan", { method: "POST", body: JSON.stringify({ url }) });
}

/** GET /scans -> ScanResult[] */
export function getScans() {
  return request("/scans");
}

/** GET /scans/{id} -> ScanResult */
export function getScan(id) {
  return request(`/scans/${id}`);
}

export { API_BASE };
