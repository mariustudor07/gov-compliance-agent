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
          "pages": [{"url", "html", "text", "headers", "frames_html", "axe_violations"}, ...],
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
        # ignore_https_errors lets us audit sites with a bad certificate; security.py reports the certificate.
        context = browser.new_context(bypass_csp=True, ignore_https_errors=True)
        page = context.new_page()

        response = _goto(page, url)
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
                response = _goto(page, href)
                pages.append(_snapshot(page, response))
            except Exception as e:
                print(f"Could not open {href}: {e}")

        browser.close()

    return {"pages": pages, "cookies_before_consent": cookies_before_consent}


def _goto(page, url):
    """Open a page and wait until JavaScript-rendered content (React/Next.js sites) has loaded."""
    response = page.goto(url, wait_until="load", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass  # sites with constant background traffic never go idle; carry on with what we have
    page.wait_for_timeout(1500)  # cookie scripts and late renders
    return response


def _snapshot(page, response):
    return {
        "url": page.url,
        "html": page.content(),
        "text": page.inner_text("body"),
        "headers": response.all_headers() if response else {},
        "frames_html": _frames_html(page),
        "axe_violations": run_axe(page),
    }


def _frames_html(page):
    """HTML of the page's iframes: some consent tools (e.g. Sourcepoint) draw the banner in one."""
    frames = []
    for frame in page.frames[1:]:
        try:
            frames.append(frame.content())
        except Exception:
            pass  # frame navigated away or is cross-origin and gone
    return frames
