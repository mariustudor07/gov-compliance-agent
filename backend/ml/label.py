"""Step 1 of our own model: build the training data in data/labels.csv.

Plan:
  1. Put 20-30 privacy policy URLs in POLICY_URLS (mix of gov.uk, big companies, small sites).
  2. Run this file. It downloads each page, splits it into sentences, and asks Gemini to
     suggest a label for each one.
  3. Open data/labels.csv (PyCharm or Excel) and FIX THE WRONG LABELS BY HAND.
     This step is what makes it our dataset and our model. Aim for ~400 good rows.
  4. Run train.py.
"""
import csv
import os
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

LABELS = ["controller", "purpose", "lawful_basis", "rights", "retention",
          "contact_dpo", "third_parties", "complaints_ico", "other"]

POLICY_URLS = [
    "https://www.gov.uk/help/privacy-notice",
    # TODO: add 20-30 more privacy policy URLs
]

OUT = Path(__file__).resolve().parents[2] / "data" / "labels.csv"


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in parts if 30 <= len(s.strip()) <= 400]


def suggest_label(client, sentence):
    prompt = (f"Classify this sentence from a UK privacy policy into exactly one of: {', '.join(LABELS)}.\n"
              f"Reply with the label only.\n\nSentence: {sentence}")
    reply = client.models.generate_content(model=os.environ["GEMINI_MODEL"], contents=prompt)
    label = reply.text.strip().lower()
    return label if label in LABELS else "other"


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sentence", "label", "source"])
        for url in POLICY_URLS:
            html = httpx.get(url, follow_redirects=True, timeout=20).text
            text = BeautifulSoup(html, "html.parser").get_text("\n")
            for s in sentences(text):
                writer.writerow([s, suggest_label(client, s), url])
            print(f"done {url}")
    print(f"Wrote {OUT}. Now check the labels by hand!")


if __name__ == "__main__":
    main()
