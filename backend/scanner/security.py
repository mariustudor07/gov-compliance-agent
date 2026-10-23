"""Basic web security checks (NCSC guidance)."""
from .findings import finding

# header -> (severity if missing, title)
REQUIRED_HEADERS = {
    "strict-transport-security": ("high", "No HSTS header"),
    "content-security-policy": ("medium", "No Content-Security-Policy header"),
    "x-content-type-options": ("low", "No X-Content-Type-Options header"),
}


def check_security(crawl_result):
    findings = []
    home = crawl_result["pages"][0]
    headers = {k.lower(): v for k, v in home["headers"].items()}

    if not home["url"].startswith("https://"):
        findings.append(finding("sec-https", "security", "critical", "Site is not served over HTTPS",
                                evidence=home["url"], page=home["url"], regulation="NCSC guidance"))

    for header, (severity, title) in REQUIRED_HEADERS.items():
        if header not in headers:
            findings.append(finding(f"sec-{header}", "security", severity, title,
                                    evidence="header missing", page=home["url"], regulation="NCSC guidance"))

    csp = headers.get("content-security-policy", "")
    if "x-frame-options" not in headers and "frame-ancestors" not in csp:
        findings.append(finding("sec-clickjacking", "security", "medium",
                                "No clickjacking protection (X-Frame-Options / frame-ancestors)",
                                evidence="header missing", page=home["url"], regulation="NCSC guidance"))

    # TODO(Rolef): mixed content: http:// src= links inside an https page's html
    # TODO(Rolef): TLS version / certificate expiry (Python's ssl module)
    # TODO(Rolef): if nothing failed, add one "pass" finding so the report shows it was checked

    return findings
