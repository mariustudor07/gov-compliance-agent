"""ADMIN script, run by a person: makes sure the Atlas search indexes exist (recreates any that were deleted).

    cd backend
    python -m db.search_indexes

- rules_vector   (Vector Search on Compliance_Rules.Embedding): finds the rule matching a problem by meaning.
                 Needs the embeddings from `python -m db.embed_rules`.
- findings_text  (Atlas Search on Findings): full-text search over everything ever found.
Existing indexes are left alone. Safe to run any time.
"""
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from pymongo.operations import SearchIndexModel  # noqa: E402

from .client import get_db  # noqa: E402

INDEXES = {
    ("Compliance_Rules", "rules_vector"): ("vectorSearch", {
        "fields": [{"type": "vector", "path": "Embedding", "numDimensions": 1024, "similarity": "cosine"}]}),
    ("Findings", "findings_text"): ("search", {
        "mappings": {"dynamic": False, "fields": {
            "Explanation": {"type": "string"},
            "Reccomendation": {"type": "string"},  # Bogdan's schema spelling
            "Evidence": {"type": "document", "fields": {"title": {"type": "string"}, "text": {"type": "string"}}},
            "Rule_ID": {"type": "token"},
            "Severity": {"type": "token"}}}}),
}


def main():
    db = get_db("admin")
    for (collection, name), (kind, definition) in INDEXES.items():
        if name in [i["name"] for i in db[collection].list_search_indexes()]:
            print(f"{name}: already exists")
            continue
        db[collection].create_search_index(SearchIndexModel(name=name, type=kind, definition=definition))
        print(f"{name}: created on {collection}")

    for _ in range(60):  # new indexes take a minute or so to become searchable
        status = {name: next((i.get("queryable") for i in db[c].list_search_indexes() if i["name"] == name), False)
                  for (c, name) in INDEXES}
        if all(status.values()):
            print("all indexes ready:", ", ".join(status))
            return
        time.sleep(5)
    print("still building:", [n for n, ok in status.items() if not ok], "(check Atlas > Atlas Search)")


if __name__ == "__main__":
    main()
