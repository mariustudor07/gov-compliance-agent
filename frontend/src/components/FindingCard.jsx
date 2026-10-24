import SeverityBadge from "./SeverityBadge";
import { CATEGORY_LABEL, SEVERITY_LABEL, CATEGORY_COLOR, severityReason } from "../lib/format";

export default function FindingCard({ finding }) {
  const { title, category, severity, evidence, page, regulation, fix } = finding;
  const reason = severityReason(finding);
  const catColor = CATEGORY_COLOR[category];

  return (
    <div className="finding" style={catColor ? { "--cat-color": catColor } : undefined}>
      <div className="finding__head">
        <SeverityBadge severity={severity} />
        <span className="finding__category">{CATEGORY_LABEL[category] ?? category}</span>
      </div>

      <h3 className="finding__title">{title}</h3>

      {severity !== "pass" && reason.text && (
        <p className="finding__reason">
          <span className="finding__reason-label">
            Why {SEVERITY_LABEL[severity] ?? severity}:
          </span>{" "}
          {reason.text}
        </p>
      )}

      {page && (
        <a className="finding__page" href={page} target="_blank" rel="noreferrer">
          {page}
        </a>
      )}

      {evidence && (
        <pre className="finding__evidence">
          <code>{evidence}</code>
        </pre>
      )}

      {fix && (
        <p className="finding__fix">
          <strong>Fix: </strong>
          {fix}
        </p>
      )}

      {regulation && <p className="finding__regulation">{regulation}</p>}
    </div>
  );
}
