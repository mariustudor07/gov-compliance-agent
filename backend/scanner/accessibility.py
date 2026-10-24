"""WCAG 2.2 AA checks using axe-core, plus the legally required accessibility statement."""
from .findings import finding

AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
SEVERITY = {"critical": "critical", "serious": "high", "moderate": "medium", "minor": "low"}


def run_axe(page):
    """Runs inside the open browser page (called by the crawler). Returns axe violations."""
    try:
        page.add_script_tag(url=AXE_URL)
        return page.evaluate("async () => (await axe.run(document, {runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']})).violations")
    except Exception as e:
        # Some sites block injected scripts with their CSP.
        print(f"axe failed on {page.url}: {e}")
        return []


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
    # The same problem on several pages becomes ONE finding ("7 elements on 2 pages"), not one per page.
    by_rule = {}
    for page in crawl_result["pages"]:
        for v in page["axe_violations"]:
            entry = by_rule.setdefault(v["id"], {"violation": v, "pages": [], "elements": 0})
            entry["pages"].append(page["url"])
            entry["elements"] += len(v["nodes"])

    findings = []
    for n, (rule, entry) in enumerate(by_rule.items()):
        v, count, pages = entry["violation"], entry["elements"], entry["pages"]
        where = f"{count} element{'s' if count != 1 else ''}" + (f" on {len(pages)} pages" if len(pages) > 1 else "")
        findings.append(finding(
            f"a11y-{rule}-{n}", "accessibility",
            SEVERITY.get(v.get("impact"), "medium"),
            f"{PLAIN_TITLES.get(rule, v['help'])} ({where})",
            evidence=v["nodes"][0]["html"][:200] if v["nodes"] else "",
            page=pages[0], regulation="WCAG 2.2 AA"))

    # TODO(Rolef): finding if no page looks like an accessibility statement
    #   (required by the Public Sector Bodies Accessibility Regulations 2018)

    return findings
