"""Saint track: "watch my council's website and tell me if it stops being compliant".

Saint (a personal AI assistant that works in your email, calendar and browser) runs this on a
schedule. Each run re-scans the site, compares it with the last scan, and prints a short,
email-ready report of what changed. Saint sends that report to the user.

Usage:  python -m integrations.saint https://www.example.gov.uk
        (run from the backend folder; the last scan of each site is kept in data/watch/)

Workflow to give Saint (paste into Saint):
    Every Monday at 9am, run GovCheck's watch on https://www.example.gov.uk.
    If the report starts with "CHANGED" or "NEW", email it to me with the subject
    "GovCheck: <site> compliance changed". If it starts with "NO CHANGE", do nothing.
    If it starts with "COULDN'T SCAN" three weeks in a row, tell me the site needs a manual check.
"""
import json
import re
import sys
from pathlib import Path

from scanner.scan import run_scan

WATCH_DIR = Path(__file__).resolve().parents[2] / "data" / "watch"
ORDER = ["critical", "high", "medium", "low", "pass"]


def watch(url):
    """Scan url, compare with the previous scan of it, save this one. Returns the report text."""
    new = run_scan(url)
    if new["blocked"]:
        # Keep the last real scan: a bot-protection page says nothing about compliance.
        return f"COULDN'T SCAN: {url}: {new['blocked']}. Nothing to compare this time."
    new.pop("homepage_screenshot", None)  # PNG bytes, not JSON, and not needed for the diff
    path = WATCH_DIR / (re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_") + ".json")
    old = json.loads(path.read_text()) if path.exists() else None

    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(new, indent=2))
    return report(url, old, new)


def compare(old, new):
    """Findings that appeared, got worse, got better or were fixed between two scans."""
    before = {_key(f): f for f in old["findings"]}
    after = {_key(f): f for f in new["findings"]}
    changes = {"new": [], "worse": [], "better": [], "fixed": []}
    for id, f in after.items():
        prev = before.get(id)
        if prev is None:
            if f["severity"] != "pass":
                changes["new"].append(f)
        elif ORDER.index(f["severity"]) < ORDER.index(prev["severity"]):
            changes["worse"].append((prev, f))
        elif ORDER.index(f["severity"]) > ORDER.index(prev["severity"]):
            (changes["fixed"] if f["severity"] == "pass" else changes["better"]).append((prev, f))
    for id, prev in before.items():
        if id not in after and prev["severity"] != "pass":
            changes["fixed"].append((prev, None))
    return changes


def _key(f):
    """a11y ids end in a position number (a11y-color-contrast-3) that shifts between scans."""
    return re.sub(r"-\d+$", "", f["id"]) if f["id"].startswith("a11y-") else f["id"]


def report(url, old, new):
    problems = [f for f in new["findings"] if f["severity"] != "pass"]
    problems.sort(key=lambda f: ORDER.index(f["severity"]))
    if old is None:
        lines = [f"NEW: first GovCheck scan of {url}: {len(problems)} problem(s) found."]
        lines += [f"  [{f['severity']}] {f['title']}: {f['evidence']}" for f in problems[:10]]
        return "\n".join(lines)

    c = compare(old, new)
    if not any(c.values()):
        return f"NO CHANGE: {url} still has the same {len(problems)} problem(s)."

    lines = [f"CHANGED: {url} compliance has changed since the last scan."]
    for f in c["new"]:
        lines.append(f"  NEW [{f['severity']}] {f['title']}: {f['evidence']}")
    for prev, f in c["worse"]:
        lines.append(f"  WORSE [{prev['severity']} -> {f['severity']}] {f['title']}: {f['evidence']}")
    for prev, f in c["better"]:
        lines.append(f"  BETTER [{prev['severity']} -> {f['severity']}] {f['title']}")
    for prev, f in c["fixed"]:
        lines.append(f"  FIXED {prev['title']}")
    lines.append(f"{len(problems)} problem(s) remain in total.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(watch(sys.argv[1] if len(sys.argv) > 1 else "https://www.gov.uk"))
