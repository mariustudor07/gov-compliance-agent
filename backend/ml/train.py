"""Step 2 of our own model: train a privacy-clause classifier on data/labels.csv.

TF-IDF turns each sentence into word-frequency numbers; LogisticRegression learns which
words point to which clause type. Simple, fast, and we can explain every part of it to judges.

Run it, then copy the printed table into docs/model_results.md.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "labels.csv"
MODEL = ROOT / "data" / "clause_model.joblib"


def main():
    df = pd.read_csv(DATA).dropna(subset=["sentence", "label"])
    print(f"{len(df)} labelled sentences\n{df['label'].value_counts()}\n")

    X_train, X_test, y_train, y_test = train_test_split(
        df["sentence"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])

    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )
    model.fit(X_train, y_train)

    print(classification_report(y_test, model.predict(X_test)))

    model.fit(df["sentence"], df["label"])  # final model uses all the data
    joblib.dump(model, MODEL)
    print(f"Saved {MODEL}")


if __name__ == "__main__":
    main()
