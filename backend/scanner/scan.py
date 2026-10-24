"""run_scan(url) is the scanner's single entry point. The agent calls only this."""
from urllib.parse import urlparse

from .accessibility import check_accessibility
from .blocked import blocked_reason
from .cookies import _base_domain, check_cookies
from .crawler import crawl
from .privacy_page import best_notice
from .security import check_security

PRIVACY_WORDS = ("privacy", "data-protection", "data protection")


def run_scan(url):
    """Returns {"pages_crawled": [...], "findings": [...], "privacy_text": "..."}."""
    crawl_result = crawl(url)
    blocked = blocked_reason(crawl_result["pages"][0])
    if blocked:
        return {"pages_crawled": [p["url"] for p in crawl_result["pages"]], "findings": [], "privacy_text": "",
                "privacy_page": "", "homepage_screenshot": None, "blocked": blocked}

    findings = []
    findings += check_cookies(crawl_result)
    findings += check_accessibility(crawl_result)
    findings += check_security(crawl_result)

    # Skip error pages (404 etc.): a "page not found" is not a privacy notice.
    privacy_pages = [p for p in crawl_result["pages"]
                     if any(w in urlparse(p["url"]).path.lower() for w in PRIVACY_WORDS) and p["status"] < 400]
    # Pick the page that looks most like a real notice, not a news article, cookie page or list of notices.
    privacy_page = best_notice(privacy_pages)
    privacy_text = privacy_page["text"] if privacy_page else ""

    return {
        "pages_crawled": [p["url"] for p in crawl_result["pages"]],
        "findings": findings,
        "privacy_text": privacy_text,
        "privacy_page": privacy_page["url"] if privacy_page else "",
        "homepage_screenshot": crawl_result["homepage_screenshot"],
        "blocked": "",
        "redirected_to": _other_site(url, crawl_result["pages"][0]["url"]),
    }


def _other_site(requested, landed):
    """The address we ended up on, if it belongs to a different website (e.g. encodehub.com is a parked domain
    that redirects to hugedomains.com), else "". Results are then about that other site, and the report says so."""
    a, b = ((urlparse(u).hostname or "").lower().removeprefix("www.") for u in (requested, landed))
    same = (a == b or a.endswith("." + b) or b.endswith("." + a)  # gov.uk <-> www.gov.uk, hub.x.com <-> x.com
            or _base_domain(a) == _base_domain(b))
    return landed if a and b and not same else ""
