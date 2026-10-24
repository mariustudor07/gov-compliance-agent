"""run_scan(url) is the scanner's single entry point. The agent calls only this."""
from .accessibility import check_accessibility
from .cookies import check_cookies
from .crawler import crawl
from .security import check_security

PRIVACY_WORDS = ("privacy", "data-protection", "data protection")


def run_scan(url):
    """Returns {"pages_crawled": [...], "findings": [...], "privacy_text": "..."}."""
    crawl_result = crawl(url)

    findings = []
    findings += check_cookies(crawl_result)
    findings += check_accessibility(crawl_result)
    findings += check_security(crawl_result)

    privacy_pages = [p for p in crawl_result["pages"] if any(w in p["url"].lower() for w in PRIVACY_WORDS)]
    # The longest privacy page is the real notice, not a hub or a cookie-settings page.
    privacy_page = max(privacy_pages, key=lambda p: len(p["text"]), default=None)
    privacy_text = privacy_page["text"] if privacy_page else ""

    return {
        "pages_crawled": [p["url"] for p in crawl_result["pages"]],
        "findings": findings,
        "privacy_text": privacy_text,
        "privacy_page": privacy_page["url"] if privacy_page else "",
        "homepage_screenshot": crawl_result["homepage_screenshot"],
    }
