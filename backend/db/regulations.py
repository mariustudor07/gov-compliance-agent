"""search_regulations(query): finds the UK rule (and its legal text) that matches a compliance problem,
using Voyage AI embeddings + Atlas Vector Search on Compliance_Rules (see db/embed_rules.py).

Gemini calls this as a tool while writing the report, so keep the type hints and docstring. It goes
through AgentStore, so Bogdan's permission table applies and every rule read is an audit event.
"""
import os

from .client import db_enabled

LAW_EXCERPT_CHARS = 1500


def _compact(rules):
    return [{"rule_id": r["Rule_ID"], "title": r["Rule_Title"], "requirement": r["Requirement"],
             "source": r["Src_ID"], "law": r.get("Legal_Text", "")[:LAW_EXCERPT_CHARS],
             "law_url": (r.get("Legal_Text_URLs") or [""])[0]} for r in rules]


def search_regulations_batch(queries: list[str], limit: int = 2) -> list[list[dict]]:
    """The matching rules for several problems, using ONE Voyage request. [] per query if unavailable."""
    if not queries or not db_enabled() or not os.getenv("VOYAGE_API_KEY"):
        return [[] for _ in queries]
    try:
        from .agent_store import AgentStore
        return [_compact(rules) for rules in AgentStore().search_rules_batch(queries, limit)]
    except Exception as e:
        print(f"search_regulations failed: {e}")
        return [[] for _ in queries]


def search_regulations(query: str) -> list[dict]:
    """Search the UK rules GovCheck checks (UK GDPR, PECR, the 2018 accessibility regulations, WCAG 2.2,
    NCSC guidance) for the ones most relevant to a compliance problem, with the actual legal text.

    Args:
        query: a description of the problem, e.g. "analytics cookies set before consent".

    Returns:
        Up to 3 rules, each with rule_id, title, requirement, source, law (an excerpt of the legal text)
        and law_url.
    """
    return search_regulations_batch([query], 3)[0]
