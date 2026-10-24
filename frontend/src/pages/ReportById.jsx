import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getScan } from "../lib/api";
import ReportView from "../components/ReportView";

export default function ReportById() {
  const { id } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setResult(null);
    setError("");
    getScan(id)
      .then((data) => {
        if (!cancelled) setResult(data);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load this scan. Is the API running?");
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <div className="empty-state">
        <p>{error}</p>
        <Link to="/history">Back to history</Link>
      </div>
    );
  }

  if (!result) return <p className="loading-text">Loading scan…</p>;

  return <ReportView result={result} />;
}
