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


def check_accessibility(crawl_result):
    findings = []
    for page in crawl_result["pages"]:
        for v in page["axe_violations"]:
            findings.append(finding(
                f"a11y-{v['id']}-{len(findings)}", "accessibility",
                SEVERITY.get(v.get("impact"), "medium"),
                f"{v['help']} ({len(v['nodes'])} element(s))",
                evidence=v["nodes"][0]["html"][:200] if v["nodes"] else "",
                page=page["url"], regulation="WCAG 2.2 AA"))

    # TODO(Rolef): merge the same violation across pages so the report isn't repetitive
    # TODO(Rolef): finding if no page looks like an accessibility statement
    #   (required by the Public Sector Bodies Accessibility Regulations 2018)

    return findings
