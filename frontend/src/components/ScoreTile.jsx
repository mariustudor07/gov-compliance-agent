import { scoreTier, legalBasis, CATEGORY_COLOR } from "../lib/format";
import ScoreRing from "./ScoreRing";

export default function ScoreTile({ label, score, icon: Icon, category, big = false }) {
  const legal = category ? legalBasis(category, score) : null;
  const color = category ? CATEGORY_COLOR[category] : null;

  const body = (
    <>
      <ScoreRing score={score} size={big ? 108 : 82} strokeWidth={big ? 8 : 6} />
      <div className="score-tile__label">
        {Icon && <Icon width={14} height={14} />}
        {label}
      </div>
    </>
  );

  const className = `score-tile score-tile--${scoreTier(score)} ${big ? "score-tile--big" : ""}`;
  const style = color ? { "--cat-color": color } : undefined;

  if (!legal) {
    return (
      <div className={className} style={style}>
        {body}
      </div>
    );
  }

  return (
    <details className={`${className} score-tile--expandable`} style={style}>
      <summary>
        {body}
        <span className="score-tile__why">Why?</span>
      </summary>
      <div className="score-tile__legal">
        <p className="score-tile__law">{legal.law}</p>
        <p>{legal.blurb}</p>
      </div>
    </details>
  );
}
