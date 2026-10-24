"""Recognise when a site blocks automated browsers, so we report "couldn't scan" instead of fake failures.

Found by testing 230 UK homepages: Tesco ("Access Denied"), Birmingham council ("403 Forbidden"),
UCL (Cloudflare "Performing security verification") and Boots (blank page) all block headless
browsers. Scanning those pages would wrongly report e.g. "No privacy notice found".
We don't try to get around bot protection.
"""
import re

BLOCK_STATUS = {401, 403, 429, 503}
BLOCK_TEXT = re.compile(
    r"access denied|performing security verification|403 forbidden|you have been blocked|"
    r"attention required|verify you are (a )?human|request unsuccessful|are you a robot|captcha",
    re.I)


def blocked_reason(homepage):
    """homepage: the crawler's snapshot of the first page. Returns a reason, or "" if not blocked."""
    words = len(homepage["text"].split())
    if homepage["status"] in BLOCK_STATUS:
        return f"the site refused automated access (HTTP {homepage['status']})"
    if words < 80 and BLOCK_TEXT.search(homepage["text"]):
        return "the site showed a bot-protection page instead of its content"
    if words == 0:  # truly blank (Boots); tiny real pages like badssl.com test sites ("expired. badssl.com") still get scanned
        return "the site showed a blank page to our scanner"
    return ""
