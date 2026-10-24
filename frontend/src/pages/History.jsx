import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getScans } from "../lib/api";
import ScoreTile from "../components/ScoreTile";
import { formatDate } from "../lib/format";

export default function History() {
  const [scans, setScans] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getScans()
      .then(setScans)
      .catch(() => setError("Couldn't load scan history. Is the API running?"));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!scans) return <p className="loading-text">Loading…</p>;
  if (scans.length === 0) return <p>No scans yet.</p>;

  return (
    <div className="history">
      <h1>Scan history</h1>
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
    </div>
  );
}
