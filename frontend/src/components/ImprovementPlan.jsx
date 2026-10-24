import Reveal from "./Reveal";
import SeverityBadge from "./SeverityBadge";
import { CATEGORY_LABEL, CATEGORY_COLOR } from "../lib/format";
import { planFor, planIntro } from "../lib/improve";

/** "How to improve your score": every fix in order, most serious first, with
 * the points each one adds. Same plan the PDF uses (lib/improve.js). */
export default function ImprovementPlan({ findings = [], scores = {} }) {
  const plan = planFor(findings, scores);

  return (
    <Reveal as="section" className="priority">
      <h2 className="priority__heading">How to improve your score</h2>
      <p className="priority__intro">{planIntro(plan)}</p>

      {plan.steps.length > 0 && (
        <ol className="priority-timeline">
          {plan.steps.map((step, i) => (
            <li key={step.key} className={`priority-timeline__item priority-timeline__item--${step.severity}`}>
              <span className="priority-timeline__node">{i + 1}</span>
              <div className="priority-timeline__card" style={{ "--cat-color": CATEGORY_COLOR[step.category] }}>
                <div className="priority-timeline__top">
                  <span className="priority-timeline__cat">
                    {CATEGORY_LABEL[step.category] ?? step.category}
                  </span>
                  {plan.showGains && step.overallGain > 0 ? (
                    <span className="gain-pill">
                      +{step.categoryGain} {CATEGORY_LABEL[step.category]} · +{step.overallGain} overall
                    </span>
                  ) : (
                    <SeverityBadge severity={step.severity} />
                  )}
                </div>
                <p className="priority-timeline__title">{step.action}</p>
                <p className="priority-timeline__fix">
                  Fixes:{" "}
                  {step.findings.map((f, j) => (
                    <span key={f.id}>
                      {j > 0 && "; "}
                      <a href={`#finding-${f.id}`}>{f.title}</a>
                    </span>
                  ))}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Reveal>
  );
}
