import { CATEGORY_LABEL, SEVERITY_ORDER } from "./format";

// Mirrors backend/agent/scoring.py: each category starts at 100 and loses
// these points per finding; overall is the rounded average. If the backend
// formula changes, keep this in step (planFor() checks they still agree).
export const PENALTY = { critical: 40, high: 20, medium: 10, low: 3, pass: 0 };

const CATEGORIES = Object.keys(CATEGORY_LABEL);

function scoresFor(findings) {
  const scores = {};
  for (const category of CATEGORIES) {
    const lost = findings
      .filter((f) => f.category === category)
      .reduce((sum, f) => sum + (PENALTY[f.severity] ?? 0), 0);
    scores[category] = Math.max(0, 100 - lost);
  }
  scores.overall = Math.round(CATEGORIES.reduce((sum, c) => sum + scores[c], 0) / CATEGORIES.length);
  return scores;
}

const severityRank = (severity) => SEVERITY_ORDER.indexOf(severity);

/** Turns findings into an ordered list of improvement steps. Findings that
 * share the same fix are merged into one step. Each step records how many
 * points it would add once the steps before it are done.
 *
 * `showGains` is false if our copy of the scoring formula doesn't reproduce
 * the scores the backend sent, so we never show numbers that don't add up. */
export function planFor(findings = [], reportedScores = {}) {
  const actionable = findings.filter((f) => f.severity !== "pass");

  const byAction = new Map();
  for (const f of actionable) {
    const action = (f.fix || f.title || "").trim();
    const key = `${f.category}|${action}`;
    if (!byAction.has(key)) {
      byAction.set(key, { key, action, category: f.category, severity: f.severity, findings: [] });
    }
    const step = byAction.get(key);
    step.findings.push(f);
    if (severityRank(f.severity) < severityRank(step.severity)) step.severity = f.severity;
  }

  const penaltyOf = (step) => step.findings.reduce((sum, f) => sum + PENALTY[f.severity], 0);
  const steps = [...byAction.values()].sort(
    (a, b) => severityRank(a.severity) - severityRank(b.severity) || penaltyOf(b) - penaltyOf(a)
  );

  let before = scoresFor(findings);
  const start = before.overall;
  const showGains = ["overall", ...CATEGORIES].every(
    (key) => typeof reportedScores[key] !== "number" || Math.round(reportedScores[key]) === before[key]
  );

  let remaining = actionable;
  for (const step of steps) {
    remaining = remaining.filter((f) => !step.findings.includes(f));
    const after = scoresFor(remaining);
    step.categoryGain = after[step.category] - before[step.category];
    step.overallGain = after.overall - before.overall;
    step.scoreAfter = after.overall;
    before = after;
  }

  return { start, steps, showGains };
}

/** One-line intro shared by the web page and the PDF. */
export function planIntro({ start, steps, showGains }) {
  if (steps.length === 0) return "Nothing to fix: this site passed every check we run.";
  if (!showGains) return "Work through these in order, most serious first.";
  let text = `Work through these in order. Fixing all of them would take your overall score from ${start} to 100.`;
  if (steps.length > 3) text += ` The first three alone get you to ${steps[2].scoreAfter}.`;
  return text;
}
