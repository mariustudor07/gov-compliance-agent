"""Choosing the right privacy notice among the pages we found.

"Longest page with 'privacy' in the link" picked news articles, cookie pages and lists of notices
(found by testing on 230 UK sites). Instead we score how much a page looks like a privacy notice:
its URL, and whether its text covers the basics a UK GDPR notice always has.
"""
import re
from urllib.parse import urlparse

GOOD_URL = re.compile(r"privacy[-_ ]?(notice|policy|statement)|/privacy/?$|/privacy(\.html?)?$|data[-_]protection", re.I)
BAD_URL = re.compile(r"cookie|news|blog|press|article|scam|fraud|settings|subject[-_]access|request|search", re.I)
# Notices for one audience or one service (CBBC children's policy on bbc.co.uk, job applicants, CCTV,
# Freedom of Information pages...) are real notices, but not the site's main one.
NARROW_URL = re.compile(r"cbbc|child|kids|alumni|applicant|recruit|jobs?\b|careers|student|staff|employee|"
                        r"cctv|body-worn|camera|supporter|volunteer|freedom[-_]of[-_]information|\bfoi\b|"
                        r"your-rights|directory|candidate", re.I)
# A page NAMED like the site's own notice or privacy hub (/privacy, /privacy-policy, /privacy-and-data),
# not one service's notice (Brighton's sitemap has dozens like /carers-survey-privacy-notice).
MAIN_NOTICE = re.compile(r"^(privacy|data[-_]protection)([-_](notice|policy|statement|and[-_]data|"
                         r"and[-_]cookies|centre|center))?(\.html?)?$", re.I)
NOTICE_SIGNALS = 3  # a page covering fewer of CONTENT_SIGNALS is a hub or a list, not the notice itself
READABLE_WORDS = 100  # fewer words than this: a PDF/download or an empty page, not text we can check

# Things every UK GDPR privacy notice mentions. A page covering several is very likely the real notice.
CONTENT_SIGNALS = [
    re.compile(p, re.I) for p in (
        r"\bcontroller\b",
        r"lawful basis|legal basis|legitimate interests?",
        r"your rights|right to (access|object|erasure|rectif|restrict)",
        r"how long|\bretain|retention",
        r"information commissioner|\bico\b",
        r"data protection officer|\bdpo\b",
    )
]


def link_rank(url):
    """Lower is better: proper privacy-notice links first, cookie/news links last."""
    return (0 if GOOD_URL.search(url) else 1) + (2 if BAD_URL.search(url) else 0) + (1 if NARROW_URL.search(url) else 0)


def page_name(url):
    """The last part of the address: "languages" for /about-website/website-and-accessibility/languages."""
    return urlparse(url).path.rstrip("/").rsplit("/", 1)[-1].lower()


def is_main_notice(url):
    return bool(MAIN_NOTICE.search(page_name(url)))


def _signals(text):
    return sum(bool(p.search(text)) for p in CONTENT_SIGNALS)


def looks_like_notice(text):
    """False for hubs and lists of notices, whose real notice is one link deeper."""
    return _signals(text) >= NOTICE_SIGNALS


def notice_score(url, text):
    score = _signals(text) * 2
    score += 3 if GOOD_URL.search(url) else 0
    score -= 4 if BAD_URL.search(url) else 0
    score -= 3 if NARROW_URL.search(url) else 0
    return score + min(len(text.split()) / 4000, 1)  # length only breaks ties


def best_notice(pages):
    """pages: [{"url", "full_text" (or just "text"), ...}] -> the one most likely to be the privacy notice, or None.
    A page we could read beats one we couldn't: Camden's best-named link is a PDF with no page text."""
    def key(page):
        text = page.get("full_text", page.get("text", ""))  # ml/evaluate_documents.py passes "text"
        return len(text.split()) >= READABLE_WORDS, notice_score(page["url"], text)
    return max(pages, key=key, default=None)
