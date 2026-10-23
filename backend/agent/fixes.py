"""Built-in regulation + fix for every finding type the scanner produces.

Fills every report even when Gemini is unavailable. When Gemini is configured it rewrites
these into site-specific advice, but the report never depends on it.
"""

# finding id -> (regulation, fix)
FIXES = {
    "ck-preconsent": ("PECR reg. 6",
                      "Don't load analytics or advertising scripts until the user clicks Accept. Use a consent "
                      "manager that blocks these tags by default, and set only strictly necessary cookies on first load."),
    "sec-https": ("NCSC guidance: Using TLS to protect data",
                  "Serve the whole site over HTTPS with a valid certificate and redirect all http:// requests to https://."),
    "sec-strict-transport-security": ("NCSC guidance: Using TLS to protect data",
                                      "Add the header: Strict-Transport-Security: max-age=31536000; includeSubDomains"),
    "sec-content-security-policy": ("NCSC guidance: Protecting websites",
                                    "Add a Content-Security-Policy header that only allows scripts from your own domain "
                                    "and trusted sources, e.g. default-src 'self'. Start in Report-Only mode to test it."),
    "sec-x-content-type-options": ("NCSC guidance: Protecting websites",
                                   "Add the header: X-Content-Type-Options: nosniff"),
    "sec-clickjacking": ("NCSC guidance: Protecting websites",
                         "Add Content-Security-Policy: frame-ancestors 'self' (or X-Frame-Options: DENY) so other "
                         "sites can't embed yours in a frame."),
    "pv-none": ("UK GDPR Art. 13",
                "Publish a privacy notice and link to it from every page (usually in the footer)."),
    "pv-controller": ("UK GDPR Art. 13(1)(a)",
                      "State the legal name and address of the organisation (or person) responsible for the data, "
                      "e.g. 'Example Ltd, 1 High Street, London, is the data controller.'"),
    "pv-purpose": ("UK GDPR Art. 13(1)(c)",
                   "List what personal data you collect and what you use each type for."),
    "pv-lawful_basis": ("UK GDPR Art. 6 and 13(1)(c)",
                        "For each purpose, state the lawful basis: consent, contract, legal obligation, vital "
                        "interests, public task or legitimate interests."),
    "pv-rights": ("UK GDPR Art. 13(2)(b) and 15-22",
                  "Explain people's rights to access, correct, delete, restrict, move and object to the use of "
                  "their data, and how to exercise them."),
    "pv-retention": ("UK GDPR Art. 13(2)(a)",
                     "Say how long each type of data is kept, or the criteria used to decide (e.g. '2 years after "
                     "your account is closed')."),
    "pv-contact_dpo": ("UK GDPR Art. 13(1)(a)-(b)",
                       "Give a contact address or email for privacy questions, and your Data Protection Officer's "
                       "details if you have one."),
    "pv-third_parties": ("UK GDPR Art. 13(1)(e)-(f)",
                         "List who data is shared with (e.g. hosting, analytics, payment providers) and whether it is "
                         "transferred outside the UK, with the safeguards used."),
    "pv-complaints_ico": ("UK GDPR Art. 13(2)(d)",
                          "Tell people they can complain to the Information Commissioner's Office (ico.org.uk, 0303 123 1113)."),
}

# axe-core rule id -> fix. Anything not listed gets a generic accessibility fix.
AXE_FIXES = {
    "color-contrast": "Increase the contrast between text and background to at least 4.5:1 (3:1 for large text).",
    "image-alt": "Give every meaningful image an alt attribute describing it; use alt=\"\" for decorative images.",
    "button-name": "Give icon-only buttons an accessible name, e.g. aria-label=\"Open menu\".",
    "link-name": "Make sure every link has text (or an aria-label) that says where it goes.",
    "label": "Connect every form field to a visible <label>.",
    "html-has-lang": "Add the page language to the html tag: <html lang=\"en\">.",
    "document-title": "Give every page a unique, descriptive <title>.",
    "heading-order": "Use headings in order (h1, then h2, then h3) without skipping levels.",
    "region": "Put all page content inside landmarks such as <header>, <nav>, <main> and <footer>.",
    "landmark-one-main": "Wrap the main content of each page in a single <main> element.",
    "meta-viewport": "Don't disable zooming: remove user-scalable=no and maximum-scale from the viewport meta tag.",
}


def apply_fixes(findings):
    """Fill in regulation and fix for every non-pass finding that doesn't have one yet."""
    for f in findings:
        if f["severity"] == "pass":
            continue
        if f["id"].startswith("a11y-"):
            rule = f["id"][len("a11y-"):].rsplit("-", 1)[0]
            regulation = "WCAG 2.2 AA (Public Sector Bodies Accessibility Regulations 2018)"
            fix = AXE_FIXES.get(rule, "Fix the elements listed in the evidence so they meet WCAG 2.2 AA.")
        else:
            regulation, fix = FIXES.get(f["id"], ("", ""))
        f["regulation"] = regulation or f["regulation"]  # the library's citation is more specific
        f["fix"] = f["fix"] or fix
    return findings


def summarise(findings):
    """Plain-English summary used when Gemini is unavailable."""
    problems = [f for f in findings if f["severity"] != "pass"]
    if not problems:
        return "No compliance problems found in the areas we check."
    counts = {s: sum(f["severity"] == s for f in problems) for s in ("critical", "high", "medium", "low")}
    parts = [f"{n} {s}" for s, n in counts.items() if n]
    worst = sorted(problems, key=lambda f: ["critical", "high", "medium", "low"].index(f["severity"]))[:3]
    return (f"We found {len(problems)} issues ({', '.join(parts)}). "
            f"Fix these first: {'; '.join(f['title'] for f in worst)}.")
