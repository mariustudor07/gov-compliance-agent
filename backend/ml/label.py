"""Step 1 of our own model: build the training data in data/labels.csv.

Plan:
  1. POLICY_URLS below has a mix of UK government, public sector and company privacy notices.
  2. Run this file. It downloads each page, splits it into sentences, takes a sample, and asks
     Gemini to suggest a label for each one (in batches, so it's quick and cheap).
  3. Open data/labels.csv (PyCharm or Excel) and FIX THE WRONG LABELS BY HAND.
     This step is what makes it our dataset and our model. Aim for ~400 good rows.
  4. Run train.py, or explore in notebooks/01_classifier_experiments.ipynb.
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

LABELS = ["controller", "purpose", "lawful_basis", "rights", "retention",
          "contact_dpo", "third_parties", "complaints_ico", "other"]

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

SENTENCES_PER_URL = 25
BATCH_SIZE = 40
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GovCheck-research/0.1"}
OUT = Path(__file__).resolve().parents[2] / "data" / "labels.csv"


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in parts if 30 <= len(s.strip()) <= 400]


def fetch_sentences(url):
    html = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return sentences(soup.get_text("\n"))


def suggest_labels(client, batch):
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(batch))
    prompt = (f"Classify each numbered sentence from a UK privacy notice into exactly one of: "
              f"{', '.join(LABELS)}.\n"
              f"Return a JSON list of labels, one per sentence, in the same order.\n\n{numbered}")
    reply = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"], contents=prompt,
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

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sentence", "label", "source"])
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            labels = suggest_labels(client, [s for s, _ in batch])
            for (sentence, url), label in zip(batch, labels):
                writer.writerow([sentence, label, url])
            print(f"labelled {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

    print(f"Wrote {OUT}. Now check the labels by hand!")


if __name__ == "__main__":
    main()
