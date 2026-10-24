"""ADMIN script, run by a person, never by the app: fills Legal_Sources and Compliance_Rules.

Bogdan's design says the AI may read the law but never write it, so the law gets into the database
by hand. Safe to run again: each record is replaced by its ID, nothing is duplicated or deleted.

    cd backend
    python -m db.seed
"""
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TODAY = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _d(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)


# Published_At is the date the law came into force / was published. For the two guidance pages we
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
     "Status": "active", "Published_At": _d(2003, 12, 11), "Reviewed_At": TODAY},
    {"Src_ID": "PSBAR2018",
     "Src_Title": "Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018",
     "Src_Type": "legislation", "Juristiction": "UK", "Src_Publisher": "UK Parliament",
     "Src_URL": "https://www.legislation.gov.uk/uksi/2018/952/contents", "Src_Version": "SI 2018/952",
     "Status": "active", "Published_At": _d(2018, 9, 23), "Reviewed_At": TODAY},
    {"Src_ID": "WCAG22", "Src_Title": "Web Content Accessibility Guidelines (WCAG) 2.2", "Src_Type": "standard",
     "Juristiction": "International (the AA level is required by PSBAR2018)", "Src_Publisher": "W3C",
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
    _rule("A11Y-WCAG", "Pages meet WCAG 2.2 AA", "other", "PSBAR2018", "reg. 3, WCAG 2.2 AA", "axe-core",
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


def main():
    db = MongoClient(os.environ["MONGODB_URI"])[os.getenv("MONGODB_DB", "Audit_AI_Db")]
    for src in LEGAL_SOURCES:
        db.Legal_Sources.replace_one({"Src_ID": src["Src_ID"]}, src, upsert=True)
    for rule in COMPLIANCE_RULES:
        db.Compliance_Rules.replace_one({"Rule_ID": rule["Rule_ID"]}, rule, upsert=True)
    print(f"Legal_Sources: {db.Legal_Sources.count_documents({})} | "
          f"Compliance_Rules: {db.Compliance_Rules.count_documents({})}")


if __name__ == "__main__":
    main()
