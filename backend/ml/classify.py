"""Step 3 of our own model: use it. The agent calls missing_clauses()."""
import re
from pathlib import Path

import joblib

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


def classify_sentences(text):
    """Returns [{"sentence", "label", "confidence"}] or None if the model isn't trained yet."""
    model = _load()
    if model is None:
        return None
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) >= 30]
    if not sents:
        return []
    probs = model.predict_proba(sents)
    results = []
    for sentence, row in zip(sents, probs):
        best = row.argmax()
        results.append({"sentence": sentence, "label": model.classes_[best], "confidence": float(row[best])})
    return results


def missing_clauses(text):
    """Which required clauses the privacy policy doesn't seem to contain.
    Returns a list of labels, or None if the model isn't trained yet."""
    results = classify_sentences(text)
    if results is None:
        return None
    found = {r["label"] for r in results if r["confidence"] >= MIN_CONFIDENCE}
    return [c for c in REQUIRED if c not in found]
