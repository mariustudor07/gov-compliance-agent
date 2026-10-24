"""Basic web security checks (NCSC guidance)."""
import re
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx

from bs4 import BeautifulSoup

from .findings import finding

# header -> (severity if missing, title)
REQUIRED_HEADERS = {
    "strict-transport-security": ("high", "No HSTS header"),
    "content-security-policy": ("medium", "No Content-Security-Policy header"),
    "x-content-type-options": ("low", "No X-Content-Type-Options header"),
}
CERT_WARNING_DAYS = 14


def check_security(crawl_result):
    findings = []
    home = crawl_result["pages"][0]
    headers = {k.lower(): v for k, v in home["headers"].items()}

    if not home["url"].startswith("https://"):
        findings.append(finding("sec-https", "security", "critical", "Site is not served over HTTPS",
                                evidence=home["url"], page=home["url"], regulation="NCSC guidance"))
    else:
        findings += _tls_findings(home["url"])

    for header, (severity, title) in REQUIRED_HEADERS.items():
        if header not in headers:
            findings.append(finding(f"sec-{header}", "security", severity, title,
                                    evidence="header missing", page=home["url"], regulation="NCSC guidance"))

    csp = headers.get("content-security-policy", "")
    if "x-frame-options" not in headers and "frame-ancestors" not in csp:
        findings.append(finding("sec-clickjacking", "security", "medium",
                                "No clickjacking protection (X-Frame-Options / frame-ancestors)",
                                evidence="header missing", page=home["url"], regulation="NCSC guidance"))

    findings += _mixed_content(crawl_result["pages"])

    if not findings:
        present = [h for h in list(REQUIRED_HEADERS) + ["x-frame-options"] if h in headers]
        findings.append(finding("sec-pass", "security", "pass", "HTTPS and security headers in place",
                                evidence="headers present: " + ", ".join(present), page=home["url"]))
    findings += _security_txt(home["url"])  # after the pass check: it's a disclosure contact, not a header
    return findings


def _tls_findings(url):
    """Connects directly to port 443 to read the TLS version and certificate."""
    host = urlparse(url).hostname
    port = urlparse(url).port or 443
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                version = tls.version()
                cert = tls.getpeercert()
    except ssl.SSLCertVerificationError as e:
        return [finding("sec-certificate", "security", "critical", "TLS certificate is not valid",
                        evidence=e.verify_message or str(e), page=url, regulation="NCSC guidance",
                        fix="Install a valid certificate for this domain (e.g. free from Let's Encrypt) "
                            "and set it to renew automatically.")]
    except ssl.SSLError as e:
        return [finding("sec-tls-version", "security", "high", "Server does not support TLS 1.2 or newer",
                        evidence=str(e)[:200], page=url, regulation="NCSC guidance: Using TLS to protect data",
                        fix="Enable TLS 1.2 and 1.3 on the server and switch off SSLv3, TLS 1.0 and TLS 1.1.")]
    except OSError as e:
        print(f"TLS check could not connect to {host}: {e}")
        return []

    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), timezone.utc)
    days_left = (expires - datetime.now(timezone.utc)).days
    if days_left < CERT_WARNING_DAYS:
        return [finding("sec-certificate", "security", "medium",
                        f"TLS certificate expires in {days_left} day(s)",
                        evidence=f"{version}, certificate valid until {expires:%Y-%m-%d}", page=url,
                        regulation="NCSC guidance",
                        fix="Renew the certificate now and set it to renew automatically.")]
    return []


def _mixed_content(pages):
    """Scripts, styles, images and frames loaded over http:// on an https:// page."""
    insecure = []
    for page in pages:
        if not page["url"].startswith("https://"):
            continue
        soup = BeautifulSoup(page["html"], "html.parser")
        for el in soup.find_all(["script", "img", "iframe", "audio", "video", "source", "embed", "link"]):
            attr = "href" if el.name == "link" else "src"
            if el.name == "link" and "stylesheet" not in (el.get("rel") or []):
                continue
            src = el.get(attr) or ""
            if src.startswith("http://"):
                insecure.append((page["url"], f"<{el.name}> {src}"))
    if not insecure:
        return []
    active = any(item.startswith(("<script>", "<iframe>", "<link>")) for _, item in insecure)
    return [finding("sec-mixed-content", "security", "high" if active else "medium",
                    f"{len(insecure)} resource(s) loaded over insecure http:// (mixed content)",
                    evidence="; ".join(item for _, item in insecure[:5]), page=insecure[0][0],
                    regulation="NCSC guidance: Using TLS to protect data",
                    fix="Load every script, stylesheet, image and frame over https://, and add "
                        "Content-Security-Policy: upgrade-insecure-requests.")]


def _security_txt(site_url):
    """RFC 9116 security.txt: how to report a vulnerability (recommended by the NCSC). One passive request.
    Checks the content, not just that the address answers: single-page apps return their homepage for any
    address (motorlog.app does), which isn't a security.txt."""
    url = urljoin(site_url, "/.well-known/security.txt")
    try:
        r = httpx.get(url, timeout=8, follow_redirects=True,
                      headers={"User-Agent": "GovCheck compliance scanner"})
    except Exception as e:
        print(f"security.txt check skipped for {site_url}: {e}")
        return []
    text = r.text[:20000] if r.status_code == 200 else ""
    if "<html" in text[:1000].lower() or not re.search(r"(?im)^\s*Contact:\s*\S+", text):
        why = ("the address returns a web page, not a security.txt" if "<html" in text[:1000].lower()
               else f"HTTP {r.status_code}" if r.status_code != 200 else "no Contact: line")
        return [finding("sec-security-txt", "security", "low", "No security.txt (how to report a vulnerability)",
                        evidence=f"{url}: {why}", page=site_url,
                        regulation="NCSC Vulnerability Disclosure Toolkit; RFC 9116",
                        fix="Publish /.well-known/security.txt with a Contact: line (an email address or a form) "
                            "and an Expires: date, e.g. 'Contact: mailto:security@example.com'.")]
    expires = re.search(r"(?im)^\s*Expires:\s*(\S+)", text)
    if expires:
        try:
            when = datetime.fromisoformat(expires.group(1).replace("Z", "+00:00"))
            if when.tzinfo and when < datetime.now(timezone.utc):
                return [finding("sec-security-txt", "security", "low", "security.txt has expired",
                                evidence=f"Expires: {expires.group(1)}", page=site_url,
                                regulation="NCSC Vulnerability Disclosure Toolkit; RFC 9116",
                                fix="Update the Expires: date in /.well-known/security.txt (at most a year ahead).")]
        except ValueError:
            pass
    return []
