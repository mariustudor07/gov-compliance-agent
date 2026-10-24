"""When a site blocks our scanner, Gemini reads its privacy notice through Google instead.

Gemini's built-in Google Search + URL context tools fetch the page on Google's side (an official API
feature; sites that block bots usually still let Google read their privacy notice). Gemini returns one
word-for-word quote per required clause, and OUR classifier double-checks each quote, so a made-up or
off-topic quote doesn't count. Only the privacy section can be checked this way: cookies, accessibility
and security need a real browser on the site. One Gemini call per blocked scan.
"""
import json
import os
import re

from google import genai
from google.genai import types

from ml.classify import REQUIRED, clause_probability
from scanner.findings import finding

from .prompts import CLAUSE_TITLES

MIN_AGREEMENT = 0.2  # our model must give the quote at least this probability for the clause
CONTACT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|data protection officer", re.I)

PROMPT = """Find the official UK privacy notice (privacy policy) of the website {url} and read it.
For each requirement below, copy ONE sentence word-for-word from the notice that covers it, or null if
the notice doesn't cover it. Never invent or paraphrase a sentence.
{clauses}.
Reply with JSON only: {{"privacy_url": "...", "quotes": {{"controller": "..." or null, ...}}}}"""


def _is_contact(quote, clause):
    # A bare address like "DPO@Tesco.com" is a valid contact, but not a sentence our classifier can judge.
    return clause == "contact_dpo" and bool(CONTACT.search(quote))


def privacy_via_gemini(url):
    """Returns (privacy_url, findings), or None if Gemini is unavailable or fails."""
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL"):
        return None
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        reply = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"],
            contents=PROMPT.format(url=url, clauses=", ".join(REQUIRED)),
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch()),
                                                      types.Tool(url_context=types.UrlContext())]),
        )
        text = reply.text.strip().removeprefix("```json").removesuffix("```").strip()
        answer = json.loads(text)
    except Exception as e:
        print(f"Gemini privacy fallback failed: {e}")
        return None

    privacy_url = answer.get("privacy_url") or ""
    quotes = answer.get("quotes") or {}
    source = f"read by Gemini via Google ({privacy_url}); our scanner was blocked"
    findings, confirmed = [], 0
    for clause in REQUIRED:
        quote = quotes.get(clause)
        if quote and (clause_probability(quote, clause) >= MIN_AGREEMENT or _is_contact(quote, clause)):
            confirmed += 1
            continue
        evidence = (f"Gemini's quote wasn't confirmed by our classifier: \"{quote[:150]}\"" if quote
                    else "Gemini found no sentence covering this") + f" | {source}"
        findings.append(finding(f"pv-{clause}", "privacy", "high", CLAUSE_TITLES[clause],
                                evidence=evidence, page=privacy_url, regulation="UK GDPR Art. 13"))
    if not findings:
        findings.append(finding("pv-complete", "privacy", "pass",
                                "Privacy notice covers all required UK GDPR Art. 13 information",
                                evidence=f"all {confirmed} quotes confirmed by our classifier | {source}",
                                page=privacy_url))
    return privacy_url, findings
