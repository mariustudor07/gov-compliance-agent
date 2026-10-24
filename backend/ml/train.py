"""Step 2 of our own model: train a privacy-clause classifier on data/labels.csv.

Model: three kinds of features, fed into a linear SVM:
  - TF-IDF on words (1-3 word phrases)
  - TF-IDF on character patterns (catch spelling variants like "retain/retention/retained")
  - sentence embeddings from a small pretrained model (meaning, not just words; see features.py)
Calibration on top gives a confidence score per prediction, which classify.py uses.
Settings (C=0.5, embedding weight 2) were chosen by cross-validation.

Evaluation: 5-fold cross-validation. Every real sentence is tested exactly once by a model
that never saw it. That gives fairer numbers than one random split on a small dataset.

If data/synthetic.csv exists (from synthesize.py), it is added to the TRAINING folds only.
The test sentences are always real.

Run it, then copy the printed tables into docs/model_results.md.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline, make_union
from sklearn.svm import LinearSVC

from ml import keywords
from ml.features import SentenceEmbeddings

DATA = Path(__file__).resolve().parents[2] / "data"
MODEL = DATA / "clause_model.joblib"


def new_model():
    features = make_union(
        TfidfVectorizer(ngram_range=(1, 3), sublinear_tf=True),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
        SentenceEmbeddings(),
    )
    classifier = LinearSVC(C=0.5, class_weight="balanced")
    return make_pipeline(features, CalibratedClassifierCV(classifier, cv=3))


def cross_validate(real, synthetic=None):
    """Predict every real sentence with a model trained on the other 4/5 of the data."""
    predictions = pd.Series(index=real.index, dtype=object)
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for train_idx, test_idx in folds.split(real["sentence"], real["label"]):
        train = real.iloc[train_idx]
        if synthetic is not None:
            train = pd.concat([train, synthetic])
        model = new_model().fit(train["sentence"], train["label"])
        predictions.iloc[test_idx] = model.predict(real["sentence"].iloc[test_idx])
    return predictions


def main():
    real = pd.read_csv(DATA / "labels.csv").dropna(subset=["sentence", "label"]).reset_index(drop=True)
    print(f"{len(real)} real labelled sentences\n{real['label'].value_counts()}\n")

    print("=== Keyword baseline (hand-written rules, the score to beat) ===")
    print(classification_report(real["label"], [keywords.predict(s) for s in real["sentence"]], zero_division=0))

    print("=== Trained model, 5-fold cross-validation ===")
    print(classification_report(real["label"], cross_validate(real), zero_division=0))

    synthetic_path = DATA / "synthetic.csv"
    synthetic = pd.read_csv(synthetic_path) if synthetic_path.exists() else None
    if synthetic is not None:
        print(f"=== Trained model + {len(synthetic)} synthetic sentences (tested on real only) ===")
        print(classification_report(real["label"], cross_validate(real, synthetic), zero_division=0))

    final = pd.concat([real, synthetic]) if synthetic is not None else real
    joblib.dump(new_model().fit(final["sentence"], final["label"]), MODEL)
    print(f"Saved {MODEL}")


if __name__ == "__main__":
    main()
