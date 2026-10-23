"""Saving and loading scans. Scans are stored exactly in the ScanResult shape."""
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from .client import get_db


def _clean(doc):
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


def save_scan(result):
    doc = dict(result)
    doc.pop("id", None)
    inserted = get_db().scans.insert_one(doc)
    get_db().sites.update_one(
        {"url": result["url"]},
        {"$set": {"last_score": result["scores"]["overall"], "last_scanned_at": result["scanned_at"]}},
        upsert=True)
    return str(inserted.inserted_id)


def get_scan(scan_id):
    return _clean(get_db().scans.find_one({"_id": ObjectId(scan_id)}))


def list_scans(limit=20):
    cursor = get_db().scans.find({}, {"findings": 0}).sort("scanned_at", -1).limit(limit)
    return [_clean(d) for d in cursor]


def find_recent_scan(url, max_age_minutes=60):
    """Cache: return a scan of this URL newer than max_age_minutes, or None."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)).isoformat()
    return _clean(get_db().scans.find_one({"url": url, "scanned_at": {"$gte": since}},
                                          sort=[("scanned_at", -1)]))


# TODO(Bogdan): create an index on (url, scanned_at)
# TODO(Bogdan): search_scans(text) using an Atlas Search index on findings.title / summary
