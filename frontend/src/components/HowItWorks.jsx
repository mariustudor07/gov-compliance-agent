import { CrawlIcon, ChecksIcon, LawIcon, ReportIcon } from "./icons";
import Reveal from "./Reveal";

const STEPS = [
  {
    icon: CrawlIcon,
    title: "Crawl",
    body: "We open your site in a real browser and find the privacy, cookie and accessibility pages — no manual digging.",
    color: "#2563eb", // blue
  },
  {
    icon: ChecksIcon,
    title: "Inspect",
    body: "Automated checks for accessibility (axe-core), cookies set before consent, and security headers — plus our own ML model reads the privacy policy for missing clauses.",
    color: "#7c3aed", // violet
  },
  {
    icon: LawIcon,
    title: "Cite the law",
    body: "Every issue is matched against the real text of UK GDPR, PECR and WCAG 2.2 via vector search — never a guess.",
    color: "#b45309", // amber
  },
  {
    icon: ReportIcon,
    title: "Score & explain",
    body: "Gemini turns the evidence into a plain-English report and scores each category 0–100.",
    color: "#059669", // emerald
  },
];

export default function HowItWorks() {
  return (
    <section className="how">
      <Reveal as="h2" className="how__heading">
        How a scan actually works
      </Reveal>

      <ol className="how__steps">
        {STEPS.flatMap(({ icon: Icon, title, body, color }, i) => {
          const nodes = [
            <Reveal
              as="li"
              key={`step-${title}`}
              delay={i * 90}
              className="how__step"
              style={{ "--step-color": color }}
            >
              <div className="how__step-top">
                <span className="how__icon">
                  <Icon />
                </span>
                <span className="how__index">{String(i + 1).padStart(2, "0")}</span>
              </div>
              <h3>{title}</h3>
              <p>{body}</p>
            </Reveal>,
          ];
          if (i < STEPS.length - 1) {
            nodes.push(
              <li className="how__connector" key={`connector-${title}`} aria-hidden="true">
                <span className="how__connector-dot" />
              </li>
            );
          }
          return nodes;
        })}
      </ol>
    </section>
  );
}
