import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { AccessibilityIcon, CookieIcon, EyeIcon, ShieldIcon } from "../components/icons";

const SECTIONS = [
  {
    id: "wcag",
    icon: AccessibilityIcon,
    color: "#7c3aed",
    badge: "WCAG 2.2 AA",
    title: "Accessibility",
    law: "Public Sector Bodies (Websites and Mobile Applications) Accessibility Regulations 2018",
    requires:
      "Public sector websites must meet WCAG 2.2 at level AA: colour contrast, keyboard navigation, screen-reader labels, and an accessibility statement are all covered.",
    howWeCheck:
      "We run axe-core (the same engine behind most professional accessibility audits) against every page we crawl, and check for a published accessibility statement.",
    source: "https://www.w3.org/TR/WCAG22/",
    sourceLabel: "Read WCAG 2.2 at w3.org",
  },
  {
    id: "pecr",
    icon: CookieIcon,
    color: "#b45309",
    badge: "PECR",
    title: "Cookies",
    law: "Privacy and Electronic Communications Regulations 2003 (PECR)",
    requires:
      "Non-essential cookies (analytics, advertising, tracking) can't be set until the visitor has given consent, and rejecting must be as easy as accepting: a 'Reject' option can't be hidden behind extra clicks.",
    howWeCheck:
      "We record every cookie set before anything is clicked. When Gemini is available, it also looks at a screenshot of the banner to judge whether 'reject' is genuinely as prominent as 'accept', the way the ICO expects a human reviewer to.",
    source: "https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/",
    sourceLabel: "Read the ICO's guide to PECR",
  },
  {
    id: "gdpr",
    icon: EyeIcon,
    color: "#2563eb",
    badge: "UK GDPR",
    title: "Privacy",
    law: "UK GDPR, Articles 13–14, and the Data Protection Act 2018",
    requires:
      "A privacy notice must say who's responsible for the data, why it's collected, the lawful basis, how long it's kept, who it's shared with, and how to exercise your rights (access, deletion, complaint to the ICO).",
    howWeCheck:
      "Our own trained classifier reads the privacy policy and flags which of those required points it can't find a sentence covering. Not a keyword search: a model trained on hand-labelled UK privacy notices.",
    source: "https://www.legislation.gov.uk/eur/2016/679/contents",
    sourceLabel: "Read UK GDPR at legislation.gov.uk",
  },
  {
    id: "ncsc",
    icon: ShieldIcon,
    color: "#059669",
    badge: "NCSC guidance",
    title: "Security",
    law: "NCSC guidance, underpinned by UK GDPR Art. 32 (security of processing)",
    requires:
      "Baseline protections: HTTPS everywhere, HSTS, a Content-Security-Policy, clickjacking protection, and no mixed content. Art. 32 makes 'appropriate technical measures' a legal duty, not just good practice.",
    howWeCheck:
      "We inspect the live response headers and certificate on every page we visit: no guessing, no cached results.",
    source: "https://www.ncsc.gov.uk/section/advice-guidance/all-advice-guidance",
    sourceLabel: "Browse NCSC guidance",
  },
];

const FAQ = [
  {
    q: "Is a GovCheck report legal advice?",
    a: "No. It's an automated first pass against the rules we check, useful for catching obvious gaps fast, not a substitute for a qualified solicitor or your Data Protection Officer. Always get a professional opinion before relying on a score for a real compliance decision.",
  },
  {
    q: "Why might the same site score differently on a rescan?",
    a: "Cookie banners, privacy pages and headers can change between visits, and our AI-written explanations can vary in wording (not substance) between runs. The underlying checks (axe-core, header inspection, our trained classifier) are deterministic; only the parts Gemini writes can phrase things differently.",
  },
  {
    q: "Do you store the sites you scan, or data from them?",
    a: "Scan results (scores and findings) are stored in MongoDB Atlas so you can look up past scans. We don't store personal data belonging to the site's own visitors: we're checking the site's compliance posture, not harvesting its users' data.",
  },
  {
    q: "How accurate is the privacy-notice classifier?",
    a: "It's our own model, trained on hand-labelled sentences from real UK privacy notices (see the numbers in the project's docs/model_results.md). It will occasionally miss a clause phrased unusually; treat a 'missing' flag as 'worth double-checking', not an infallible verdict.",
  },
  {
    q: "What if I think a finding is wrong?",
    a: "Every finding includes its evidence (the actual header, HTML snippet, or classifier output) so you can verify it yourself rather than taking our word for it. That's deliberate: a compliance tool should show its working.",
  },
  {
    q: "What's actually running under the hood?",
    a: "A Playwright-driven crawler, axe-core for accessibility, our own trained privacy-notice classifier, Google Gemini for explanations and the cookie-banner vision check, and MongoDB Atlas (including Vector Search) to ground every citation in the real text of the law.",
  },
];

export default function Docs() {
  const { hash } = useLocation();

  useEffect(() => {
    if (!hash) return;
    const el = document.getElementById(hash.slice(1));
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [hash]);

  return (
    <div className="docs">
      <div className="docs__head">
        <h1>How GovCheck checks compliance</h1>
        <p className="docs__intro">
          Every score on this site traces back to a specific law and a specific, repeatable check,
          not a vibe. Here's exactly what we look for, and where to read the source material yourself.
        </p>
      </div>

      {SECTIONS.map((s) => {
        const Icon = s.icon;
        return (
          <section key={s.id} id={s.id} className="docs__section" style={{ "--cat-color": s.color }}>
            <div className="docs__section-head">
              <span className="docs__section-icon">
                <Icon width={20} height={20} />
              </span>
              <div>
                <span className="docs__badge">{s.badge}</span>
                <h2>{s.title}</h2>
              </div>
            </div>
            <p className="docs__law">{s.law}</p>
            <div className="docs__grid">
              <div>
                <h3>What it requires</h3>
                <p>{s.requires}</p>
              </div>
              <div>
                <h3>How we check it</h3>
                <p>{s.howWeCheck}</p>
              </div>
            </div>
            <a className="docs__source" href={s.source} target="_blank" rel="noreferrer">
              {s.sourceLabel} ↗
            </a>
          </section>
        );
      })}

      <section id="faq" className="docs__section docs__faq">
        <h2>FAQ</h2>
        <div className="faq-list">
          {FAQ.map((item) => (
            <details key={item.q} className="faq-item">
              <summary>{item.q}</summary>
              <p>{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <div className="docs__disclaimer">
        <strong>Not legal advice.</strong> GovCheck is an automated compliance-checking tool built for a
        hackathon demo. Use it to find obvious gaps quickly, then verify anything that matters with a
        qualified professional.
      </div>
    </div>
  );
}
