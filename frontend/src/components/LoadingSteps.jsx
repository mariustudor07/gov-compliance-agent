import { useEffect, useState } from "react";
import {
  CrawlIcon,
  CookieIcon,
  AccessibilityIcon,
  ShieldIcon,
  EyeIcon,
  LawIcon,
  SparkleIcon,
  ReportIcon,
} from "./icons";

// Scans take 20-60s (README section 2). There's no live progress stream yet
// (that's Bogdan's Atlas Change Streams stretch goal), so we walk through the
// agent's real pipeline steps to show what's actually happening.
const STEPS = [
  { icon: CrawlIcon, label: "Crawling the site" },
  { icon: CookieIcon, label: "Checking cookies set before consent" },
  { icon: AccessibilityIcon, label: "Running accessibility checks (axe-core)" },
  { icon: ShieldIcon, label: "Checking security headers & TLS" },
  { icon: EyeIcon, label: "Reading the privacy policy" },
  { icon: LawIcon, label: "Matching findings to the law (vector search)" },
  { icon: SparkleIcon, label: "Asking Gemini to write the report" },
  { icon: ReportIcon, label: "Scoring every category" },
];

const STEP_MS = 3500;

export default function LoadingSteps() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => Math.min(i + 1, STEPS.length - 1));
    }, STEP_MS);
    return () => clearInterval(timer);
  }, []);

  const progress = (index / (STEPS.length - 1)) * 100;

  return (
    <div className="loading">
      <ol className="timeline" style={{ "--timeline-progress": `${progress}%` }}>
        {STEPS.map(({ icon: Icon, label }, i) => {
          const state = i < index ? "done" : i === index ? "active" : "pending";
          return (
            <li key={label} className={`timeline__step timeline__step--${state}`}>
              <span className="timeline__node">
                {state === "done" ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 13l4 4L19 7"
                      stroke="currentColor"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <Icon width="14" height="14" />
                )}
              </span>
              <span className="timeline__label">{label}</span>
            </li>
          );
        })}
      </ol>
      <p className="loading__hint">This usually takes 20–60 seconds.</p>
    </div>
  );
}
