"""Step 2 of our own model: train a privacy-clause classifier on data/labels.csv.

TF-IDF turns each sentence into word-frequency numbers; LogisticRegression learns which
words point to which clause type. Simple, fast, and we can explain every part of it to judges.

If data/synthetic.csv exists (from synthesize.py), it is added to the TRAINING data only.
The test set is always real, human-checked sentences.

Run it, then copy the printed tables into docs/model_results.md.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

DATA = Path(__file__).resolve().parents[2] / "data"
MODEL = DATA / "clause_model.joblib"


def new_model():
    return make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )


def main():
    real = pd.read_csv(DATA / "labels.csv").dropna(subset=["sentence", "label"])
    print(f"{len(real)} real labelled sentences\n{real['label'].value_counts()}\n")

    X_train, X_test, y_train, y_test = train_test_split(
        real["sentence"], real["label"], test_size=0.2, random_state=42, stratify=real["label"])

    model = new_model().fit(X_train, y_train)
    print("=== Real data only ===")
    print(classification_report(y_test, model.predict(X_test)))

    synthetic_path = DATA / "synthetic.csv"
    synthetic = pd.read_csv(synthetic_path) if synthetic_path.exists() else None
    if synthetic is not None:
        model = new_model().fit(pd.concat([X_train, synthetic["sentence"]]),
                                pd.concat([y_train, synthetic["label"]]))
        print(f"=== Real + {len(synthetic)} synthetic (same real test set) ===")
        print(classification_report(y_test, model.predict(X_test)))

    # Final model: all real data (+ synthetic if present).
    X_all, y_all = real["sentence"], real["label"]
    if synthetic is not None:
        X_all, y_all = pd.concat([X_all, synthetic["sentence"]]), pd.concat([y_all, synthetic["label"]])
    joblib.dump(new_model().fit(X_all, y_all), MODEL)
    print(f"Saved {MODEL}")


if __name__ == "__main__":
    main()
