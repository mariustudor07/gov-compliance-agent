export const SEVERITY_ORDER = ["critical", "high", "medium", "low", "pass"];

export const SEVERITY_LABEL = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  pass: "Pass",
};

export const CATEGORY_LABEL = {
  accessibility: "Accessibility",
  cookies: "Cookies",
  privacy: "Privacy",
  security: "Security",
};

// Each category gets its own hue so the report reads as a spread of colour,
// not a single accent repeated everywhere.
export const CATEGORY_COLOR = {
  accessibility: "#7c3aed", // violet
  cookies: "#b45309", // amber
  privacy: "#2563eb", // blue
  security: "#059669", // emerald
  overall: "#4f46e5", // indigo — the brand colour
};

// Generic "what does this severity mean" text, used whenever a finding
// doesn't come with its own `severity_reason` from the backend yet.
export const SEVERITY_REASON_FALLBACK = {
  critical: "Blocks people from using the site, exposes personal data, or breaks the law outright — fix this first.",
  high: "A real compliance gap a regulator or auditor would flag. Should be fixed before launch.",
  medium: "Worth fixing — it falls short of the rule, but doesn't block access or breach the law outright.",
  low: "A minor improvement. Good practice, not a legal requirement.",
  pass: "This check came back clean — no action needed.",
};

/** The reason a finding got its severity: the finding's own text if the
 * backend provided one, otherwise a generic definition of that level. */
export function severityReason(finding) {
  return {
    text: finding.severity_reason || SEVERITY_REASON_FALLBACK[finding.severity] || "",
    isSpecific: Boolean(finding.severity_reason),
  };
}

/** 0-100 score -> "good" | "ok" | "bad", used to color score tiles. */
export function scoreTier(score) {
  if (score == null) return "unknown";
  if (score >= 80) return "good";
  if (score >= 50) return "ok";
  return "bad";
}

// The actual law each category is scored against, and what a score at each
// tier means in terms of that law — not just "good/bad" but which obligation
// is or isn't being met.
const CATEGORY_LEGAL = {
  accessibility: {
    law: "Public Sector Bodies Accessibility Regulations 2018 → WCAG 2.2 AA",
    good: "Disabled users can use the site without hitting barriers — this meets the legal bar the Regulations set.",
    ok: "Real barriers remain for disabled users. Each unresolved WCAG violation is a specific legal non-compliance, not a style nitpick.",
    bad: "Disabled users are likely blocked from core parts of the site — a direct breach of the 2018 Regulations, which apply to public sector sites by law.",
  },
  cookies: {
    law: "PECR (Privacy and Electronic Communications Regulations), Reg. 6",
    good: "No tracking cookies are set before the user consents — exactly what PECR requires.",
    ok: "The consent banner likely has no genuine 'reject' option, which the ICO treats as invalid consent under PECR.",
    bad: "Cookies are being set before anyone agrees to them. Under PECR Reg. 6 that's unlawful tracking, with no ambiguity.",
  },
  privacy: {
    law: "UK GDPR Art. 13–14 & Data Protection Act 2018",
    good: "The privacy notice covers what Art. 13 requires: who's responsible, why data is collected, and people's rights.",
    ok: "The privacy notice is missing some information Art. 13 makes mandatory, not optional extras.",
    bad: "The privacy notice is missing most of what Art. 13 legally requires (controller, lawful basis, retention, rights) — people can't exercise rights they were never told they have.",
  },
  security: {
    law: "UK GDPR Art. 32 (security of processing) & NCSC guidance",
    good: "Baseline technical protections (HTTPS, security headers) are in place — what Art. 32 expects as a minimum.",
    ok: "Some baseline protections are missing. Art. 32 requires 'appropriate technical measures' — gaps here can themselves count as a GDPR breach.",
    bad: "Multiple basic protections are missing. Under Art. 32, failing to secure personal data is itself a breach, even before any data is actually stolen.",
  },
  overall: {
    law: "Blended across UK GDPR, PECR, WCAG 2.2 AA and NCSC guidance",
    good: "This site is meeting its obligations across accessibility, cookies, privacy and security.",
    ok: "There are real gaps in at least one legal area above — worth fixing before this is genuinely compliant.",
    bad: "This site carries meaningful legal risk across multiple UK laws, not just one area.",
  },
};

/** Which law a category score is judged against, and what the current score
 * means under that law. Falls back to "overall"-style wording if the
 * category is unknown. */
export function legalBasis(category, score) {
  const entry = CATEGORY_LEGAL[category] || CATEGORY_LEGAL.overall;
  const tier = scoreTier(score);
  return { law: entry.law, blurb: entry[tier] || entry.ok };
}

export function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

/** Group findings by severity, in SEVERITY_ORDER, dropping empty groups. */
export function groupBySeverity(findings = []) {
  const groups = SEVERITY_ORDER.map((severity) => ({
    severity,
    findings: findings.filter((f) => f.severity === severity),
  }));
  return groups.filter((g) => g.findings.length > 0);
}

export function countBySeverity(findings = []) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0, pass: 0 };
  for (const f of findings) {
    if (counts[f.severity] != null) counts[f.severity] += 1;
  }
  return counts;
}
