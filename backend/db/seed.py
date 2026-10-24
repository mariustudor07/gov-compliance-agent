"""ADMIN script, run by a person, never by the app: fills Legal_Sources, Compliance_Rules (with the
real legal text from legislation.gov.uk) and Training_Labels (our labelled sentences).

Bogdan's design says the AI may read the law but never write it, so the law gets into the database
by hand. Safe to run again: each record is replaced by its ID, nothing is duplicated or deleted.
Re-run it after the label review to update Training_Labels.

    cd backend
    python -m db.seed
"""
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .client import get_db  # noqa: E402

TODAY = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _d(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)


# Published_At: Royal Assent for Acts, "made" date for regulations (checked on legislation.gov.uk). For the two guidance pages we
# don't know the original date, so Status is "under review" and Published_At is our review date.
LEGAL_SOURCES = [
    {"Src_ID": "UKGDPR", "Src_Title": "UK General Data Protection Regulation", "Src_Type": "legislation",
     "Juristiction": "UK", "Src_Publisher": "UK Parliament (retained Regulation (EU) 2016/679)",
     "Src_URL": "https://www.legislation.gov.uk/eur/2016/679/contents", "Src_Version": "UK GDPR, as amended",
     "Status": "active", "Published_At": _d(2016, 4, 27), "Reviewed_At": TODAY},
    {"Src_ID": "DPA2018", "Src_Title": "Data Protection Act 2018", "Src_Type": "legislation",
     "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/ukpga/2018/12/contents", "Src_Version": "2018 c. 12, as amended",
     "Status": "active", "Published_At": _d(2018, 5, 23), "Reviewed_At": TODAY},
    {"Src_ID": "PECR", "Src_Title": "Privacy and Electronic Communications (EC Directive) Regulations 2003",
     "Src_Type": "legislation", "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/uksi/2003/2426/contents", "Src_Version": "SI 2003/2426, as amended",
     "Status": "active", "Published_At": _d(2003, 9, 18), "Reviewed_At": TODAY},
    {"Src_ID": "PSBAR2018",
     "Src_Title": "Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018",
     "Src_Type": "legislation", "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/uksi/2018/952/contents", "Src_Version": "SI 2018/952",
     "Status": "active", "Published_At": _d(2018, 8, 29), "Reviewed_At": TODAY},
    {"Src_ID": "DUAA2025", "Src_Title": "Data (Use and Access) Act 2025", "Src_Type": "legislation",
     "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/ukpga/2025/18/contents",
     "Src_Version": "2025 c. 18 (amends UK GDPR, DPA 2018 and PECR, e.g. PECR Schedule A1)",
     "Status": "active", "Published_At": _d(2025, 6, 19), "Reviewed_At": TODAY},
    {"Src_ID": "EQA2010", "Src_Title": "Equality Act 2010", "Src_Type": "legislation",
     "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/ukpga/2010/15/contents",
     "Src_Version": "2010 c. 15 (s.20 duty to make adjustments: applies to private service providers too)",
     "Status": "active", "Published_At": _d(2010, 4, 8), "Reviewed_At": TODAY},
    {"Src_ID": "WCAG22", "Src_Title": "Web Content Accessibility Guidelines (WCAG) 2.2", "Src_Type": "standard",
     "Juristiction": "UK (required by PSBAR 2018 reg. 6); international W3C standard", "Src_Publisher": "W3C",
     "Src_URL": "https://www.w3.org/TR/WCAG22/", "Src_Version": "2.2 W3C Recommendation",
     "Status": "active", "Published_At": _d(2023, 10, 5), "Reviewed_At": TODAY},
    {"Src_ID": "NCSC-TLS", "Src_Title": "Using TLS to protect data", "Src_Type": "guidance",
     "Juristiction": "UK", "Src_Publisher": "National Cyber Security Centre",
     "Src_URL": "https://www.ncsc.gov.uk/guidance/using-tls-to-protect-data",
     "Src_Version": "as read on review date; original publication date not verified",
     "Status": "under review", "Published_At": TODAY, "Reviewed_At": TODAY},
    {"Src_ID": "ICO-PECR", "Src_Title": "Guide to PECR: cookies and similar technologies", "Src_Type": "guidance",
     "Juristiction": "UK", "Src_Publisher": "Information Commissioner's Office",
     "Src_URL": "https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/",
     "Src_Version": "as read on review date; original publication date not verified",
     "Status": "under review", "Published_At": TODAY, "Reviewed_At": TODAY},
]


def _rule(rule_id, title, category, src, requirement, method, severity, description):
    return {"Rule_ID": rule_id, "Rule_Title": title, "Category": category, "Src_ID": src,
            "Requirement": requirement, "Check_Mthd": method, "Severity": severity,
            "Description": description, "Rule_Version": 1.0, "Status": "Active"}


# One rule per kind of finding GovCheck produces (see RULE_FOR_FINDING in db/agent_store.py).
# Category uses Bogdan's enum (accessibility has no category of its own, so it is "other").
COMPLIANCE_RULES = [
    _rule("PRIV-NOTICE", "A privacy notice is published", "other", "UKGDPR", "Art. 12-13", "browser",
          "Critical", "Information about how personal data is used must be provided where it is collected."),
    _rule("PRIV-CONTROLLER", "Notice names the data controller", "controller", "UKGDPR", "Art. 13(1)(a)",
          "ml_classifier", "High", "Identity and contact details of the controller."),
    _rule("PRIV-PURPOSE", "Notice states the purposes of processing", "purpose", "UKGDPR", "Art. 13(1)(c)",
          "ml_classifier", "High", "Why personal data is collected and used."),
    _rule("PRIV-LAWFUL", "Notice states the lawful basis", "lawful_basics", "UKGDPR", "Art. 6, 13(1)(c)",
          "ml_classifier", "High", "Consent, contract, legal obligation, vital interests, public task or legitimate interests."),
    _rule("PRIV-RIGHTS", "Notice explains data subject rights", "rights", "UKGDPR", "Art. 13(2)(b), 15-22",
          "ml_classifier", "High", "Access, rectification, erasure, restriction, portability and objection."),
    _rule("PRIV-RETENTION", "Notice states how long data is kept", "retention", "UKGDPR", "Art. 13(2)(a)",
          "ml_classifier", "High", "Retention period, or the criteria used to decide it."),
    _rule("PRIV-CONTACT", "Notice gives a privacy contact / DPO", "contact_dpo", "UKGDPR", "Art. 13(1)(a)-(b)",
          "ml_classifier", "High", "How to contact the organisation, and its Data Protection Officer if it has one."),
    _rule("PRIV-THIRDPARTIES", "Notice says who data is shared with", "third_parties", "UKGDPR",
          "Art. 13(1)(e)-(f)", "ml_classifier", "High", "Recipients of the data and any transfers outside the UK."),
    _rule("PRIV-ICO", "Notice mentions the right to complain to the ICO", "complaints_ico", "UKGDPR",
          "Art. 13(2)(d)", "ml_classifier", "High", "The right to lodge a complaint with the Information Commissioner."),
    _rule("COOK-PRECONSENT", "No non-essential cookies before consent", "cookies", "PECR", "reg. 6",
          "browser", "Critical", "Tracking and analytics cookies may only be set after the user agrees."),
    _rule("COOK-BANNER", "Rejecting cookies is as easy as accepting", "cookies", "ICO-PECR", "PECR reg. 6",
          "browser+gemini_vision", "High", "A consent banner with a reject option as prominent as accept."),
    _rule("COOK-POLICY", "A cookie policy is published", "cookies", "PECR", "reg. 6(2)", "browser", "Medium",
          "Clear and comprehensive information about every cookie used."),
    _rule("A11Y-WCAG", "Pages meet WCAG 2.2 AA", "other", "PSBAR2018", "reg. 6, WCAG 2.2 AA", "axe-core",
          "High", "Automated WCAG 2.2 A/AA checks on every crawled page."),
    _rule("A11Y-STATEMENT", "An accessibility statement is published", "other", "PSBAR2018", "reg. 8", "browser",
          "High", "Public sector websites must publish an accessibility statement saying how compliant they are."),
    _rule("SEC-TLS", "Site uses valid, modern TLS", "security", "NCSC-TLS", "HTTPS, TLS 1.2+, valid certificate",
          "tls_handshake", "Critical", "All traffic encrypted with a valid certificate."),
    _rule("SEC-HSTS", "HSTS header is set", "security", "NCSC-TLS", "Strict-Transport-Security", "http_headers",
          "High", "Browsers are told to always use HTTPS."),
    _rule("SEC-HEADERS", "Basic security headers are set", "security", "NCSC-TLS",
          "CSP, X-Content-Type-Options, frame-ancestors", "http_headers", "Medium",
          "Protection against script injection, content sniffing and clickjacking."),
    _rule("SEC-MIXED", "No mixed content", "security", "NCSC-TLS", "No http:// resources on https:// pages",
          "html_parse", "High", "Every script, stylesheet, image and frame loaded over HTTPS."),
]


# The exact legal provisions each rule enforces. Their current text is fetched from legislation.gov.uk
# and stored on the rule (Legal_Text), so Gemini can quote the real law and Vector Search has text to embed.
GDPR = "https://www.legislation.gov.uk/eur/2016/679/article/"
PECR6 = ["https://www.legislation.gov.uk/uksi/2003/2426/regulation/6",
         "https://www.legislation.gov.uk/uksi/2003/2426/schedule/A1"]
PROVISIONS = {
    "PRIV-NOTICE": [GDPR + "12", GDPR + "13"],
    "PRIV-CONTROLLER": [GDPR + "13"], "PRIV-PURPOSE": [GDPR + "13"],
    "PRIV-LAWFUL": [GDPR + "6", GDPR + "13"], "PRIV-RIGHTS": [GDPR + "13"],
    "PRIV-RETENTION": [GDPR + "13"], "PRIV-CONTACT": [GDPR + "13"],
    "PRIV-THIRDPARTIES": [GDPR + "13"], "PRIV-ICO": [GDPR + "13"],
    "COOK-PRECONSENT": PECR6, "COOK-BANNER": PECR6, "COOK-POLICY": PECR6,
    "A11Y-WCAG": ["https://www.legislation.gov.uk/uksi/2018/952/regulation/6",
                  "https://www.legislation.gov.uk/uksi/2018/952/regulation/3"],
    "A11Y-STATEMENT": ["https://www.legislation.gov.uk/uksi/2018/952/regulation/8"],
    # NCSC guidance isn't law; the legal hook for basic web security is UK GDPR Article 32.
    "SEC-TLS": [GDPR + "32"], "SEC-HSTS": [GDPR + "32"], "SEC-HEADERS": [GDPR + "32"], "SEC-MIXED": [GDPR + "32"],
}
MAX_LEGAL_TEXT = 12000  # characters stored per rule


def fetch_provision(url, cache={}):
    import re

    import httpx
    from bs4 import BeautifulSoup
    if url not in cache:
        r = httpx.get(url, follow_redirects=True, timeout=30, headers={"User-Agent": "GovCheck-research/0.1"})
        r.raise_for_status()
        body = BeautifulSoup(r.text, "html.parser").select_one("#viewLegContents")
        cache[url] = re.sub(r"\s+", " ", body.get_text(" ", strip=True)) if body else ""
    return cache[url]


def add_legal_text(rule):
    urls = PROVISIONS.get(rule["Rule_ID"], [])
    texts = [fetch_provision(u) for u in urls]
    rule["Legal_Text"] = "\n\n".join(t for t in texts if t)[:MAX_LEGAL_TEXT]
    rule["Legal_Text_URLs"] = urls
    rule["Legal_Text_Fetched_At"] = datetime.now(timezone.utc)
    return rule


# --- Training_Labels: our labelled sentences (data/labels.csv). Not in the AI agent's permission table,
# so the agent can't touch it; it's for people training the model.
LABELS = ["controller", "purpose", "lawful_basis", "rights", "retention", "contact_dpo", "third_parties",
          "complaints_ico", "data_collected", "cookies", "security", "automated_decisions", "other"]
TRAINING_VALIDATOR = {"$jsonSchema": {
    "title": "Training_Labels", "bsonType": "object",
    "required": ["Label_ID", "Sentence", "Label", "Human_Checked", "Source_URL", "Imported_At"],
    "properties": {
        "Label_ID": {"bsonType": "string"}, "Sentence": {"bsonType": "string"},
        "Label": {"enum": LABELS}, "Second_Opinion": {"bsonType": "string"},
        "Human_Checked": {"bsonType": "bool"}, "Needs_Review": {"bsonType": "bool"},
        "Also": {"bsonType": "string"}, "Source_URL": {"bsonType": "string"}, "Imported_At": {"bsonType": "date"}}}}


def import_labels(db):
    import csv
    import hashlib
    if "Training_Labels" not in db.list_collection_names():
        db.create_collection("Training_Labels", validator=TRAINING_VALIDATOR)
        db.Training_Labels.create_index("Label_ID", unique=True)
        db.Training_Labels.create_index("Label")
    path = Path(__file__).resolve().parents[2] / "data" / "labels.csv"
    now = datetime.now(timezone.utc)
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            label_id = hashlib.sha1((row["source"] + "|" + row["sentence"]).encode()).hexdigest()[:16]
            db.Training_Labels.replace_one({"Label_ID": label_id}, {
                "Label_ID": label_id, "Sentence": row["sentence"], "Label": row["label"],
                "Second_Opinion": row.get("second_opinion", ""), "Human_Checked": row.get("human_checked") == "True",
                "Needs_Review": row.get("needs_review") == "True", "Also": row.get("also", ""),
                "Source_URL": row["source"], "Imported_At": now}, upsert=True)


def main():
    db = get_db("admin")  # the AI agent may not write the law: this runs as the admin user
    for src in LEGAL_SOURCES:
        db.Legal_Sources.replace_one({"Src_ID": src["Src_ID"]}, src, upsert=True)
    for rule in COMPLIANCE_RULES:
        new = add_legal_text(dict(rule))
        # keep the Voyage embedding from db.embed_rules (re-run that script if the legal text changed)
        old = db.Compliance_Rules.find_one({"Rule_ID": rule["Rule_ID"]}, {"_id": 0, "Embedding": 1, "Embedding_Model": 1})
        new.update(old or {})
        db.Compliance_Rules.replace_one({"Rule_ID": rule["Rule_ID"]}, new, upsert=True)
    import_labels(db)
    with_text = db.Compliance_Rules.count_documents({"Legal_Text": {"$ne": ""}})
    print(f"Legal_Sources: {db.Legal_Sources.count_documents({})} | "
          f"Compliance_Rules: {db.Compliance_Rules.count_documents({})} ({with_text} with legal text) | "
          f"Training_Labels: {db.Training_Labels.count_documents({})}")


if __name__ == "__main__":
    main()
