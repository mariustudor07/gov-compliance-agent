import { useEffect, useId, useState } from "react";
import useCountUp from "../hooks/useCountUp";
import { scoreTier } from "../lib/format";

const GRADIENTS = {
  good: ["#22c55e", "#16a34a"],
  ok: ["#f59e0b", "#d97706"],
  bad: ["#ef4444", "#dc2626"],
  unknown: ["#cbd5e1", "#94a3b8"],
};

export default function ScoreRing({ score, size = 86, strokeWidth = 7 }) {
  const uid = useId();
  const tier = scoreTier(score);
  const value = useCountUp(typeof score === "number" ? score : 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = typeof score === "number" ? Math.min(Math.max(score, 0), 100) : 0;
  const [from, to] = GRADIENTS[tier];

  // Start fully undrawn, then animate the stroke in on the next frame so
  // the CSS transition on stroke-dashoffset actually has something to tween.
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(id);
  }, []);
  const offset = ready ? circumference - (pct / 100) * circumference : circumference;

  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <linearGradient id={`ring-grad-${uid}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={from} />
            <stop offset="100%" stopColor={to} />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--ring-track)"
          strokeWidth={strokeWidth}
        />
        {typeof score === "number" && (
          <circle
            className="ring__progress"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={`url(#ring-grad-${uid})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )}
      </svg>
      <span className="ring__value">{typeof score === "number" ? value : "N/A"}</span>
    </div>
  );
}
