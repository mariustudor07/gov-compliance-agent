"""PECR checks: no non-essential cookies before consent, and the user must be able to say no."""
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .findings import finding

# Cookie name prefixes of common tracking / analytics tools.
TRACKING_PREFIXES = ("_ga", "_gid", "_gat", "_gcl", "_fbp", "_fbc", "_hj", "_clck", "_clsk",
                     "_uet", "ajs_", "mp_", "_pin", "_tt", "IDE", "test_cookie")

# Ids/classes used by common consent tools (OneTrust, Cookiebot, Didomi, Quantcast, TrustArc,
# Osano, Cookie Consent, CookieYes, Termly, GOV.UK) plus generic words.
BANNER_HINTS = ("cookie", "consent", "gdpr", "cmp", "onetrust", "cybotcookiebot", "didomi",
                "qc-cmp", "truste", "osano", "cc-window", "cky-", "termly", "usercentrics")
REJECT_WORDS = re.compile(r"\b(reject|decline|refuse|deny|disagree|no,? thanks|"
                          r"(only|strictly) (necessary|essential)|(necessary|essential)( cookies)? only|"
                          r"don.t (accept|allow))\b", re.I)
SETTINGS_WORDS = re.compile(r"\b(manage|settings|preferences|customi[sz]e|options|choose)\b", re.I)
ACCEPT_WORDS = re.compile(r"\b(accept|agree|allow|got it|ok|okay|i understand)\b", re.I)

# Second-level labels under which the registrable domain has three parts (example.gov.uk).
SECOND_LEVEL = {"co", "gov", "org", "ac", "nhs", "police", "ltd", "plc", "me", "net", "sch", "com"}


def check_cookies(crawl_result):
    homepage = crawl_result["pages"][0]
    tracking = _tracking_cookies(crawl_result["cookies_before_consent"], homepage["url"])
    banner = _find_banner(homepage)

    findings = []
    if tracking:
        findings.append(finding(
            "ck-preconsent", "cookies", "critical",
            f"{len(tracking)} tracking cookie(s) set before consent",
            evidence=", ".join(tracking), page=homepage["url"], regulation="PECR reg. 6"))
    else:
        names = [c["name"] for c in crawl_result["cookies_before_consent"]]
        findings.append(finding(
            "ck-preconsent", "cookies", "pass",
            "No known tracking cookies set before consent",
            evidence=f"{len(names)} cookie(s) on first load: {', '.join(names) or 'none'}",
            page=homepage["url"]))

    findings.append(_banner_finding(banner, tracking, homepage["url"]))
    findings.append(_policy_finding(crawl_result["pages"]))
    return findings


def _tracking_cookies(cookies, site_url):
    """Known tracker names, plus any cookie set by another site's domain (third-party)."""
    host = (urlparse(site_url).hostname or "").lower()
    base = _base_domain(host)
    found = []
    for c in cookies:
        domain = c.get("domain", "").lstrip(".").lower()
        same_site = domain == host or host.endswith("." + domain) or domain == base or domain.endswith("." + base)
        third_party = bool(host) and not same_site
        if c["name"].startswith(TRACKING_PREFIXES) or third_party:
            found.append(f"{c['name']} ({domain})" if third_party else c["name"])
    return found


def _base_domain(host):
    parts = host.lower().split(".")
    if len(parts) >= 3 and parts[-2] in SECOND_LEVEL and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _find_banner(page):
    """Looks for a cookie banner in the page and in its iframes (some consent tools use one).

    Returns None, or {"where": short description, "buttons": [button texts]}.
    """
    sources = [(page["html"], False)] + [(html, True) for html in page.get("frames_html", [])]
    for html, is_frame in sources:
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all(True):
            attrs = " ".join([el.get("id") or "", " ".join(el.get("class") or []),
                              el.get("aria-label") or "", el.get("role") or ""]).lower()
            # A consent tool's iframe is the banner itself, even without telling class names.
            if not (is_frame and el.name == "body") and not any(h in attrs for h in BANNER_HINTS):
                continue
            text = el.get_text(" ", strip=True)
            if len(text) > 3000:
                continue  # a whole-page wrapper (e.g. <body class="cookies-enabled">), not a banner
            buttons = [b.get_text(" ", strip=True) or b.get("value", "") or b.get("aria-label", "")
                       for b in el.find_all(["button", "a", "input"])]
            buttons = [b for b in buttons if b]
            # A real banner mentions cookies and offers at least one choice.
            if "cookie" in text.lower() and any(ACCEPT_WORDS.search(b) or REJECT_WORDS.search(b) for b in buttons):
                where = f"<{el.name} id=\"{el.get('id') or ''}\" class=\"{' '.join(el.get('class') or [])}\">"
                if is_frame:
                    where = "in an iframe " + where
                return {"where": where, "buttons": buttons[:10]}
    return None


def _banner_finding(banner, tracking, url):
    if not banner:
        if tracking:
            return finding("ck-banner", "cookies", "high",
                           "No cookie banner, but tracking cookies are set",
                           evidence=f"no consent banner found; cookies set: {', '.join(tracking)}",
                           page=url, regulation="PECR reg. 6",
                           fix="Add a cookie banner that asks for consent before any non-essential cookies are set, "
                               "with Accept and Reject buttons that are equally easy to use.")
        return finding("ck-banner", "cookies", "pass",
                       "No cookie banner, and no tracking cookies that would need one",
                       evidence="no consent banner found", page=url)

    shown = "; ".join(f'"{b}"' for b in banner["buttons"])
    evidence = f"banner {banner['where']} with buttons: {shown}"
    if any(REJECT_WORDS.search(b) for b in banner["buttons"]):
        return finding("ck-banner", "cookies", "pass",
                       "Cookie banner lets users reject non-essential cookies", evidence=evidence, page=url)
    if any(SETTINGS_WORDS.search(b) for b in banner["buttons"]):
        return finding("ck-banner", "cookies", "medium",
                       "Cookie banner hides the reject option behind settings", evidence=evidence, page=url,
                       regulation="PECR reg. 6 (ICO guidance on cookies)",
                       fix="Put a 'Reject all' button on the first layer of the banner, as prominent as 'Accept all'.")
    return finding("ck-banner", "cookies", "high",
                   "Cookie banner has no way to reject cookies", evidence=evidence, page=url,
                   regulation="PECR reg. 6",
                   fix="Add a 'Reject all' button next to 'Accept', and don't set non-essential cookies "
                       "unless the user accepts.")


def _policy_finding(pages):
    policy = next((p for p in pages if "cookie" in p["url"].lower()), None)
    if policy:
        return finding("ck-policy", "cookies", "pass", "Cookie policy page found",
                       evidence=policy["url"], page=policy["url"])
    return finding("ck-policy", "cookies", "medium", "No cookie policy page found",
                   evidence=f"no linked page with 'cookie' in its URL among {len(pages)} page(s) crawled",
                   page=pages[0]["url"], regulation="PECR reg. 6(2)",
                   fix="Publish a cookie policy listing every cookie, what it does and how long it lasts, "
                       "and link to it from the banner and the footer.")
