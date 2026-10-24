"""Choosing the right privacy notice among the pages we found.

"Longest page with 'privacy' in the link" picked news articles, cookie pages and lists of notices
(found by testing on 230 UK sites). Instead we score how much a page looks like a privacy notice:
its URL, and whether its text covers the basics a UK GDPR notice always has.
"""
import re

GOOD_URL = re.compile(r"privacy[-_ ]?(notice|policy|statement)|/privacy/?$|/privacy(\.html?)?$|data[-_]protection", re.I)
BAD_URL = re.compile(r"cookie|news|blog|press|article|scam|fraud|settings|subject[-_]access|request|search", re.I)
# Notices for one audience or one service (CBBC children's policy on bbc.co.uk, job applicants, CCTV,
# Freedom of Information pages...) are real notices, but not the site's main one.
NARROW_URL = re.compile(r"cbbc|child|kids|alumni|applicant|recruit|jobs?\b|careers|student|staff|employee|"
                        r"cctv|body-worn|camera|supporter|volunteer|freedom[-_]of[-_]information|\bfoi\b|"
                        r"your-rights", re.I)

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


def notice_score(url, text):
    signals = sum(bool(p.search(text)) for p in CONTENT_SIGNALS)
    score = signals * 2
    score += 3 if GOOD_URL.search(url) else 0
    score -= 4 if BAD_URL.search(url) else 0
    score -= 3 if NARROW_URL.search(url) else 0
    return score + min(len(text.split()) / 4000, 1)  # length only breaks ties


def best_notice(pages):
    """pages: [{"url", "text", ...}] -> the one most likely to be the privacy notice, or None."""
    return max(pages, key=lambda p: notice_score(p["url"], p["text"]), default=None)
