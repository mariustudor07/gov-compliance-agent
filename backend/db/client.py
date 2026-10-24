import os

from pymongo import MongoClient

_client = None


def db_enabled():
    return bool(os.getenv("MONGODB_URI"))


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ["MONGODB_URI"])
    return _client[os.getenv("MONGODB_DB", "Audit_AI_Db")]  # Bogdan's database
