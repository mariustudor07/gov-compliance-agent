import { useLocation, Link } from "react-router-dom";
import ReportView from "../components/ReportView";

export default function Report() {
  const location = useLocation();
  let result = location.state?.result;
  let usingMock = location.state?.usingMock ?? false;

  // Survive a page refresh by falling back to the last cached result.
  if (!result) {
    const cached = sessionStorage.getItem("govcheck:lastResult");
    if (cached) result = JSON.parse(cached);
  }

  if (!result) {
    return (
      <div className="empty-state">
        <p>No scan loaded yet.</p>
        <Link to="/">Scan a URL</Link>
      </div>
    );
  }

  return <ReportView result={result} usingMock={usingMock} />;
}
