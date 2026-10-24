"""Document-level evaluation: does GovCheck get the right answer for WHOLE privacy policies?

The app doesn't need every sentence right. It needs to know whether a policy covers each required
clause at least once. This measures exactly that, fairly:

  For each of the 20 policies in labels.csv:
    1. train the model on the OTHER 19 policies only (it never sees this one)
    2. run it on this policy's full text
    3. for each required clause, record "present" (with the sentence that convinced it) or "missing"

Step 1 (python -m ml.evaluate_documents) writes data/doc_eval.csv.
Step 2: fill in the `truth` column (present / missing) by checking each policy. The `evidence`
        column shows the sentence the model relied on, which makes checking "present" quick.
Step 3 (python -m ml.evaluate_documents score) prints the scores.

Held-out test (fairer still): python -m ml.evaluate_documents new
  Runs the saved model on policies listed in data/test_policies.txt, none of which were used for
  training, fetched in a real browser exactly like the app does. Writes data/doc_eval_new.csv;
  fill in `truth`, then: python -m ml.evaluate_documents score new
"""
import csv
import sys
from pathlib import Path

import pandas as pd

from ml.classify import MIN_CONFIDENCE, REQUIRED
from ml.label import fetch_sentences
from ml.train import new_model

DATA = Path(__file__).resolve().parents[2] / "data"
OUT = DATA / "doc_eval.csv"
NEW_OUT = DATA / "doc_eval_new.csv"
FIELDS = ["policy", "clause", "model", "confidence", "evidence", "truth"]


def run():
    labels = pd.read_csv(DATA / "labels.csv").dropna(subset=["sentence", "label"])
    old_truth = {}
    if OUT.exists():  # keep any truth already filled in
        old_truth = {(r["policy"], r["clause"]): r["truth"] for r in csv.DictReader(OUT.open(encoding="utf-8"))}

    rows = []
    for policy in labels["source"].unique():
        train = labels[labels["source"] != policy]
        model = new_model().fit(train["sentence"], train["label"])
        sentences = fetch_sentences(policy)
        probs = model.predict_proba(sentences)
        classes = list(model.classes_)
        for clause in REQUIRED:
            col = probs[:, classes.index(clause)]
            best = col.argmax()
            # Same rule as the app: present if some sentence's TOP label is this clause with enough confidence.
            hits = [i for i, row in enumerate(probs) if classes[row.argmax()] == clause and row.max() >= MIN_CONFIDENCE]
            if hits:
                best = max(hits, key=lambda i: col[i])
            rows.append({"policy": policy, "clause": clause, "model": "present" if hits else "missing",
                         "confidence": f"{col[best]:.2f}", "evidence": sentences[best][:300],
                         "truth": old_truth.get((policy, clause), "")})
        print(f"{sum(r['model'] == 'missing' for r in rows[-len(REQUIRED):])} missing  {policy}")

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {OUT}. Fill in the truth column, then run: python -m ml.evaluate_documents score")


def run_new():
    """Saved model on unseen policies, fetched in a browser like the real scanner."""
    from playwright.sync_api import sync_playwright

    from agent.agent import MIN_POLICY_WORDS
    from ml.classify import classify_sentences
    from scanner.crawler import USER_AGENT, _goto

    urls = [u.strip() for u in (DATA / "test_policies.txt").read_text().splitlines()
            if u.strip() and not u.startswith("#")]
    old_truth = {}
    if NEW_OUT.exists():
        old_truth = {(r["policy"], r["clause"]): r["truth"] for r in csv.DictReader(NEW_OUT.open(encoding="utf-8"))
                     if r["truth"] != "n/a"}  # n/a = was unreadable last time; judge afresh if readable now

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            # fresh tab per policy (a failed page can't disturb the next), same browser identity as the scanner
            page = browser.new_context(user_agent=USER_AGENT, locale="en-GB").new_page()
            try:
                response = _goto(page, url)
                if response and response.status >= 400:
                    print(f"skip {url}: HTTP {response.status}")
                    continue
                text = page.inner_text("body")
            except Exception as e:
                print(f"skip {url}: {str(e).splitlines()[0]}")
                continue
            finally:
                page.context.close()
            results = classify_sentences(text)
            words = len(text.split())
            for clause in REQUIRED:
                hits = [r for r in results if r["label"] == clause and r["confidence"] >= MIN_CONFIDENCE]
                best = max(hits, key=lambda r: r["confidence"]) if hits else None
                # Same rule as the app: too little text to judge -> "couldn't read", not "missing".
                verdict = "unreadable" if words < MIN_POLICY_WORDS else "present" if hits else "missing"
                rows.append({"policy": url, "clause": clause, "model": verdict,
                             "confidence": f"{best['confidence']:.2f}" if best else "",
                             "evidence": best["sentence"][:300] if best else "",
                             "truth": old_truth.get((url, clause), ""), "words": words})
            print(f"{sum(r['model'] == 'missing' for r in rows[-len(REQUIRED):])} missing  {words:6} words  {url}")
        browser.close()

    with NEW_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS + ["words"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {NEW_OUT}")


def score(path=OUT):
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8")) if r["truth"] in ("present", "missing")]
    if not rows:
        print("No truth filled in yet.")
        return
    tp = sum(r["model"] == "missing" and r["truth"] == "missing" for r in rows)   # correctly flagged
    fp = sum(r["model"] == "missing" and r["truth"] == "present" for r in rows)   # false alarm
    fn = sum(r["model"] == "present" and r["truth"] == "missing" for r in rows)   # missed a gap
    correct = sum(r["model"] == r["truth"] for r in rows)
    print(f"{len(rows)} policy/clause decisions checked")
    print(f"Accuracy: {correct / len(rows):.1%}  ({correct}/{len(rows)})")
    print(f"Gaps correctly flagged: {tp} | false alarms: {fp} | gaps missed: {fn}")
    for clause in REQUIRED:
        sub = [r for r in rows if r["clause"] == clause]
        if sub:
            print(f"  {clause:15} {sum(r['model'] == r['truth'] for r in sub)}/{len(sub)} correct")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["new"]:
        run_new()
    elif args[:1] == ["score"]:
        score(NEW_OUT if args[1:] == ["new"] else OUT)
    else:
        run()
