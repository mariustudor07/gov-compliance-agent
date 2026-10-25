// Talks to backend/api/main.py (FastAPI). See README section 5 for the contract.
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

// The deployed site has no backend unless VITE_API_BASE is set. Calling
// 127.0.0.1 from a public page makes Chrome hold the request behind a
// local-network permission prompt, so the scan hangs instead of failing.
const NO_BACKEND =
  !import.meta.env.VITE_API_BASE &&
  !["localhost", "127.0.0.1"].includes(window.location.hostname);

async function request(path, options) {
  if (NO_BACKEND) {
    throw new Error("No backend configured for this deployment");
  }
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

/** GET /search?q=... -> [{scan_id, url, scanned_at, title, severity, page}] (Atlas Search over findings) */
export function searchFindings(q) {
  return request(`/search?q=${encodeURIComponent(q)}`);
}

export { API_BASE };
