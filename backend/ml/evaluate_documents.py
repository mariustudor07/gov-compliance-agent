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
SITES_OUT = DATA / "doc_eval_sites.csv"
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


def _find_policy(browser, homepage):
    """Like the scanner: open the homepage, follow privacy links (one level deeper from short hub
    pages), skip error pages, and return the longest privacy page found."""
    from urllib.parse import urlparse

    from scanner.crawler import SHORT_PAGE_CHARS, USER_AGENT, _goto, _matching_links
    from scanner.privacy_page import best_notice, link_rank

    context = browser.new_context(user_agent=USER_AGENT, locale="en-GB")
    page = context.new_page()
    try:
        _goto(page, homepage)
        host = urlparse(page.url).netloc
        candidates = sorted(_matching_links(page, host, ("privacy", "data-protection")), key=link_rank)[:4]
        found = []
        for href in candidates:
            try:
                response = _goto(page, href)
            except Exception:
                continue
            if response and response.status >= 400:
                continue
            text = page.inner_text("body")
            found.append((page.url, text))
            if len(text) < SHORT_PAGE_CHARS:  # privacy hub: follow one level deeper
                deeper = sorted((h for h in _matching_links(page, host, ("privacy",)) if h not in candidates), key=link_rank)
                for deep in deeper[:2]:
                    try:
                        response = _goto(page, deep)
                        if not response or response.status < 400:
                            found.append((page.url, page.inner_text("body")))
                    except Exception:
                        pass
        if not found:
            return {"policy_url": "", "text": "", "error": "no privacy link found"}
        best = best_notice([{"url": u, "text": t} for u, t in found])
        return {"policy_url": best["url"], "text": best["text"], "error": ""}
    except Exception as e:
        return {"policy_url": "", "text": "", "error": str(e).splitlines()[0][:120]}
    finally:
        context.close()


def _crawl_chunk(homepages):
    from playwright.sync_api import sync_playwright

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for homepage in homepages:
            results[homepage] = _find_policy(browser, homepage)
            r = results[homepage]
            print(f"{len(r['text'].split()):6} words  {homepage}  {r['error']}", flush=True)
        browser.close()
    return results


def run_sites(workers=6):
    """Large-scale test: the app's own policy-finding + model on many UK homepages."""
    import json
    from concurrent.futures import ThreadPoolExecutor

    from agent.agent import MIN_POLICY_WORDS
    from ml.classify import classify_sentences

    homepages = [u.strip() for u in (DATA / "test_sites.txt").read_text().splitlines()
                 if u.strip() and not u.startswith("#")]
    cache = DATA / "raw" / "site_texts.json"
    cache.parent.mkdir(exist_ok=True)
    texts = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    todo = [h for h in homepages if h not in texts]
    chunks = [todo[i::workers] for i in range(workers)]
    with ThreadPoolExecutor(workers) as pool:  # each thread runs its own browser
        for result in pool.map(_crawl_chunk, chunks):
            texts.update(result)
    cache.write_text(json.dumps(texts), encoding="utf-8")

    old_truth = {}
    if SITES_OUT.exists():
        old_truth = {(r["policy"], r["clause"]): r["truth"] for r in csv.DictReader(SITES_OUT.open(encoding="utf-8"))}
    rows = []
    for homepage in homepages:
        site = texts[homepage]
        words = len(site["text"].split())
        results = classify_sentences(site["text"]) if words >= MIN_POLICY_WORDS else []
        for clause in REQUIRED:
            hits = [r for r in results if r["label"] == clause and r["confidence"] >= MIN_CONFIDENCE]
            best = max(hits, key=lambda r: r["confidence"]) if hits else None
            verdict = "unreadable" if words < MIN_POLICY_WORDS else "present" if hits else "missing"
            rows.append({"policy": homepage, "clause": clause, "model": verdict,
                         "confidence": f"{best['confidence']:.2f}" if best else "",
                         "evidence": best["sentence"][:300] if best else "",
                         "truth": old_truth.get((homepage, clause), ""), "words": words,
                         "policy_url": site["policy_url"]})
    with SITES_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS + ["words", "policy_url"])
        writer.writeheader()
        writer.writerows(rows)
    readable = {r["policy"] for r in rows if r["model"] != "unreadable"}
    print(f"\n{len(readable)} of {len(homepages)} sites had a readable privacy notice. Wrote {SITES_OUT}")


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
    elif args == ["sites"]:
        run_sites()
    elif args[:1] == ["score"]:
        score({"new": NEW_OUT, "sites": SITES_OUT}.get(args[1] if args[1:] else "", OUT))
    else:
        run()
