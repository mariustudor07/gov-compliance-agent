"""Built-in regulation + fix for every finding type the scanner produces.

Fills every report even when Gemini is unavailable. When Gemini is configured it rewrites
these into site-specific advice, but the report never depends on it.
"""

# finding id -> (regulation, fix)
FIXES = {
    "ck-preconsent": ("PECR reg. 6",
                      "Don't load analytics or advertising scripts until the user clicks Accept. Use a consent "
                      "manager that blocks these tags by default, and set only strictly necessary cookies on first load."),
    "ck-banner-noreject": ("PECR reg. 6; ICO guidance on cookies",
                           "Add a 'Reject all' button next to 'Accept all' on the first screen of the banner."),
    "ck-banner-unequal": ("PECR reg. 6; ICO guidance on cookies",
                          "Make 'Reject all' the same size, colour weight and position as 'Accept all'."),
    "ck-banner-preticked": ("PECR reg. 6; UK GDPR Art. 4(11) (consent must be an active choice)",
                            "Untick all non-essential cookie categories by default."),
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
    "pv-short": ("UK GDPR Art. 12-13",
                 "Make sure the full privacy notice is a normal web page (not a PDF or behind a script) and is "
                 "linked clearly from every page, e.g. 'Privacy notice' in the footer."),
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


# Why each finding got its severity (shown in the report as "Why critical/high/...").
SEVERITY_REASONS = {
    "ck-preconsent": "Tracking starts before the visitor can say no, so PECR consent is never actually given.",
    "ck-banner": "Consent only counts if refusing is as easy as accepting; otherwise PECR consent isn't valid.",
    "ck-policy": "PECR requires clear information about every cookie; without a cookie policy visitors can't "
                 "make an informed choice.",
    "a11y-statement": "Public sector websites are legally required to publish an accessibility statement "
                      "(2018 Regulations, reg. 8).",
    "a11y-not-run": "We couldn't test these pages automatically, so problems there may be unreported.",
    "sec-certificate": "Browsers warn visitors away from sites with invalid or expiring certificates, and "
                       "connections can't be trusted.",
    "sec-tls-version": "Old TLS versions have known weaknesses that let attackers read or tamper with traffic.",
    "sec-mixed-content": "Anything loaded over http:// can be read or replaced by an attacker on the network, "
                         "undermining the page's HTTPS.",
    "ck-banner-noreject": "If refusing takes more effort than accepting, consent isn't freely given, so it isn't valid.",
    "ck-banner-unequal": "Nudging people towards 'Accept' with design undermines free choice, which the ICO "
                         "treats as invalid consent.",
    "ck-banner-preticked": "Pre-ticked boxes are not consent under UK GDPR; the user never actively agreed.",
    "sec-https": "Everything sent to the site, including logins and form data, can be read or changed in transit.",
    "sec-strict-transport-security": "Without HSTS, an attacker on the same network can downgrade a visitor's first "
                                     "request to unencrypted HTTP.",
    "sec-content-security-policy": "CSP is a second line of defence against injected scripts (XSS). Strongly "
                                   "recommended, but not a legal requirement on its own.",
    "sec-x-content-type-options": "It only blocks a narrow class of browser content-sniffing attacks.",
    "sec-clickjacking": "Another site could embed this one invisibly and trick users into clicking its buttons.",
    "pv-short": "We couldn't read a full notice, so we can't confirm the required information is there. "
                "If we can't find it, visitors may not either.",
    "pv-none": "UK GDPR requires this information whenever personal data is collected; without a notice, "
               "nothing else can be checked.",
}
CLAUSE_REASON = ("UK GDPR Article 13 lists this as information people must be given when their data is "
                 "collected, so leaving it out is a direct breach.")
AXE_REASONS = {
    "color-contrast": "Low-contrast text is hard to read for people with low vision or colour blindness, "
                      "and for anyone in bright light.",
    "button-name": "Screen readers announce this as just 'button', so blind users can't tell what it does.",
    "image-alt": "Screen-reader users get no description of the image, or hear the file name read out.",
    "link-name": "Screen-reader users can't tell where the link goes.",
    "label": "Screen-reader users can't tell what to type into the field.",
    "html-has-lang": "Screen readers may read the page in the wrong language and accent.",
}
AXE_SEVERITY_REASONS = {
    "critical": "It blocks some disabled users from using this part of the site at all.",
    "high": "It makes this content very hard to use for some disabled users.",
    "medium": "It causes friction for some users, but they can usually still complete the task.",
    "low": "The impact on users is minor.",
}


# Rolef's accessibility findings that are not axe rules: keep their own (more specific) regulation.
NON_AXE_IDS = {"a11y-statement", "a11y-not-run", "a11y-axe"}


def apply_fixes(findings):
    """Fill in regulation, fix and severity_reason for every non-pass finding that doesn't have them yet."""
    for f in findings:
        if f["severity"] == "pass":
            continue
        if f["id"].startswith("a11y-") and f["id"] not in NON_AXE_IDS:
            rule = f["id"][len("a11y-"):].rsplit("-", 1)[0]
            regulation = "WCAG 2.2 AA (Public Sector Bodies Accessibility Regulations 2018)"
            fix = AXE_FIXES.get(rule, "Fix the elements listed in the evidence so they meet WCAG 2.2 AA.")
            reason = AXE_REASONS.get(rule) or AXE_SEVERITY_REASONS.get(f["severity"], "")
        else:
            regulation, fix = FIXES.get(f["id"], ("", ""))
            reason = SEVERITY_REASONS.get(f["id"]) or (CLAUSE_REASON if f["id"].startswith("pv-") else "")
        f["regulation"] = regulation or f["regulation"]  # the library's citation is more specific
        f["fix"] = f["fix"] or fix
        f["severity_reason"] = f.get("severity_reason") or reason
    return findings


def summarise(findings):
    """Plain-English summary used when Gemini is unavailable."""
    problems = [f for f in findings if f["severity"] != "pass"]
    if not problems:
        return "No compliance problems found in the areas we check."
    counts = {s: sum(f["severity"] == s for f in problems) for s in ("critical", "high", "medium", "low")}
    parts = [f"{n} {s}" for s, n in counts.items() if n]
    breakdown = ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]
    areas = sorted({f["category"] for f in problems if f["severity"] in ("critical", "high")})
    issue_word = "issue" if len(problems) == 1 else "issues"
    summary = f"We found {len(problems)} {issue_word}: {breakdown}."
    if areas:
        summary += f" The most serious are in {_join(areas)}, so start there."
    return summary


def _join(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]
