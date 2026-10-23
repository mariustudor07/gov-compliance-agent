"""PECR checks: no non-essential cookies before consent, and the user must be able to say no."""
from .findings import finding

# Cookie name prefixes of common tracking / analytics tools.
TRACKING_PREFIXES = ("_ga", "_gid", "_gat", "_gcl", "_fbp", "_fbc", "_hj", "_clck", "_clsk",
                     "_uet", "ajs_", "mp_", "_pin", "_tt", "IDE", "test_cookie")


def check_cookies(crawl_result):
    findings = []
    homepage = crawl_result["pages"][0]["url"]
    tracking = [c["name"] for c in crawl_result["cookies_before_consent"]
                if c["name"].startswith(TRACKING_PREFIXES)]

    if tracking:
        findings.append(finding(
            "ck-preconsent", "cookies", "critical",
            f"{len(tracking)} tracking cookie(s) set before consent",
            evidence=", ".join(tracking), page=homepage, regulation="PECR reg. 6"))
    else:
        findings.append(finding(
            "ck-preconsent", "cookies", "pass",
            "No known tracking cookies set before consent", page=homepage))

    # TODO(Rolef): detect the cookie banner in crawl_result["pages"][0]["html"]
    #   - look for elements whose id/class/text contains "cookie" or "consent"
    #   - is there a button whose text contains "reject", "decline" or "necessary only"?
    #   - no banner but tracking cookies -> high finding; banner without reject -> high finding
    # TODO(Rolef): check whether a cookie policy page was found among crawl_result["pages"]

    return findings
