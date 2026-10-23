"""Keyword baseline: hand-written rules that guess a sentence's label.

Two jobs:
  1. A baseline our trained model has to beat (train.py prints both scores side by side).
  2. A fallback for classify.py, so privacy checks work before the model is trained.
"""
import re

# Checked in this order; the first label with a matching pattern wins.
# More specific labels come first (e.g. "complain to the ICO" before generic "contact us").
RULES = [
    ("complaints_ico", [r"\binformation commissioner", r"\bico\b", r"\bcomplain"]),
    ("contact_dpo", [r"data protection officer", r"\bdpo\b", r"contact us", r"@[\w.-]+\.\w+", r"write to"]),
    ("retention", [r"\bretain", r"\bretention\b", r"how long", r"\bkeep (your|the|this|personal)",
                   r"\b\d+ (years?|months?|days)\b", r"\bdelete(d)? (it|your|after)"]),
    ("rights", [r"\bright to\b", r"\byour rights\b", r"\berasure\b", r"\brectif", r"\bportability\b",
                r"\bobject to\b", r"\brestrict", r"subject access"]),
    ("lawful_basis", [r"lawful basis", r"legal basis", r"legitimate interest", r"public task",
                      r"legal obligation", r"vital interest", r"article 6", r"performance of a contract"]),
    ("third_parties", [r"\bshare\b", r"\bshared\b", r"third[- ]part", r"\bprocessors?\b", r"\btransfer",
                       r"\bdisclose", r"outside (the uk|the european)", r"\bsuppliers?\b"]),
    ("controller", [r"data controller", r"\bcontroller\b", r"\bregistered (office|in england)",
                    r"company number", r"\bwe are\b.*\bresponsible"]),
    ("purpose", [r"\bwe use (your|this|the|personal)", r"\bpurposes?\b", r"\bin order to\b",
                 r"\bto (provide|improve|deliver|process|manage) "]),
]
_COMPILED = [(label, [re.compile(p, re.IGNORECASE) for p in patterns]) for label, patterns in RULES]


def predict(sentence):
    for label, patterns in _COMPILED:
        if any(p.search(sentence) for p in patterns):
            return label
    return "other"
