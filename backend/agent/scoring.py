"""Turns findings into 0-100 scores (method: docs/ranking.md).

Each category starts at 100 and loses points per finding. Overall is the average of the four categories,
but capped by the worst finding: a site breaking the law for every visitor shouldn't score 84 because its
other categories are fine (like SSL Labs capping a grade when there's a serious flaw).
"""

CATEGORIES = ["accessibility", "cookies", "privacy", "security"]
PENALTY = {"critical": 40, "high": 20, "medium": 10, "low": 3, "pass": 0}
OVERALL_CAP = {"critical": 60, "high": 80}  # the highest overall score possible with such a finding


def score(findings):
    scores = {}
    for category in CATEGORIES:
        lost = sum(PENALTY[f["severity"]] for f in findings if f["category"] == category)
        scores[category] = max(0, 100 - lost)
    overall = round(sum(scores[c] for c in CATEGORIES) / len(CATEGORIES))
    caps = [OVERALL_CAP[f["severity"]] for f in findings if f["severity"] in OVERALL_CAP]
    scores["overall"] = min([overall] + caps)
    return scores
