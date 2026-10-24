// Small inline icon set, stroke-based, 24x24, currentColor. Keeps the bundle
// light with no icon library dependency.

const base = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function CrawlIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
      <path d="M11 7a4 4 0 0 0-4 4" strokeOpacity="0.5" />
    </svg>
  );
}

export function ChecksIcon(props) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M7 9h10" />
      <path d="M7 13l2 2 4-4" />
    </svg>
  );
}

export function LawIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v18" />
      <path d="M5 7l4-2 4 2" />
      <path d="M15 7l4-2 4 2" />
      <path d="M3 7h6M15 7h6" />
      <path d="M3 7l-1.5 5a2.5 2.5 0 0 0 5 0L5 7" />
      <path d="M19 7l-1.5 5a2.5 2.5 0 0 0 5 0L21 7" />
      <path d="M8 21h8" />
    </svg>
  );
}

export function ReportIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M14 3v5h5" />
      <path d="M6 3h8l5 5v13H6z" />
      <path d="M9 13h6M9 17h6M9 9h2" />
    </svg>
  );
}

export function ShieldIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z" />
      <path d="M9.5 12l1.8 1.8 3.2-3.6" />
    </svg>
  );
}

export function CookieIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3a9 9 0 1 0 9 9 4 4 0 0 1-4-4 4 4 0 0 1-4-4 4.5 4.5 0 0 1-1-1z" />
      <circle cx="9" cy="11" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="13" cy="15" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="10" cy="16" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function EyeIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function AccessibilityIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="4.5" r="1.8" />
      <path d="M5 8.5h14" />
      <path d="M12 8.5v5l-4 7" />
      <path d="M12 13.5l4 6.5" />
      <path d="M9 12.5h6" />
    </svg>
  );
}

export function SparkleIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6z" />
      <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z" />
    </svg>
  );
}
