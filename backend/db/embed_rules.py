"""ADMIN script, run by a person: Voyage AI embeddings for Compliance_Rules + the Atlas Vector Search index.

Each rule's title, requirement, description and legal text is turned into an embedding (1024 numbers
that capture its meaning) and stored in the rule's `Embedding` field. The index `rules_vector` lets the
agent find the rule that matches a problem by meaning (db.agent_store.AgentStore.search_rules).
Runs as the admin user: the AI agent may only read rules. Re-run after `python -m db.seed`.

    cd backend
    python -m db.embed_rules
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

import voyageai  # noqa: E402
from pymongo.operations import SearchIndexModel  # noqa: E402

from .client import get_db  # noqa: E402

EMBED_MODEL = "voyage-3.5"
DIMENSIONS = 1024
INDEX = "rules_vector"


# Without a payment method on the Voyage account the limits are 3 requests and 10K tokens per minute,
# so rules are sent in small batches with a pause in between (about a minute in total for 18 rules).
BATCH = 6
PAUSE_SECONDS = 22
LEGAL_TEXT_CHARS = 2500  # enough of the law to match by meaning, and keeps each batch under 10K tokens


def rule_text(rule):
    return "\n".join([rule["Rule_Title"], rule["Requirement"], rule["Description"],
                      rule.get("Legal_Text", "")[:LEGAL_TEXT_CHARS]])


def main():
    db = get_db("admin")
    rules = list(db.Compliance_Rules.find({}, {"_id": 0, "Embedding": 0}))
    client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    vectors = []
    for i in range(0, len(rules), BATCH):
        if i:
            time.sleep(PAUSE_SECONDS)
        batch = [rule_text(r) for r in rules[i:i + BATCH]]
        vectors += client.embed(batch, model=EMBED_MODEL, input_type="document").embeddings
        print(f"embedded {len(vectors)}/{len(rules)}")
    for rule, vector in zip(rules, vectors):
        db.Compliance_Rules.update_one({"Rule_ID": rule["Rule_ID"]},
                                       {"$set": {"Embedding": vector, "Embedding_Model": EMBED_MODEL}})
    print(f"embedded {len(rules)} rules with {EMBED_MODEL}")

    if INDEX not in [i["name"] for i in db.Compliance_Rules.list_search_indexes()]:
        db.Compliance_Rules.create_search_index(SearchIndexModel(
            name=INDEX, type="vectorSearch",
            definition={"fields": [{"type": "vector", "path": "Embedding",
                                    "numDimensions": DIMENSIONS, "similarity": "cosine"}]}))
        print(f"created vector index {INDEX}")
    for _ in range(60):  # a new index takes a little while to become searchable
        index = next(i for i in db.Compliance_Rules.list_search_indexes() if i["name"] == INDEX)
        if index.get("queryable"):
            print(f"index {INDEX} is ready")
            return
        time.sleep(5)
    print(f"index {INDEX} is still building; check Atlas > Search & Vector Search")


if __name__ == "__main__":
    main()
