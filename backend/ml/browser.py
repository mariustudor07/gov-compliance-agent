"""Small Playwright helpers for the evaluation scripts (ml/evaluate_documents.py).

The app's scanner now crawls with Scrapling (scanner/crawler.py); the evaluations still drive Playwright
directly, so they keep their own copies of the page-opening and link-finding helpers here.
"""
from urllib.parse import urlparse

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/141.0.0.0 Safari/537.36")


def goto(page, url):
    """Open a page and wait until JavaScript-rendered content has loaded."""
    response = page.goto(url, wait_until="load", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass  # sites with constant background traffic never go idle
    page.wait_for_timeout(1500)
    return response


def matching_links(page, host, keywords):
    """Same-site links whose path or text contains one of the keywords, in page order, no duplicates."""
    links = page.eval_on_selector_all(
        "a[href]", "els => els.map(e => [typeof e.href === 'string' ? e.href : (e.href && e.href.baseVal) || '', e.innerText || ''])")
    found = []
    for href, label in links:
        if not href.startswith("http"):
            continue
        href = href.split("#")[0]
        text = (urlparse(href).path + " " + label).lower()
        if urlparse(href).netloc == host and any(k in text for k in keywords) and href not in found:
            found.append(href)
    return found
