"""Opens the site in a real Chromium browser and collects everything the checks need.

Built on Scrapling (github.com/D4Vinci/Scrapling): StealthySession drives a patched Chromium
that looks like a normal visitor's browser, retries failed loads, and keeps one browser open for
the whole scan. Scrapling's Fetcher also reads robots.txt and the sitemap, so we find privacy,
cookie and accessibility pages that the homepage doesn't link to.

Scrapling can solve Cloudflare challenges (solve_cloudflare); we leave that off on purpose.
We don't try to get around bot protection: blocked.py reports those sites as "couldn't scan".
"""
import asyncio
import gzip
import logging
import sys
from urllib.parse import urljoin, urlparse

from lxml import etree
from protego import Protego
from scrapling.fetchers import Fetcher, StealthySession

from .accessibility import run_axe
from .privacy_page import link_rank

logging.getLogger("scrapling").setLevel(logging.WARNING)  # one INFO line per request is too noisy

# Links whose URL or text contains one of these are worth visiting.
KEYWORDS = ("privacy", "cookie", "accessibility", "data-protection")
# The pages we need, for looking them up in the sitemap when the homepage doesn't link to one.
PAGE_TYPES = (("privacy", "data-protection"), ("cookie",), ("accessibility",))
SHORT_PAGE_CHARS = 3000  # a privacy page shorter than this is probably a hub linking to the real policy
MAX_SITEMAPS = 5  # sitemap files read per site (an index can list hundreds)
# Sitemaps come from the site we're auditing, so don't expand entities or fetch anything they point to.
SAFE_XML = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
# robots.txt and sitemaps are public files: read them even on a bad certificate (security.py reports that),
# try once, and don't add Scrapling's fake "came from Google" referer.
SITEMAP_REQUEST = {"timeout": 10, "retries": 1, "verify": False, "stealthy_headers": False}


def crawl(url, max_pages=5):
    """Visit the homepage, then the privacy / cookie / accessibility pages it (or its sitemap) links to.

    Returns:
        {
          "pages": [{"url", "html", "text", "headers", "status", "frames_html", "axe_violations"}, ...],
          "cookies_before_consent": [ {name, domain, ...}, ... ],
          "homepage_screenshot": PNG bytes,
        }
    """
    if sys.platform == "win32":
        # Playwright needs this event loop type on Windows when run inside uvicorn.
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    pages = []
    # bypass_csp lets us inject axe-core; the real CSP header is still recorded for security checks.
    # Scrapling already ignores HTTPS errors, so sites with a bad certificate still get audited
    # (security.py reports the certificate). google_search=False: no fake "came from Google" referer.
    with StealthySession(headless=True, google_search=False, locale="en-GB", network_idle=True,
                         wait=1500, retries=2, timeout=30000,
                         additional_args={"bypass_csp": True, "viewport": {"width": 1366, "height": 768}}) as session:
        home = _visit(session, url, first=True)
        # Nothing has been clicked yet, so every cookie here was set without consent.
        cookies_before_consent = home["cookies"]
        homepage_screenshot = home["screenshot"]  # what a first-time visitor sees, cookie banner included
        pages.append(home["snapshot"])

        host = urlparse(home["snapshot"]["url"]).netloc
        # Proper "privacy notice/policy" links first, cookie/news links last (stable: keeps page order otherwise).
        wanted = sorted(_matching(home["links"], host, KEYWORDS), key=link_rank)
        # Pages the homepage doesn't link to (common for accessibility statements) can still be in the sitemap.
        missing = [words for words in PAGE_TYPES if not any(w in h.lower() for w in words for h in wanted)]
        if missing:
            sitemap = _sitemap_links(home["snapshot"]["url"])
            for words in missing:
                wanted += sorted(_matching(sitemap, host, words), key=link_rank)[:1]
        visited = {_same_page(home["snapshot"]["url"])}

        for href in wanted[: max_pages - 1]:
            if _same_page(href) in visited:
                continue
            try:
                visit = _visit(session, href)
                pages.append(visit["snapshot"])
                visited.update({_same_page(href), _same_page(visit["snapshot"]["url"])})
            except Exception as e:
                print(f"Could not open {href}: {e}")
                continue
            # Many sites link to a short privacy "hub" page that links on to the real policy.
            # Follow those links one level deeper so we read the actual notice.
            if "privacy" in visit["snapshot"]["url"].lower() and len(visit["snapshot"]["text"]) < SHORT_PAGE_CHARS:
                deeper = sorted((h for h in _matching(visit["links"], host, ("privacy",))
                                 if _same_page(h) not in visited), key=link_rank)
                for deep in deeper[:2]:
                    try:
                        visit = _visit(session, deep)
                        pages.append(visit["snapshot"])
                        visited.update({_same_page(deep), _same_page(visit["snapshot"]["url"])})
                    except Exception as e:
                        print(f"Could not open {deep}: {e}")

    return {"pages": pages, "cookies_before_consent": cookies_before_consent,
            "homepage_screenshot": homepage_screenshot}


def _visit(session, url, first=False):
    """Open one page with Scrapling and collect what the checks need while the page is still open."""
    seen = {}

    def inspect(page):
        # Runs inside the open page after it has loaded (Scrapling's page_action hook).
        # Order matters: read the HTML before axe-core injects its own <script>.
        if first:
            seen["screenshot"] = page.screenshot()
        seen["html"] = page.content()
        seen["text"] = page.inner_text("body")
        seen["frames_html"] = _frames_html(page)
        seen["links"] = _links(page)
        seen["axe_violations"] = run_axe(page)

    response = session.fetch(url, page_action=inspect)
    if "html" not in seen:
        raise RuntimeError(f"page loaded but could not be read (HTTP {response.status})")
    return {
        "snapshot": {
            "url": response.url,
            "html": seen["html"],
            "text": seen["text"],
            "headers": dict(response.headers),
            "status": response.status,
            "frames_html": seen["frames_html"],
            "axe_violations": seen["axe_violations"],
        },
        "links": seen["links"],
        "cookies": [dict(c) for c in response.cookies],
        "screenshot": seen.get("screenshot"),
    }


def _links(page):
    """Every link on the page as (href, text)."""
    # SVG links have an object as href (with .baseVal), not a string; that crashed the scan on cam.ac.uk.
    return page.eval_on_selector_all(
        "a[href]", "els => els.map(e => [typeof e.href === 'string' ? e.href : (e.href && e.href.baseVal) || '', e.innerText || ''])")


def _matching(links, host, keywords):
    """Same-site links whose URL or text contains one of the keywords, in page order, no duplicates."""
    found, seen = [], set()
    for href, label in links:
        if not href.startswith("http"):
            continue
        href = href.split("#")[0]
        text = (href + " " + label).lower()
        if urlparse(href).netloc == host and any(k in text for k in keywords) and _same_page(href) not in seen:
            found.append(href)
            seen.add(_same_page(href))
    return found


def _same_page(url):
    """/accessibility and /accessibility/ are the same page."""
    return url.split("#")[0].rstrip("/").lower()


def _sitemap_links(site_url):
    """(url, "") pairs from the site's sitemap(s), found via robots.txt or /sitemap.xml. [] on any failure."""
    queue = []
    try:
        robots = Fetcher.get(urljoin(site_url, "/robots.txt"), **SITEMAP_REQUEST)
        if robots.status == 200:
            queue = list(Protego.parse(robots.body.decode("utf-8", "replace").removeprefix("﻿")).sitemaps)
    except Exception as e:
        print(f"Could not read robots.txt: {e}")
    queue = queue or [urljoin(site_url, "/sitemap.xml")]

    urls, read = [], 0
    while queue and read < MAX_SITEMAPS:
        sitemap = queue.pop(0)
        read += 1
        try:
            response = Fetcher.get(sitemap, **SITEMAP_REQUEST)
            if response.status != 200:
                continue
            body = response.body
            if body[:2] == b"\x1f\x8b":  # .xml.gz
                body = gzip.decompress(body)
            root = etree.fromstring(body, SAFE_XML)
        except Exception as e:
            print(f"Could not read sitemap {sitemap}: {e}")
            continue
        locs = [el.text.strip() for el in root.iter("{*}loc") if el.text]
        if etree.QName(root).localname == "sitemapindex":
            # Sitemaps for pages/info come first; news and product sitemaps rarely hold policies.
            queue += sorted(locs, key=lambda u: any(w in u.lower() for w in ("news", "product", "article", "blog")))
        else:
            urls += locs
    return [(u, "") for u in urls]


def _frames_html(page):
    """HTML of the page's iframes: some consent tools (e.g. Sourcepoint) draw the banner in one."""
    frames = []
    for frame in page.frames[1:]:
        try:
            frames.append(frame.content())
        except Exception:
            pass  # frame navigated away or is cross-origin and gone
    return frames
