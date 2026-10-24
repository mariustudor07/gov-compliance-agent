"""Gemini looks at the homepage screenshot and judges whether the cookie banner gives a fair choice.

ICO guidance on PECR: rejecting cookies must be as easy as accepting them. A rule can't judge
that from HTML (button size, colour, wording, hidden 'reject' links), but a vision model can,
the same way a person would. Skipped silently when Gemini isn't configured or fails.
"""
import json
import os

from google import genai
from google.genai import types

from scanner.findings import finding

PROMPT = """You are checking a UK website's cookie banner against PECR and the ICO's cookie guidance.
This screenshot shows the homepage exactly as a first-time visitor sees it, before clicking anything.

Reply with JSON only:
{
  "banner_present": true/false,
  "reject_on_first_layer": true/false,          // a 'Reject' / 'Decline' / 'Necessary only' button visible without opening settings
  "reject_as_prominent_as_accept": true/false,  // same size, colour weight and position as 'Accept'
  "pre_ticked_boxes": true/false,
  "evidence": "one sentence describing exactly what you see on the banner"
}"""


def check_banner(screenshot, page_url):
    """Returns cookie-banner findings, or [] if Gemini is unavailable."""
    if not screenshot or not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL"):
        return []
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        reply = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"],
            contents=[types.Part.from_bytes(data=screenshot, mime_type="image/png"), PROMPT],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        verdict = json.loads(reply.text)
    except Exception as e:
        print(f"Cookie banner check skipped: {e}")
        return []
    return findings_from_verdict(verdict, page_url)


def findings_from_verdict(verdict, page_url):
    if not verdict.get("banner_present"):
        return []  # no banner: the pre-consent cookie check already covers what matters

    evidence = f"Gemini, from a screenshot of the first visit: {verdict.get('evidence', '')}"
    findings = []
    if not verdict.get("reject_on_first_layer"):
        findings.append(finding("ck-banner-noreject", "cookies", "high",
                                "Cookie banner has no 'Reject' option on the first screen",
                                evidence=evidence, page=page_url))
    elif not verdict.get("reject_as_prominent_as_accept"):
        findings.append(finding("ck-banner-unequal", "cookies", "medium",
                                "'Reject' is less prominent than 'Accept' on the cookie banner",
                                evidence=evidence, page=page_url))
    if verdict.get("pre_ticked_boxes"):
        findings.append(finding("ck-banner-preticked", "cookies", "high",
                                "Cookie banner has pre-ticked consent boxes",
                                evidence=evidence, page=page_url))
    if not findings:
        findings.append(finding("ck-banner-fair", "cookies", "pass",
                                "Cookie banner gives a fair choice between accepting and rejecting",
                                evidence=evidence, page=page_url))
    return findings
