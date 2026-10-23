import Reveal from "./Reveal";
import { SEVERITY_ORDER, SEVERITY_LABEL, CATEGORY_LABEL, CATEGORY_COLOR } from "../lib/format";

// What counts as "fix this first" — pass/low don't need urgent action.
const URGENT = ["critical", "high", "medium"];

/** A visual timeline of the most urgent findings, most severe first — built
 * straight from the findings data (not scraped out of the AI's prose
 * summary), each step linking down to the full finding. */
export default function PriorityFixes({ findings = [], max = 4 }) {
  const ranked = SEVERITY_ORDER.filter((s) => URGENT.includes(s))
    .flatMap((severity) => findings.filter((f) => f.severity === severity))
    .slice(0, max);

  if (ranked.length === 0) return null;

  return (
    <Reveal as="section" className="priority">
      <h2 className="priority__heading">Fix these first</h2>
      <ol className="priority-timeline">
        {ranked.map((f, i) => (
          <li key={f.id} className={`priority-timeline__item priority-timeline__item--${f.severity}`}>
            <span className="priority-timeline__node">{i + 1}</span>
            <a
              href={`#finding-${f.id}`}
              className="priority-timeline__card"
              style={{ "--cat-color": CATEGORY_COLOR[f.category] }}
            >
              <div className="priority-timeline__top">
                <span className="priority-timeline__cat">{CATEGORY_LABEL[f.category] ?? f.category}</span>
                <span className={`badge badge--${f.severity}`}>{SEVERITY_LABEL[f.severity]}</span>
              </div>
              <p className="priority-timeline__title">{f.title}</p>
              {f.fix && <p className="priority-timeline__fix">{f.fix}</p>}
            </a>
          </li>
        ))}
      </ol>
    </Reveal>
  );
}
