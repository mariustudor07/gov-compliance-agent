"""Opens the site in a real Chromium browser and collects everything the checks need."""
import asyncio
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .accessibility import run_axe

# Links whose URL or text contains one of these are worth visiting.
KEYWORDS = ("privacy", "cookie", "accessibility", "data-protection")


def crawl(url, max_pages=5):
    """Visit the homepage, then the privacy / cookie / accessibility pages it links to.

    Returns:
        {
          "pages": [{"url", "html", "text", "headers", "axe_violations"}, ...],
          "cookies_before_consent": [ {name, domain, ...}, ... ],
        }
    """
    if sys.platform == "win32":
        # Playwright needs this event loop type on Windows when run inside uvicorn.
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    pages = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # bypass_csp lets us inject axe-core; the real CSP header is still recorded for security checks.
        context = browser.new_context(bypass_csp=True)
        page = context.new_page()

        response = page.goto(url, wait_until="load", timeout=30000)
        page.wait_for_timeout(2000)  # give cookie scripts time to run
        # Nothing has been clicked yet, so every cookie here was set without consent.
        cookies_before_consent = context.cookies()
        pages.append(_snapshot(page, response))

        host = urlparse(page.url).netloc
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.href, e.innerText])")
        wanted = []
        for href, label in links:
            text = (href + " " + label).lower()
            if urlparse(href).netloc == host and any(k in text for k in KEYWORDS) and href not in wanted:
                wanted.append(href)

        for href in wanted[: max_pages - 1]:
            try:
                response = page.goto(href, wait_until="load", timeout=30000)
                pages.append(_snapshot(page, response))
            except Exception as e:
                print(f"Could not open {href}: {e}")

        browser.close()

    return {"pages": pages, "cookies_before_consent": cookies_before_consent}


def _snapshot(page, response):
    return {
        "url": page.url,
        "html": page.content(),
        "text": page.inner_text("body"),
        "headers": response.all_headers() if response else {},
        "axe_violations": run_axe(page),
    }
