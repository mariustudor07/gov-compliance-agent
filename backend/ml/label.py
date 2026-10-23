"""Step 1 of our own model: build the training data in data/labels.csv.

How it works (human-in-the-loop labelling):
  1. Download each privacy notice in POLICY_URLS and take a random sample of sentences.
  2. Gemini labels every sentence TWICE, with two differently worded prompts.
  3. If the two labels agree, it's probably right. If they disagree, the row gets
     needs_review = True.
  4. YOU open data/labels.csv, filter needs_review = True, and fix the `label` column.
     Then skim the rest. This is what makes it our dataset.
  5. Run train.py, or explore in notebooks/01_classifier_experiments.ipynb.
"""
import csv
import json
import os
import random
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# What each label means. Used in the prompts, and a guide for checking labels by hand.
LABEL_GUIDE = {
    "controller": "who is responsible for the data (organisation name, 'we are the data controller')",
    "purpose": "why personal data is collected or what it is used for",
    "lawful_basis": "the legal basis: consent, contract, legal obligation, vital interests, public task, legitimate interests",
    "rights": "people's data rights: access, rectification, erasure, restriction, portability, objection",
    "retention": "how long data is kept or when it is deleted",
    "contact_dpo": "how to contact the organisation or its Data Protection Officer about data",
    "third_parties": "who data is shared with, sold to, or transferred to (including outside the UK)",
    "complaints_ico": "the right to complain to the ICO (Information Commissioner's Office)",
    "other": "anything else: cookies detail, definitions, navigation text, general statements",
}
LABELS = list(LABEL_GUIDE)

# Checked 23 Oct: all of these load without JavaScript and have 25+ usable sentences.
POLICY_URLS = [
    # UK government and public sector
    "https://www.gov.uk/help/privacy-notice",
    "https://www.ons.gov.uk/aboutus/transparencyandgovernance/dataprotection",
    "https://www.nhs.uk/our-policies/privacy-policy/",
    "https://www.ofcom.org.uk/about-ofcom/foi-dp/general-privacy-statement",
    "https://www.bbc.co.uk/usingthebbc/privacy-policy/",
    "https://www.kcl.ac.uk/terms/privacy",
    "https://www.lse.ac.uk/lse-information/privacy-policy",
    # Charities
    "https://www.cancerresearchuk.org/privacy-statement",
    "https://www.citizensadvice.org.uk/about-us/about-us1/citizens-advice-privacy-policy/",
    "https://www.rspca.org.uk/utilities/privacy",
    # Companies
    "https://www.theguardian.com/help/privacy-policy",
    "https://www.royalmail.com/privacy-notice",
    "https://www.bt.com/privacy-policy",
    "https://monzo.com/legal/privacy-notice",
    "https://www.asos.com/privacy-policy/",
    "https://www.argos.co.uk/help/privacy-policy",
    "https://deliveroo.co.uk/privacy",
    "https://policies.google.com/privacy?hl=en-GB",
    "https://www.spotify.com/uk/legal/privacy-policy/",
    "https://www.mozilla.org/en-GB/privacy/websites/",
]

SENTENCES_PER_URL = 40
BATCH_SIZE = 40
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GovCheck-research/0.1"}
OUT = Path(__file__).resolve().parents[2] / "data" / "labels.csv"

# Two differently worded prompts, so their mistakes don't line up.
PROMPT_A = ("Classify each numbered sentence from a UK privacy notice into exactly one of these labels:\n"
            + "\n".join(f"- {k}: {v}" for k, v in LABEL_GUIDE.items())
            + "\n\nReturn a JSON list of labels, one per sentence, in the same order.\n\n{sentences}")
PROMPT_B = ("You are a UK GDPR auditor checking a privacy notice against Article 13. For each numbered "
            "sentence, which Article 13 requirement does it satisfy? Answer with one of: "
            + ", ".join(LABELS) + " (use 'other' if it satisfies none).\n"
            "Return a JSON list of labels, one per sentence, in the same order.\n\n{sentences}")


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in parts if 30 <= len(s.strip()) <= 400]


def fetch_sentences(url):
    html = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return sentences(soup.get_text("\n"))


def ask_gemini(client, prompt_template, batch):
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(batch))
    reply = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"], contents=prompt_template.format(sentences=numbered),
        config=types.GenerateContentConfig(response_mime_type="application/json"))
    labels = json.loads(reply.text)
    if len(labels) != len(batch):
        labels = (labels + ["other"] * len(batch))[:len(batch)]
    return [lab if lab in LABELS else "other" for lab in labels]


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    random.seed(42)
    rows = []
    for url in POLICY_URLS:
        try:
            sents = fetch_sentences(url)
        except Exception as e:
            print(f"skip {url}: {e}")
            continue
        sample = random.sample(sents, min(SENTENCES_PER_URL, len(sents)))
        rows += [(s, url) for s in sample]
        print(f"{len(sample):3} sentences from {url}")

    disagreements = 0
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sentence", "label", "second_opinion", "needs_review", "source"])
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            texts = [s for s, _ in batch]
            labels_a = ask_gemini(client, PROMPT_A, texts)
            labels_b = ask_gemini(client, PROMPT_B, texts)
            for (sentence, url), a, b in zip(batch, labels_a, labels_b):
                disagreements += a != b
                writer.writerow([sentence, a, b, a != b, url])
            print(f"labelled {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

    print(f"\nWrote {len(rows)} rows to {OUT}")
    print(f"{disagreements} rows need review ({disagreements / max(len(rows), 1):.0%}). "
          f"Filter needs_review = True and fix the label column.")


if __name__ == "__main__":
    main()
