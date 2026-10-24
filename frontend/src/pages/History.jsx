import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getScans, searchFindings } from "../lib/api";
import ScoreTile from "../components/ScoreTile";
import SeverityBadge from "../components/SeverityBadge";
import { formatDate } from "../lib/format";

export default function History() {
  const [scans, setScans] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    getScans()
      .then(setScans)
      .catch(() => setError("Couldn't load scan history. Is the API running?"));
  }, []);

  // Atlas Search over every website's latest findings, e.g. "tracking cookies" or "no ICO".
  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return setResults(null);
    setSearching(true);
    try {
      setResults(await searchFindings(query.trim()));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!scans) return <p className="loading-text">Loading…</p>;

  return (
    <div className="history">
      <h1>Scan history</h1>

      <form className="scan-form" onSubmit={handleSearch} role="search">
        <label htmlFor="finding-search" className="visually-hidden">
          Search all findings
        </label>
        <input
          id="finding-search"
          type="search"
          placeholder="Search all findings, e.g. tracking cookies, data controller, contrast"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={searching}>
          {searching ? "Searching…" : "Search"}
        </button>
      </form>

      {results !== null && (
        <section aria-live="polite">
          <h2>
            {results.length} finding{results.length === 1 ? "" : "s"} for “{query}”
          </h2>
          <ul className="history-list">
            {results.map((r, i) => (
              <li key={`${r.scan_id}-${i}`} className="history-list__item">
                <Link to={`/report/${r.scan_id}`}>
                  <div className="history-list__url">
                    <strong>{r.title}</strong>
                    <span className="history-list__date">
                      {r.url} · {formatDate(r.scanned_at)}
                    </span>
                  </div>
                  <SeverityBadge severity={r.severity} />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {scans.length === 0 ? (
        <p>No scans yet.</p>
      ) : (
        <>
          {results !== null && <h2>Latest scan of each website</h2>}
          <ul className="history-list">
            {scans.map((scan) => {
              const scanId = scan.id ?? scan._id;
              const inner = (
                <>
                  <div className="history-list__url">
                    <strong>{scan.url}</strong>
                    <span className="history-list__date">{formatDate(scan.scanned_at)}</span>
                  </div>
                  <ScoreTile label="Overall" score={scan.scores?.overall} />
                </>
              );
              return (
                <li key={scanId ?? scan.url + scan.scanned_at} className="history-list__item">
                  {scanId ? <Link to={`/report/${scanId}`}>{inner}</Link> : <div>{inner}</div>}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}
