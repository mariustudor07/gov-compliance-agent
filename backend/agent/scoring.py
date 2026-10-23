"""Turns findings into 0-100 scores. Tune the penalties until the scores feel fair."""

CATEGORIES = ["accessibility", "cookies", "privacy", "security"]
PENALTY = {"critical": 40, "high": 20, "medium": 10, "low": 3, "pass": 0}


def score(findings):
    scores = {}
    for category in CATEGORIES:
        lost = sum(PENALTY[f["severity"]] for f in findings if f["category"] == category)
        scores[category] = max(0, 100 - lost)
    scores["overall"] = round(sum(scores[c] for c in CATEGORIES) / len(CATEGORIES))
    return scores
