import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postScan } from "../lib/api";
import LoadingSteps, { ALL_STEPS_MS } from "../components/LoadingSteps";
import HowItWorks from "../components/HowItWorks";
import mockResult from "../mock/example_scan.json";

function normaliseUrl(input) {
  const trimmed = input.trim();
  if (!trimmed) return "";
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    const target = normaliseUrl(url);
    if (!target) {
      setError("Enter a URL to scan.");
      return;
    }

    setError("");
    setLoading(true);

    let result;
    let usingMock = false;
    const started = Date.now();
    try {
      result = await postScan(target);
    } catch {
      // Backend not running yet, so fall back to the example report so the
      // frontend can be built and demoed on its own (README section "Dawan").
      usingMock = true;
      result = { ...mockResult, url: target, scanned_at: new Date().toISOString() };
      // Walk through every scan step first, as a real scan would.
      const remaining = ALL_STEPS_MS - (Date.now() - started);
      if (remaining > 0) await new Promise((resolve) => setTimeout(resolve, remaining));
    }

    setLoading(false);
    sessionStorage.setItem("govcheck:lastResult", JSON.stringify(result));
    navigate("/report", { state: { result, usingMock } });
  }

  return (
    <div className="home">
      <div className="home__hero">
        <span className="eyebrow">AI compliance auditor</span>
        <h1>
          Is your site <span className="gradient-text">government compliant?</span>
        </h1>
        <p className="home__subtitle">
          Paste a UK website URL. We check accessibility, cookies, privacy and security,
          and cite the exact regulation for every issue.
        </p>

        <form className="scan-form" onSubmit={handleSubmit}>
          <input
            type="text"
            inputMode="url"
            placeholder="https://www.example.gov.uk"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading}>
            {loading ? "Scanning…" : "Scan"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}
      </div>

      {loading && <LoadingSteps />}

      {!loading && <HowItWorks />}
    </div>
  );
}
