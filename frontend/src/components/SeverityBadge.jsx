import { SEVERITY_LABEL } from "../lib/format";

export default function SeverityBadge({ severity }) {
  return (
    <span className={`badge badge--${severity}`}>
      {SEVERITY_LABEL[severity] ?? severity}
    </span>
  );
}
