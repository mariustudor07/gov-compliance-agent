"""The AI agent's access to Bogdan's database: his workflow, his permission table, and an audit trail.

Workflow (docs/database.md):
  1. find or create the Project for the website          (accessed / created event)
  2. the project's Compliance_Scope decides what's checked: read Legal_Sources, then
     Compliance_Rules in scope                            (accessed event per record)
  3. create the Code_Scans record                         (created event)
  4. create a Findings record per finding                 (created event each)
  5. set the project to "scanned"                         (update event)

Every action goes through _check(), which enforces Bogdan's R/W/M/D table, so the agent can never
delete anything or write to the law. Every read, create and update writes an Audit_Events entry
(creating an audit event is not itself logged, as the design says).

Reads made by the website's History pages (list_scans / get_scan) are not the AI agent, so they
aren't logged.
"""
import itertools
import json
import os
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from bson import Timestamp

from .client import get_db

ACTOR = "govcheck-agent"

# Bogdan's permission table: R read, W write (create), M modify, D delete.
PERMISSIONS = {
    "Audit_Events": "RW",
    "Code_Scans": "RW",
    "Compliance_Rules": "R",
    "Findings": "RWM",
    "Legal_Sources": "R",
    "Projects": "RWM",
}
OPERATION = {"R": "read", "W": "write", "M": "modify", "D": "delete"}
ENTITY_TYPE = {"Projects": "Project", "Code_Scans": "Scan", "Findings": "finding",
               "Compliance_Rules": "Rule", "Legal_Sources": "Source"}
ID_FIELD = {"Projects": "Project_ID", "Code_Scans": "Scan_ID", "Findings": "Finding_ID",
            "Compliance_Rules": "Rule_ID", "Legal_Sources": "Src_ID"}

# Compliance_Scope value -> the rules (by Rule_ID prefix) it brings into a scan.
SCOPE_RULES = {"privacy": "PRIV-", "cookies": "COOK-", "accessibility": "A11Y-", "security": "SEC-"}
DEFAULT_SCOPE = list(SCOPE_RULES)

CLAUSE_RULE = {"controller": "PRIV-CONTROLLER", "purpose": "PRIV-PURPOSE", "lawful_basis": "PRIV-LAWFUL",
               "rights": "PRIV-RIGHTS", "retention": "PRIV-RETENTION", "contact_dpo": "PRIV-CONTACT",
               "third_parties": "PRIV-THIRDPARTIES", "complaints_ico": "PRIV-ICO"}

_tick = itertools.count(1)  # BSON timestamps need an increment to stay unique within one second


def _now_ts():
    return Timestamp(int(time.time()), next(_tick) % 2**31)


def rule_for(finding_id):
    """Which Compliance_Rules record a GovCheck finding is checked against."""
    if finding_id.startswith("pv-"):
        return CLAUSE_RULE.get(finding_id[3:], "PRIV-NOTICE")
    if finding_id == "ck-preconsent":
        return "COOK-PRECONSENT"
    if finding_id.startswith("ck-banner"):
        return "COOK-BANNER"
    if finding_id == "ck-policy":
        return "COOK-POLICY"
    if finding_id == "a11y-statement":
        return "A11Y-STATEMENT"
    if finding_id.startswith("a11y-"):
        return "A11Y-WCAG"
    if finding_id in ("sec-https", "sec-certificate", "sec-tls-version"):
        return "SEC-TLS"
    if finding_id == "sec-strict-transport-security":
        return "SEC-HSTS"
    if finding_id == "sec-mixed-content":
        return "SEC-MIXED"
    if finding_id.startswith("sec-"):
        return "SEC-HEADERS"
    return None


def _agent_description():
    gemini_on = os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")
    return "GovCheck agent: crawler + our clause classifier" + (f" + {os.environ['GEMINI_MODEL']}" if gemini_on else "")


class AgentStore:
    def __init__(self, db=None):
        self.db = db if db is not None else get_db()
        self.context = {}  # scan_id / website for the events of the scan being saved

    # --- permission-checked, audited operations ------------------------------------------------
    def _check(self, collection, op):
        if op not in PERMISSIONS.get(collection, ""):
            raise PermissionError(f"The AI agent may not {OPERATION[op]} {collection} (Bogdan's permission table)")

    def _event(self, event_type, collection, entity_id, what, reason, **extra):
        """'Set details of what the agent did' (Bogdan's note): a plain description, why, and context."""
        self._check("Audit_Events", "W")
        details = {"what": what, "reason": reason, "collection": collection, "agent": _agent_description(),
                   **self.context, **extra}
        self.db.Audit_Events.insert_one({
            "Event_ID": str(uuid.uuid4()), "Event_Type": event_type, "Entity_Type": ENTITY_TYPE[collection],
            "Entity_ID": str(entity_id), "Actor": ACTOR, "Timestamp": _now_ts(), "details": details})

    def find(self, collection, query, why):
        self._check(collection, "R")
        docs = list(self.db[collection].find(query, {"_id": 0}))
        for doc in docs:
            self._event("accessed", collection, doc[ID_FIELD[collection]],
                        f"read {ENTITY_TYPE[collection]} {doc[ID_FIELD[collection]]}", why,
                        query=json.dumps(query, default=str))  # as text: stored keys can't start with "$"
        return docs

    def insert(self, collection, doc, why):
        self._check(collection, "W")
        self.db[collection].insert_one(dict(doc))
        self._event("created", collection, doc[ID_FIELD[collection]],
                    f"created {ENTITY_TYPE[collection]} {doc[ID_FIELD[collection]]}", why, fields_set=sorted(doc))

    def update(self, collection, entity_id, changes, why):
        self._check(collection, "M")
        before = self.db[collection].find_one({ID_FIELD[collection]: entity_id}, {"_id": 0, **{k: 1 for k in changes}})
        if before is not None and all(before.get(k) == v for k, v in changes.items()):
            return  # nothing would change: no write, so no event
        self.db[collection].update_one({ID_FIELD[collection]: entity_id}, {"$set": changes})
        self._event("update", collection, entity_id, f"updated {ENTITY_TYPE[collection]} {entity_id}", why,
                    changes={k: {"from": str((before or {}).get(k)), "to": str(v)} for k, v in changes.items()})

    def delete(self, collection, entity_id):
        self._check(collection, "D")  # nothing allows D, so this always refuses

    # --- the workflow ---------------------------------------------------------------------------
    def save_scan(self, result):
        """Stores one GovCheck result following Bogdan's workflow. Returns the Scan_ID."""
        url = result["url"]
        scan_id = str(uuid.uuid4())
        self.context = {"scan_id": scan_id, "website": url}

        # 1. project
        projects = self.find("Projects", {"Repository_URL": url}, "look up the project for this website")
        if projects:
            project = projects[0]
        else:
            project = {"Project_ID": str(uuid.uuid4()), "Project_Title": urlparse(url).netloc or url,
                       "Repository_URL": url, "Environnement": "production", "Juristiction": "UK",
                       "Src_ID": "UKGDPR", "Compliance_Scope": DEFAULT_SCOPE,
                       "Project_Created": datetime.now(timezone.utc), "Project_Status": "unscanned"}
            self.insert("Projects", project, "new website scanned for the first time")

        # 2. compliance scope -> legal sources -> rules
        sources = self.find("Legal_Sources", {"Juristiction": {"$regex": "UK"}, "Status": {"$ne": "archhived"}},
                            "legal sources relevant to a UK website")
        prefixes = tuple(SCOPE_RULES[s] for s in project["Compliance_Scope"] if s in SCOPE_RULES)
        rules = [r for r in self.find("Compliance_Rules",
                                      {"Status": "Active", "Src_ID": {"$in": [s["Src_ID"] for s in sources]}},
                                      "rules from those sources")
                 if r["Rule_ID"].startswith(prefixes)]
        rule_ids = {r["Rule_ID"] for r in rules}

        # 3. scan
        kept = [f for f in result["findings"] if rule_for(f["id"]) in rule_ids]
        self.insert("Code_Scans", {
            "Scan_ID": scan_id, "Project_ID": project["Project_ID"],
            "Commit_Sha": result["scanned_at"],  # websites have no commits: the scan time identifies the version
            "Status": "completed", "Ruleset_Version": "1.0",
            "Summary": {"url": url, "scanned_at": result["scanned_at"], "scores": result.get("scores", {}),
                        "summary": result.get("summary", ""), "blocked": bool(result.get("blocked")),
                        "pages_crawled": result.get("pages_crawled", []),
                        "findings_out_of_scope": len(result["findings"]) - len(kept)},
            "Files_Scanned": len(result.get("pages_crawled", [])),
            "Started_At": _now_ts(), "Finished_At": _now_ts()}, "scan finished")

        # 4. findings
        for f in kept:
            self.insert("Findings", {
                "Finding_ID": str(uuid.uuid4()), "Scan_ID": scan_id, "Project_ID": project["Project_ID"],
                "Rule_ID": rule_for(f["id"]), "File_Path": f.get("page") or url, "Line_Start": None,
                "Severity": f["severity"].capitalize(), "Status": "Open",
                "Evidence": {"text": f.get("evidence", ""), "finding_key": f["id"], "title": f["title"],
                             "category": f["category"], "regulation": f.get("regulation", "")},
                "Explanation": f.get("severity_reason") or f["title"],
                "Reccomendation": f.get("fix", ""), "Confidence_Score": None,
                "Created_At": datetime.now(timezone.utc)}, f"finding from scan {scan_id}")

        # 5. project scanned
        self.update("Projects", project["Project_ID"], {"Project_Status": "scanned"}, f"scan {scan_id} saved")
        return scan_id


# --- reads for the website (History / report pages): not the AI agent, so not audited -------------
def list_scans(limit=20):
    db = get_db()
    scans = db.Code_Scans.find({}, {"_id": 0}).sort("Started_At", -1).limit(limit)
    return [{"id": s["Scan_ID"], "url": s["Summary"]["url"], "scanned_at": s["Summary"]["scanned_at"],
             "scores": s["Summary"]["scores"]} for s in scans]


def get_scan(scan_id):
    db = get_db()
    scan = db.Code_Scans.find_one({"Scan_ID": scan_id}, {"_id": 0})
    if not scan:
        return None
    summary = scan["Summary"]
    findings = [{"id": f["Evidence"]["finding_key"], "category": f["Evidence"]["category"],
                 "severity": f["Severity"].lower(), "title": f["Evidence"]["title"],
                 "evidence": f["Evidence"]["text"], "page": f["File_Path"],
                 "regulation": f["Evidence"]["regulation"], "fix": f["Reccomendation"],
                 "severity_reason": f["Explanation"]}
                for f in db.Findings.find({"Scan_ID": scan_id}, {"_id": 0})]
    return {"id": scan_id, "url": summary["url"], "scanned_at": summary["scanned_at"],
            "pages_crawled": summary["pages_crawled"], "scores": summary["scores"],
            "summary": summary["summary"], "blocked": summary["blocked"], "findings": findings}
