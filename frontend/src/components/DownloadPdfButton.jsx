import { useState } from "react";
import { downloadReportPdf } from "../lib/pdf";

export default function DownloadPdfButton({ result, usingMock }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleClick() {
    setBusy(true);
    setFailed(false);
    try {
      await downloadReportPdf(result, { usingMock });
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pdf-action">
      <button type="button" className="btn-secondary" onClick={handleClick} disabled={busy}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 4v11" />
          <path d="M7 10l5 5 5-5" />
          <path d="M5 20h14" />
        </svg>
        {busy ? "Preparing PDF…" : "Download PDF"}
      </button>
      {failed && <p className="pdf-action__error">Couldn't create the PDF. Please try again.</p>}
    </div>
  );
}
