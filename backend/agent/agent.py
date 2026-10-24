"""analyse(url): the whole GovCheck pipeline, from URL to finished ScanResult."""
import json
import os
from datetime import datetime, timezone

from google import genai
from google.genai import types

from db.regulations import search_regulations
from ml.classify import missing_clauses, model_name
from scanner.findings import finding
from scanner.scan import run_scan

from .banner import check_banner
from .fixes import apply_fixes, summarise
from .prompts import CLAUSE_TITLES, SYSTEM_PROMPT
from .scoring import score


def analyse(url):
    scan = run_scan(url)
    if scan["blocked"]:
        # Honest "couldn't scan" result: no scores, no findings, so we never blame a site for its bot protection.
        return {
            "url": url,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "pages_crawled": scan["pages_crawled"],
            "blocked": True,
            "scores": {},
            "findings": [],
            "summary": (f"We couldn't scan this site: {scan['blocked']}. Many large sites block automated "
                        "tools, so this says nothing about whether the site is compliant. It needs a manual check."),
        }
    banner = check_banner(scan["homepage_screenshot"], scan["pages_crawled"][0])
    scanner_findings = scan["findings"]
    if banner:  # Gemini judged the banner from a screenshot: use that instead of the HTML check, so it isn't penalised twice
        scanner_findings = [f for f in scanner_findings if f["id"] != "ck-banner"]
    findings = apply_fixes(scanner_findings + banner + _privacy_findings(scan))
    summary = _explain_with_gemini(url, findings) or summarise(findings)

    return {
        "url": url,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "pages_crawled": scan["pages_crawled"],
        "scores": score(findings),
        "findings": findings,
        "summary": summary,
    }


MIN_POLICY_WORDS = 250  # shorter than this, there's not enough text to judge which clauses are missing


def _privacy_findings(scan):
    """Runs OUR classifier on the privacy policy."""
    page = scan["privacy_page"]
    if not scan["privacy_text"]:
        return [finding("pv-none", "privacy", "critical", "No privacy notice found",
                        evidence="no privacy page linked from the homepage", regulation="UK GDPR Art. 13")]
    words = len(scan["privacy_text"].split())
    if words < MIN_POLICY_WORDS:
        # Too little text to judge: probably a menu page or a policy we couldn't load.
        # Better to say so than to report every clause as missing.
        return [finding("pv-short", "privacy", "medium", "Couldn't find a full privacy notice",
                        evidence=f"the privacy page we found has only {words} words", page=page)]

    missing = missing_clauses(scan["privacy_text"])
    if not missing:
        return [finding("pv-complete", "privacy", "pass",
                        "Privacy notice covers all required UK GDPR Art. 13 information",
                        evidence=f"checked by our {model_name()}", page=page)]
    return [finding(f"pv-{clause}", "privacy", "high", CLAUSE_TITLES[clause],
                    evidence=f"our {model_name()} found no sentence covering this",
                    page=page, regulation="UK GDPR Art. 13")
            for clause in missing]


def _explain_with_gemini(url, findings):
    """Gemini adds a regulation + fix to each finding and writes the summary.
    It can call search_regulations() itself to look up the law in MongoDB."""
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("GEMINI_MODEL"):
        return ""  # built-in fixes and summary are used instead

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    problems = [f for f in findings if f["severity"] != "pass"]
    try:
        response = client.models.generate_content(
            model=os.environ["GEMINI_MODEL"],
            contents=f"Website: {url}\n\nFindings:\n{json.dumps(problems, indent=2)}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[search_regulations],  # the SDK runs the tool calls for us
            ),
        )
    except Exception as e:
        print(f"Gemini failed, using built-in fixes: {e}")
        return ""

    try:
        text = response.text.strip().removeprefix("```json").removesuffix("```")
        answer = json.loads(text)
    except (ValueError, AttributeError):
        return response.text or ""

    by_id = {f["id"]: f for f in findings}
    for item in answer.get("findings", []):
        f = by_id.get(item.get("id"))
        if f:
            f["fix"] = item.get("fix") or f["fix"]
            f["regulation"] = item.get("regulation") or f["regulation"]
            f["severity_reason"] = item.get("severity_reason") or f.get("severity_reason", "")
    return answer.get("summary", "")
