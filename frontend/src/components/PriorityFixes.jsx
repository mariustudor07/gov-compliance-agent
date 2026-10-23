import Reveal from "./Reveal";
import { SEVERITY_ORDER, SEVERITY_LABEL, CATEGORY_LABEL, CATEGORY_COLOR } from "../lib/format";

// What counts as "fix this first" — pass/low don't need urgent action.
const URGENT = ["critical", "high", "medium"];

/** A ranked, visual "fix these first" list built straight from the findings
 * data (not scraped out of the AI's prose summary) — so it's always accurate
 * and always has something real to link to. */
export default function PriorityFixes({ findings = [], max = 3 }) {
  const ranked = SEVERITY_ORDER.filter((s) => URGENT.includes(s))
    .flatMap((severity) => findings.filter((f) => f.severity === severity))
    .slice(0, max);

  if (ranked.length === 0) return null;

  return (
    <Reveal as="section" className="priority">
      <h2 className="priority__heading">Fix these first</h2>
      <ol className="priority__list">
        {ranked.map((f, i) => (
          <li key={f.id} className="priority__item">
            <a
              href={`#finding-${f.id}`}
              className="priority__link"
              style={{ "--cat-color": CATEGORY_COLOR[f.category] }}
            >
              <span className="priority__rank">{i + 1}</span>
              <div className="priority__body">
                <span className="priority__cat">{CATEGORY_LABEL[f.category] ?? f.category}</span>
                <p className="priority__title">{f.title}</p>
              </div>
              <span className={`badge badge--${f.severity}`}>{SEVERITY_LABEL[f.severity]}</span>
            </a>
          </li>
        ))}
      </ol>
    </Reveal>
  );
}
