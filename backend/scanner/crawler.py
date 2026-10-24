"""Opens the site in a real Chromium browser and collects everything the checks need."""
import asyncio
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .accessibility import run_axe

# Links whose URL or text contains one of these are worth visiting.
KEYWORDS = ("privacy", "cookie", "accessibility", "data-protection")
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/141.0.0.0 Safari/537.36")
SHORT_PAGE_CHARS = 3000  # a privacy page shorter than this is probably a hub linking to the real policy


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
        # A normal browser identity: bot protection (e.g. Cloudflare) blocks "HeadlessChrome" outright,
        # which made 4 of 27 big UK sites show a "security verification" page instead of their policy.
        context = browser.new_context(bypass_csp=True, user_agent=USER_AGENT, locale="en-GB",
                                      viewport={"width": 1366, "height": 768})
        page = context.new_page()

        response = _goto(page, url)
        # Nothing has been clicked yet, so every cookie here was set without consent.
        cookies_before_consent = context.cookies()
        homepage_screenshot = page.screenshot()  # what a first-time visitor sees, cookie banner included
        pages.append(_snapshot(page, response))

        host = urlparse(page.url).netloc
        wanted = _matching_links(page, host, KEYWORDS)
        visited = {page.url}

        for href in wanted[: max_pages - 1]:
            try:
                response = _goto(page, href)
                pages.append(_snapshot(page, response))
                visited.add(page.url)
            except Exception as e:
                print(f"Could not open {href}: {e}")
                continue
            # Many sites link to a short privacy "hub" page that links on to the real policy.
            # Follow those links one level deeper so we read the actual notice.
            if "privacy" in page.url.lower() and len(pages[-1]["text"]) < SHORT_PAGE_CHARS:
                deeper = [h for h in _matching_links(page, host, ("privacy",)) if h not in visited]
                for deep in deeper[:2]:
                    try:
                        response = _goto(page, deep)
                        pages.append(_snapshot(page, response))
                        visited.add(page.url)
                    except Exception as e:
                        print(f"Could not open {deep}: {e}")

        browser.close()

    return {"pages": pages, "cookies_before_consent": cookies_before_consent,
            "homepage_screenshot": homepage_screenshot}


def _matching_links(page, host, keywords):
    """Same-site links whose URL or text contains one of the keywords, in page order, no duplicates."""
    links = page.eval_on_selector_all("a[href]", "els => els.map(e => [e.href, e.innerText])")
    found = []
    for href, label in links:
        href = href.split("#")[0]
        text = (href + " " + label).lower()
        if urlparse(href).netloc == host and any(k in text for k in keywords) and href not in found:
            found.append(href)
    return found


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
        "status": response.status if response else 0,
        "axe_violations": run_axe(page),
    }
