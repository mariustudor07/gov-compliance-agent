"""Severity ranking: ONE place, ONE documented method (docs/ranking.md), applied to every finding.

Severity answers: "if this finding is real, how bad is it?"
  critical  direct breach of the law that affects every visitor, or traffic that can be read or forged
  high      breach of a specific legal requirement, or a real attack path
  medium    weakens compliance or security but is not a breach on its own (a missing safety net)
  low       good practice
Benchmarks: the legal text (UK GDPR, PECR, PSBAR 2018, Equality Act 2010), axe-core's impact rating for
accessibility, and OWASP ZAP's passive-scan risk levels for security headers.

Before this, severities were set in six files with no shared method. Every finding now gets its severity
and a severity_reason from here; Gemini may reword the reason but never changes the severity.
"""
from urllib.parse import urlparse

# Public sector bodies have extra duties (PSBAR 2018: accessibility statement, WCAG 2.2 AA by regulation).
PUBLIC_SECTOR_SUFFIXES = (".gov.uk", ".nhs.uk", ".police.uk", ".ac.uk", ".sch.uk", ".mod.uk", ".parliament.uk",
                          ".gov.scot", ".gov.wales", ".llyw.cymru")

# Cookie domains of well-known tracking / advertising services.
TRACKER_DOMAINS = ("google-analytics", "doubleclick", "googlesyndication", "googleadservices", "facebook",
                   "fbcdn", "hotjar", "clarity.ms", "bing.com", "linkedin", "twitter", "tiktok", "snapchat",
                   "pinterest", "dotmetrics", "scorecardresearch", "quantserve", "adnxs", "criteo", "taboola",
                   "outbrain", "amazon-adsystem", "adsrvr", "rubiconproject", "pubmatic", "casalemedia",
                   "id5-sync", "yahoo", "demdex", "everesttech", "mathtag", "tapad", "bluekai")
TRACKER_NAME_PREFIXES = ("_ga", "_gid", "_gat", "_gcl", "_fbp", "_fbc", "_hj", "_clck", "_clsk", "_uet",
                         "ajs_", "mp_", "_pin", "_tt", "IDE", "test_cookie")

AXE = {"critical": ("critical", "axe-core rates this 'critical': it blocks some disabled users from this content entirely."),
       "high": ("high", "axe-core rates this 'serious': it makes the content very hard to use for some disabled users."),
       "medium": ("medium", "axe-core rates this 'moderate': it causes friction, but users can usually still get through."),
       "low": ("low", "axe-core rates this 'minor'.")}

FIXED = {
    # security: OWASP ZAP passive-scan levels in brackets
    "sec-https": ("critical", "Without HTTPS everything sent to the site, including logins and form data, can be read or changed in transit."),
    "sec-tls-version": ("high", "TLS older than 1.2 has known weaknesses that let attackers read or tamper with traffic."),
    "sec-strict-transport-security": ("medium", "A hardening header: without HSTS a visitor's first request can be downgraded to "
                                                "plain HTTP on hostile networks (OWASP ZAP rates a missing HSTS header Low; GOV.UK requires it)."),
    "sec-content-security-policy": ("medium", "A missing safety net, not a vulnerability: no cross-site scripting (XSS) was found or "
                                              "tested for, but a CSP would limit the damage if one existed (OWASP ZAP: Medium)."),
    "sec-clickjacking": ("medium", "Another site could embed this one in a hidden frame and trick users into clicking (OWASP ZAP: Medium)."),
    "sec-security-txt": ("low", "Good practice recommended by the NCSC: without a published contact, people who "
                                "find a security flaw may not know how to report it safely."),
    "sec-x-content-type-options": ("low", "Blocks a narrow class of browser content-sniffing attacks (OWASP ZAP: Low)."),
    # cookies (PECR reg. 6)
    "ck-policy": ("medium", "PECR requires clear information about every cookie; without a cookie policy visitors can't make an informed choice."),
    "ck-banner-noreject": ("high", "If refusing takes more effort than accepting, consent isn't freely given, so it isn't valid under PECR."),
    "ck-banner-unequal": ("medium", "Nudging visitors towards 'Accept' undermines free choice, which the ICO treats as invalid consent."),
    "ck-banner-preticked": ("high", "Pre-ticked boxes are not consent under UK GDPR: the visitor never actively agreed."),
    # privacy (UK GDPR Art. 13)
    "pv-none": ("critical", "No privacy notice was found at all, so none of the information UK GDPR Article 13 requires is given."),
    "pv-short": ("medium", "We couldn't read a full notice, so we can't confirm the required information is there. If we can't find it, visitors may not either."),
    "a11y-not-run": ("low", "Our automated test couldn't run on these pages, so problems there may be unreported."),
}
CLAUSE_REASON = ("UK GDPR Article 13 requires this information whenever personal data is collected, "
                 "so leaving it out is a direct breach.")


def is_public_sector(url):
    host = (urlparse(url).hostname or "").lower()
    return host.endswith(PUBLIC_SECTOR_SUFFIXES) or host in ("gov.uk", "www.gov.uk")


def _is_known_tracker(item):
    """item: 'name' or 'name (domain)' as written by scanner/cookies.py."""
    name, _, domain = item.partition(" (")
    return name.startswith(TRACKER_NAME_PREFIXES) or any(t in domain for t in TRACKER_DOMAINS)


def rank(finding, site_url):
    """(severity, reason) for one finding. Pass findings stay 'pass'."""
    fid, current = finding["id"], finding["severity"]
    if current == "pass":
        return "pass", ""
    public = is_public_sector(site_url)

    if fid in FIXED:
        return FIXED[fid]
    if fid == "sec-certificate":  # invalid certificate vs one that's merely expiring soon
        return (("critical", "The certificate isn't valid, so browsers warn visitors away and connections can't be trusted.")
                if current == "critical" else
                ("medium", "The certificate is still valid but expires soon; once it does, browsers will block the site."))
    if fid == "sec-mixed-content":
        return (("high", "Scripts, styles or frames loaded over http:// can be replaced by an attacker, undermining HTTPS.")
                if current in ("critical", "high") else
                ("medium", "Images or media loaded over http:// can be read or swapped by an attacker on the network."))
    if fid == "ck-preconsent":
        items = [i.strip() for i in finding.get("evidence", "").split(",") if i.strip()]
        known = [i for i in items if _is_known_tracker(i)]
        if known:
            return "critical", (f"Known tracking cookies ({', '.join(known[:3])}) are set before the visitor can say no: "
                                "a direct breach of PECR reg. 6 for every visitor.")
        return "high", ("Third-party cookies are set before consent. We don't recognise them as trackers, so check "
                        "whether they're strictly necessary; if not, this breaches PECR reg. 6.")
    if fid == "ck-banner":
        return (("high", "There is no way to refuse cookies, so consent isn't freely given and isn't valid under PECR.")
                if current in ("critical", "high") else
                ("medium", "Rejecting is hidden behind settings while accepting is one click, which the ICO says isn't a free choice."))
    if fid == "a11y-statement":
        if public:
            return "high", "Public sector websites must publish an accessibility statement (PSBAR 2018, reg. 8)."
        return "low", ("Only public sector bodies are legally required to publish an accessibility statement; "
                       "for other sites it's good practice.")
    if fid.startswith("a11y-"):
        return AXE.get(current, (current, ""))
    if fid.startswith("pv-"):
        return "high", CLAUSE_REASON
    return current, finding.get("severity_reason", "")


def rank_all(findings, site_url):
    """Sets severity + severity_reason on every finding (and the right regulation for private sites)."""
    public = is_public_sector(site_url)
    for f in findings:
        f["severity"], reason = rank(f, site_url)
        if reason:
            f["severity_reason"] = reason
        if f["id"].startswith("a11y-") and f["id"] not in ("a11y-statement", "a11y-not-run", "a11y-axe") and not public:
            # WCAG is only required by regulation for the public sector; for others the duty comes from the Equality Act
            f["regulation"] = "Equality Act 2010, s.20 (duty to make adjustments; WCAG 2.2 AA as the benchmark)"
    return findings
