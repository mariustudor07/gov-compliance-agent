"""WCAG 2.2 AA checks using axe-core, plus the legally required accessibility statement."""
import inspect

from .findings import finding

AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
SEVERITY = {"critical": "critical", "serious": "high", "moderate": "medium", "minor": "low"}
ORDER = ["critical", "high", "medium", "low"]

# The 2018 regulations require the statement to say how compliant the site is.
COMPLIANCE_PHRASES = ("fully compliant", "partially compliant", "not compliant")


def run_axe(page):
    """Runs inside the open browser page (called by the crawler).
    Returns axe violations, or None if axe couldn't run on this page."""
    try:
        page.add_script_tag(url=AXE_URL)
        script = "async () => (await axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']})).violations"
        if "isolated_context" in inspect.signature(page.evaluate).parameters:
            # Scrapling's stealth browser (patchright) runs evaluate() in a hidden world by default,
            # where the axe we just injected into the page isn't visible.
            return page.evaluate(script, isolated_context=False)
        return page.evaluate(script)
    except Exception as e:
        # Some sites block injected scripts with their CSP.
        print(f"axe failed on {page.url}: {e}")
        return None


# Plain-English titles for common axe rules; anything else uses axe's own wording.
PLAIN_TITLES = {
    "color-contrast": "Text with too little colour contrast to read easily",
    "button-name": "Buttons with no label that screen readers can announce",
    "image-alt": "Images with no text description",
    "link-name": "Links with no text saying where they go",
    "label": "Form fields with no label",
    "html-has-lang": "Page doesn't declare its language",
    "document-title": "Page has no title",
    "heading-order": "Headings skip levels",
    "region": "Content outside the page's main landmarks",
    "landmark-one-main": "Page has no main content landmark",
    "meta-viewport": "Zooming is disabled",
}


def check_accessibility(crawl_result):
    pages = crawl_result["pages"]
    findings = _axe_findings(pages)
    findings.append(_statement_finding(pages))
    return findings


def _axe_findings(pages):
    """The same problem on several pages becomes ONE finding ("7 elements on 2 pages"), not one per page."""
    by_rule = {}
    for page in pages:
        for v in page["axe_violations"] or []:
            rule = by_rule.setdefault(v["id"], {"v": v, "pages": [], "elements": 0, "impacts": []})
            rule["pages"].append(page["url"])
            rule["elements"] += len(v["nodes"])
            rule["impacts"].append(SEVERITY.get(v.get("impact"), "medium"))

    findings = []
    for rule_id, rule in by_rule.items():
        v, count = rule["v"], rule["elements"]
        example = v["nodes"][0]["html"][:200] if v["nodes"] else ""
        n_pages = len(rule["pages"])
        where = f"{count} element{'s' if count != 1 else ''}" + (f" on {n_pages} pages" if n_pages > 1 else "")
        findings.append(finding(
            f"a11y-{rule_id}-{len(findings)}", "accessibility",
            min(rule["impacts"], key=ORDER.index),  # the worst impact seen on any page
            f"{PLAIN_TITLES.get(rule_id, v['help'])} ({where})",
            evidence=f"e.g. {example}" + (f" | also on: {', '.join(rule['pages'][1:])}" if n_pages > 1 else ""),
            page=rule["pages"][0], regulation="WCAG 2.2 AA"))

    checked = [p["url"] for p in pages if p["axe_violations"] is not None]
    skipped = [p["url"] for p in pages if p["axe_violations"] is None]
    if skipped:
        findings.append(finding(
            "a11y-not-run", "accessibility", "low",
            f"Automated accessibility test could not run on {len(skipped)} page(s)",
            evidence=", ".join(skipped), page=skipped[0], regulation="WCAG 2.2 AA",
            fix="Test these pages manually or with a browser extension such as axe DevTools."))
    if checked and not by_rule:
        findings.append(finding(
            "a11y-axe", "accessibility", "pass", "No automated WCAG 2.2 AA failures found",
            evidence=f"axe-core checked {len(checked)} page(s)", page=checked[0]))
    return findings


def _statement_finding(pages):
    statement = next((p for p in pages if "accessibility" in p["url"].lower()
                      or "accessibility statement" in p["text"][:2000].lower()), None)
    if not statement:
        return finding(
            "a11y-statement", "accessibility", "high", "No accessibility statement found",
            evidence=f"no linked page with 'accessibility' in its URL or heading among {len(pages)} page(s) crawled",
            page=pages[0]["url"],
            regulation="Public Sector Bodies Accessibility Regulations 2018, reg. 8",
            fix="Publish an accessibility statement using the GOV.UK model statement and link to it from every page.")

    text = statement["text"].lower()
    if not any(p in text for p in COMPLIANCE_PHRASES):
        return finding(
            "a11y-statement", "accessibility", "medium",
            "Accessibility statement doesn't say how compliant the site is",
            evidence=f"none of {', '.join(COMPLIANCE_PHRASES)} found on {statement['url']}",
            page=statement["url"],
            regulation="Public Sector Bodies Accessibility Regulations 2018, reg. 8",
            fix="State whether the site is fully, partially or not compliant with WCAG 2.2 AA, list the known "
                "problems, and say when the statement was last reviewed.")
    return finding("a11y-statement", "accessibility", "pass", "Accessibility statement found",
                   evidence=statement["url"], page=statement["url"])
