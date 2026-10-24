import ScoreTile from "./ScoreTile";
import FindingCard from "./FindingCard";
import SeverityDonut from "./SeverityDonut";
import PriorityFixes from "./PriorityFixes";
import Reveal from "./Reveal";
import { ReportIcon, AccessibilityIcon, CookieIcon, EyeIcon, ShieldIcon, SparkleIcon } from "./icons";
import { CATEGORY_LABEL, formatDate, groupBySeverity, countBySeverity } from "../lib/format";

const CATEGORY_ICON = {
  accessibility: AccessibilityIcon,
  cookies: CookieIcon,
  privacy: EyeIcon,
  security: ShieldIcon,
};

export default function ReportView({ result, usingMock = false }) {
  const { url, scanned_at, scores = {}, findings = [], summary } = result;
  const grouped = groupBySeverity(findings);
  const counts = countBySeverity(findings);

  return (
    <div className="report">
      {usingMock && (
        <div className="banner">
          Showing example data: the backend isn't connected yet (set
          <code> VITE_API_BASE</code> or run the API).
        </div>
      )}

      <div className="report__head">
        <h1>{url}</h1>
        <p className="report__meta">Scanned {formatDate(scanned_at)}</p>
      </div>

      <div className="scores">
        <ScoreTile label="Overall" score={scores.overall} icon={ReportIcon} category="overall" big />
        {Object.entries(CATEGORY_LABEL).map(([key, label]) => (
          <ScoreTile
            key={key}
            label={label}
            score={scores[key]}
            icon={CATEGORY_ICON[key]}
            category={key}
          />
        ))}
      </div>
      <p className="scores__hint">Tap a score to see the law it's judged against.</p>

      {summary && (
        <Reveal className="summary">
          <span className="summary__icon">
            <SparkleIcon width={16} height={16} />
          </span>
          <p>{summary}</p>
        </Reveal>
      )}

      <Reveal className="findings-overview">
        <SeverityDonut counts={counts} />
      </Reveal>

      <PriorityFixes findings={findings} />

      {grouped.map((group, groupIndex) => (
        <section key={group.severity} className="finding-group">
          <h2>
            {group.severity} <span className="finding-group__count">({group.findings.length})</span>
          </h2>
          <ul className="finding-list">
            {group.findings.map((f, i) => (
              <Reveal
                as="li"
                id={`finding-${f.id}`}
                key={f.id}
                delay={Math.min(i, 5) * 60 + groupIndex * 20}
              >
                <FindingCard finding={f} />
              </Reveal>
            ))}
          </ul>
        </section>
      ))}

      {findings.length === 0 && <p>No findings.</p>}
    </div>
  );
}
