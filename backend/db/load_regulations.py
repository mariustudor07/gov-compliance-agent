"""One-off script: load the law text into MongoDB with embeddings, for Vector Search.

1. Save each regulation as a .txt file in data/regulations/, named after its source,
   e.g. "PECR.txt", "UK GDPR.txt", "WCAG 2.2.txt".
   Start each section with a line like:  ### reg. 6   or   ### Art. 13
2. Run:  python -m db.load_regulations   (from the backend folder)
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .client import get_db  # noqa: E402
from .regulations import embed  # noqa: E402

REG_DIR = Path(__file__).resolve().parents[2] / "data" / "regulations"


def chunks(path):
    section, lines = "", []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            if lines:
                yield section, "\n".join(lines).strip()
            section, lines = line[4:].strip(), []
        else:
            lines.append(line)
    if lines:
        yield section, "\n".join(lines).strip()


def main():
    docs = []
    for path in REG_DIR.glob("*.txt"):
        for section, text in chunks(path):
            if text:
                docs.append({"source": path.stem, "section": section, "text": text})
    print(f"{len(docs)} chunks")

    vectors = []
    for i in range(0, len(docs), 100):
        vectors += embed([d["text"] for d in docs[i:i + 100]], "document")
    for d, v in zip(docs, vectors):
        d["embedding"] = v

    get_db().regulations.delete_many({})
    get_db().regulations.insert_many(docs)
    print("Loaded into MongoDB. Now create the Vector Search index in Atlas (see regulations.py).")


if __name__ == "__main__":
    main()
