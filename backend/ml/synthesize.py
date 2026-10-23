"""Optional: Gemini writes extra example sentences for labels that are rare in data/labels.csv.

These go in data/synthetic.csv and are ONLY used for training, never for testing.
The test set must be 100% real sentences, or our accuracy numbers would be meaningless.

Run after label.py and after you've reviewed labels.csv.
"""
import csv
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

from ml.label import LABEL_GUIDE

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DATA = Path(__file__).resolve().parents[2] / "data"
TARGET_PER_LABEL = 80  # top up every label to at least this many examples


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    counts = pd.read_csv(DATA / "labels.csv")["label"].value_counts()

    rows = []
    for label, meaning in LABEL_GUIDE.items():
        if label == "other":
            continue
        missing = TARGET_PER_LABEL - counts.get(label, 0)
        if missing <= 0:
            continue
        prompt = (f"Write {missing} different, realistic sentences that could appear in the privacy notice "
                  f"of a UK organisation (vary the sector: councils, NHS, universities, shops, banks, apps, charities). "
                  f"Every sentence must be about: {meaning}. Vary length and wording; avoid repeating phrases.\n"
                  f"Return a JSON list of strings.")
        reply = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"], contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=1.0))
        sentences = json.loads(reply.text)
        rows += [(s, label) for s in sentences if isinstance(s, str)]
        print(f"{label}: +{len(sentences)}")

    with (DATA / "synthetic.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sentence", "label"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic sentences to data/synthetic.csv")


if __name__ == "__main__":
    main()
