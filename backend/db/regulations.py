"""search_regulations(query): finds the most relevant pieces of UK law with Atlas Vector Search.
Gemini calls this as a tool, so keep the type hints and docstring."""
import os

import voyageai

from .client import db_enabled, get_db

EMBED_MODEL = "voyage-3.5"
INDEX_NAME = "regulations_vector"  # TODO(Bogdan): create this Vector Search index in Atlas on field "embedding"


def embed(texts: list[str], input_type: str) -> list[list[float]]:
    client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])
    return client.embed(texts, model=EMBED_MODEL, input_type=input_type).embeddings


def search_regulations(query: str) -> list[dict]:
    """Search UK regulations (UK GDPR, PECR, WCAG 2.2, Accessibility Regulations 2018, NCSC)
    for the passages most relevant to a compliance problem.

    Args:
        query: a description of the problem, e.g. "analytics cookies set before consent".

    Returns:
        Up to 3 passages, each with source, section and text.
    """
    if not db_enabled() or not os.getenv("VOYAGE_API_KEY"):
        return []
    pipeline = [
        {"$vectorSearch": {"index": INDEX_NAME, "path": "embedding",
                           "queryVector": embed([query], "query")[0],
                           "numCandidates": 50, "limit": 3}},
        {"$project": {"_id": 0, "source": 1, "section": 1, "text": 1}},
    ]
    try:
        return list(get_db().regulations.aggregate(pipeline))
    except Exception as e:
        print(f"search_regulations failed: {e}")
        return []
