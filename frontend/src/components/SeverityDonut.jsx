import { SEVERITY_LABEL } from "../lib/format";

const COLORS = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#0891b2",
  pass: "#16a34a",
};

const ORDER = ["critical", "high", "medium", "low", "pass"];

export default function SeverityDonut({ counts, size = 150, strokeWidth = 16 }) {
  const total = ORDER.reduce((sum, key) => sum + (counts[key] || 0), 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  if (total === 0) return null;

  let cumulative = 0;
  const arcs = ORDER.filter((key) => counts[key] > 0).map((key) => {
    const count = counts[key];
    const length = (count / total) * circumference;
    const arc = { key, count, length, offset: -cumulative };
    cumulative += length;
    return arc;
  });

  return (
    <div className="donut">
      <div className="donut__chart" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--ring-track)"
            strokeWidth={strokeWidth}
          />
          {arcs.map(({ key, length, offset }) => (
            <circle
              key={key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={COLORS[key]}
              strokeWidth={strokeWidth}
              strokeDasharray={`${Math.max(length - 2, 0)} ${circumference}`}
              strokeDashoffset={offset}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
          ))}
        </svg>
        <div className="donut__center">
          <span className="donut__total">{total}</span>
          <span className="donut__total-label">checks</span>
        </div>
      </div>

      <ul className="donut__legend">
        {ORDER.filter((key) => counts[key] > 0).map((key) => (
          <li key={key}>
            <span className="donut__dot" style={{ background: COLORS[key] }} />
            {counts[key]} {SEVERITY_LABEL[key]}
          </li>
        ))}
      </ul>
    </div>
  );
}
