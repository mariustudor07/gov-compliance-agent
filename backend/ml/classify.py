"""Step 3 of our own model: use it. The agent calls missing_clauses()."""
import re
from pathlib import Path

import joblib

from . import keywords

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "clause_model.joblib"

# What UK GDPR Articles 13/14 require a privacy notice to contain.
REQUIRED = ["controller", "purpose", "lawful_basis", "rights", "retention",
            "contact_dpo", "third_parties", "complaints_ico"]

MIN_CONFIDENCE = 0.4
_model = None


def _load():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model


def model_name():
    return "trained classifier" if _load() is not None else "keyword baseline"


def classify_sentences(text):
    """Returns [{"sentence", "label", "confidence"}].
    Uses our trained model if data/clause_model.joblib exists, otherwise the keyword baseline."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) >= 30]
    if not sents:
        return []

    model = _load()
    if model is None:
        return [{"sentence": s, "label": keywords.predict(s), "confidence": 1.0} for s in sents]

    probs = model.predict_proba(sents)
    results = []
    for sentence, row in zip(sents, probs):
        best = row.argmax()
        results.append({"sentence": sentence, "label": model.classes_[best], "confidence": float(row[best])})
    return results


def clause_probability(sentence, clause):
    """How likely our model thinks this one sentence is about `clause` (0-1).
    Used to double-check quotes Gemini brings back from sites that block our scanner."""
    model = _load()
    if model is None:
        return 1.0 if keywords.predict(sentence) == clause else 0.0
    probs = model.predict_proba([sentence])[0]
    classes = list(model.classes_)
    return float(probs[classes.index(clause)]) if clause in classes else 0.0


def missing_clauses(text):
    """Which required clauses the privacy policy doesn't seem to contain."""
    found = {r["label"] for r in classify_sentences(text) if r["confidence"] >= MIN_CONFIDENCE}
    return [c for c in REQUIRED if c not in found]
