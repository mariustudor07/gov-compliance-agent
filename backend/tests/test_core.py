"""Fast checks for the rules that must never silently change. No network, no database, no API keys.

    cd backend
    python -m pytest -q
"""
import pytest

from agent.ranking import is_public_sector, rank
from agent.scoring import score
from db.agent_store import PERMISSIONS, AgentStore, rule_for


def f(fid, severity="high", evidence="", category="security"):
    return {"id": fid, "severity": severity, "evidence": evidence, "category": category}


# --- ranking (docs/ranking.md) ---------------------------------------------------------------
@pytest.mark.parametrize("fid,expected", [
    ("sec-https", "critical"), ("sec-strict-transport-security", "medium"),
    ("sec-content-security-policy", "medium"), ("sec-clickjacking", "medium"),
    ("sec-x-content-type-options", "low"), ("pv-controller", "high"), ("pv-none", "critical"),
])
def test_fixed_severities(fid, expected):
    assert rank(f(fid), "https://example.com")[0] == expected


def test_missing_csp_is_not_called_a_vulnerability():
    reason = rank(f("sec-content-security-policy", "medium"), "https://example.com")[1]
    assert "not a vulnerability" in reason


def test_known_trackers_are_critical_unknown_third_party_high():
    assert rank(f("ck-preconsent", "critical", "_ga, _gid"), "https://x.com")[0] == "critical"
    assert rank(f("ck-preconsent", "critical", "uid (dotmetrics.net)"), "https://x.com")[0] == "critical"
    assert rank(f("ck-preconsent", "critical", "sess (cdn.example.net)"), "https://x.com")[0] == "high"


def test_accessibility_statement_only_required_for_public_sector():
    assert rank(f("a11y-statement"), "https://www.leeds.gov.uk")[0] == "high"
    assert rank(f("a11y-statement"), "https://motorlog.app")[0] == "low"


def test_pass_stays_pass():
    assert rank(f("ck-preconsent", "pass"), "https://x.com")[0] == "pass"


def test_public_sector_detection():
    assert is_public_sector("https://www.gov.uk") and is_public_sector("https://www.uclh.nhs.uk")
    assert not is_public_sector("https://motorlog.app") and not is_public_sector("https://fakegov.uk.example.com")


# --- scoring ---------------------------------------------------------------------------------------
def test_overall_capped_by_worst_finding():
    assert score([f("x", "critical", category="cookies")])["overall"] == 60
    assert score([f("x", "high", category="privacy")])["overall"] == 80
    assert score([f("x", "medium", category="security")])["overall"] == 98
    assert score([])["overall"] == 100


# --- Bogdan's permission table (enforced before the database is touched) ------------------------
class NoDatabase:
    def __getattr__(self, name):
        raise AssertionError("permission check must happen before any database access")


@pytest.mark.parametrize("collection,op", [
    ("Legal_Sources", "W"), ("Legal_Sources", "M"), ("Compliance_Rules", "W"), ("Compliance_Rules", "M"),
    ("Code_Scans", "M"), ("Audit_Events", "M"), ("Training_Labels", "R"),
] + [(c, "D") for c in PERMISSIONS])
def test_forbidden_operations_are_refused(collection, op):
    with pytest.raises(PermissionError):
        AgentStore(db=NoDatabase())._check(collection, op)


def test_every_finding_type_maps_to_a_rule():
    for fid in ["pv-controller", "pv-none", "ck-preconsent", "ck-banner", "ck-banner-noreject", "ck-policy",
                "a11y-statement", "a11y-color-contrast-0", "sec-https", "sec-certificate",
                "sec-strict-transport-security", "sec-mixed-content", "sec-clickjacking"]:
        assert rule_for(fid), fid


# --- Bogdan's "create a Source ID if the source is new" (our reading: link, never create) -------------
def test_unknown_jurisdiction_source_is_pending_not_invented():
    store = AgentStore(db=NoDatabase())
    store.find = lambda collection, query, why: []  # the law isn't in Legal_Sources
    assert store._governing_source("UK") == "PENDING-REVIEW"
    assert store._governing_source("Narnia") == "PENDING-REVIEW"


def test_known_jurisdiction_links_its_main_law():
    store = AgentStore(db=NoDatabase())
    store.find = lambda collection, query, why: [{"Src_ID": query["Src_ID"]}]
    assert store._governing_source("UK") == "UKGDPR"


def test_redirect_to_another_website_is_detected():
    from scanner.scan import _other_site
    assert _other_site("https://encodehub.com", "https://www.hugedomains.com/domain_profile.cfm")  # parked domain
    assert not _other_site("https://gov.uk", "https://www.gov.uk/")
    assert not _other_site("https://hub.encodeclub.com", "https://encodeclub.com/")
    assert not _other_site("https://motorlog.app", "https://motorlog.app/quick-check")


def test_security_txt_rule_and_rank():
    assert rule_for("sec-security-txt") == "SEC-DISCLOSURE"
    assert rank(f("sec-security-txt", "low"), "https://example.com")[0] == "low"
