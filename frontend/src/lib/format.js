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
  security: "#047857", // emerald
  overall: "#4f46e5", // indigo, the brand colour
};

// Generic "what does this severity mean" text, used whenever a finding
// doesn't come with its own `severity_reason` from the backend yet. Framed
// as a legal question (which law, how directly it's breached), not an
// ethical or UX judgement.
export const SEVERITY_REASON_FALLBACK = {
  critical: "A direct, unambiguous breach of UK GDPR, PECR or the 2018 Accessibility Regulations, not a style or UX issue.",
  high: "A specific breach a regulator (the ICO) or an accessibility audit would cite by name. Required to fix, not optional.",
  medium: "Falls short of a legal requirement, though short of an outright breach; still non-compliant, just lower-risk.",
  low: "Recommended practice under the relevant guidance, but not something the law currently mandates.",
  pass: "Meets the legal requirement this check is based on.",
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
// tier means in terms of that law, not just "good/bad" but which obligation
// is or isn't being met.
const CATEGORY_LEGAL = {
  accessibility: {
    law: "Public Sector Bodies Accessibility Regulations 2018 → WCAG 2.2 AA",
    good: "Meets the legal standard the 2018 Regulations set: WCAG 2.2 AA.",
    ok: "Each unresolved WCAG 2.2 AA violation is a specific breach of the 2018 Regulations: a legal issue, not a style preference.",
    bad: "Multiple WCAG 2.2 AA failures: a direct breach of the Public Sector Bodies Accessibility Regulations 2018, a legal duty for public sector sites, not a recommendation.",
  },
  cookies: {
    law: "PECR (Privacy and Electronic Communications Regulations), Reg. 6",
    good: "Complies with PECR Reg. 6: no non-essential cookie is set before consent.",
    ok: "No genuine 'reject' option on the banner means the consent collected here is invalid under the ICO's interpretation of PECR.",
    bad: "Cookies are set before consent is given, an unlawful act under PECR Reg. 6, regardless of what the cookies are used for.",
  },
  privacy: {
    law: "UK GDPR Art. 13–14 & Data Protection Act 2018",
    good: "Satisfies the mandatory disclosure requirements of UK GDPR Art. 13.",
    ok: "Missing information that Art. 13 makes a legal requirement to disclose, not optional detail.",
    bad: "Missing most of what Art. 13 legally mandates (controller, lawful basis, retention, rights): a breach of a statutory disclosure duty.",
  },
  security: {
    law: "UK GDPR Art. 32 (security of processing) & NCSC guidance",
    good: "Meets the baseline technical measures UK GDPR Art. 32 requires.",
    ok: "A gap against the 'appropriate technical measures' UK GDPR Art. 32 requires: a compliance issue in itself, separate from whether data has actually been compromised.",
    bad: "Multiple baseline protections absent. Under Art. 32, this is itself a breach of the duty to secure personal data, regardless of whether an incident has occurred.",
  },
  overall: {
    law: "Blended across UK GDPR, PECR, WCAG 2.2 AA and NCSC guidance",
    good: "No outstanding legal non-compliance across the four laws this tool checks.",
    ok: "At least one category above has an active legal non-compliance that needs resolving.",
    bad: "Legal non-compliance across multiple UK laws at once, not an isolated issue.",
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
