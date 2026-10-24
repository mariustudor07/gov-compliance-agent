"""MongoDB connections. Two users, as in Bogdan's design:

- app   (restricted, e.g. govcheck_app): what the API and the AI agent use.
- admin (full access): ONLY for scripts a person runs by hand (db.seed, db.embed_rules).

Set MONGODB_HOST plus MONGODB_APP_USER/PASSWORD and MONGODB_ADMIN_USER/PASSWORD in .env; the address
is built here, with the password safely encoded (special characters like @ : / # are fine).
If those aren't set, the single MONGODB_URI is used for both (the setup before the restricted user existed).
"""
import os
from urllib.parse import quote_plus

from pymongo import MongoClient

_clients = {}


def _uri(role):
    host = os.getenv("MONGODB_HOST")
    user = os.getenv(f"MONGODB_{role.upper()}_USER")
    password = os.getenv(f"MONGODB_{role.upper()}_PASSWORD")
    if host and user and password:
        return f"mongodb+srv://{quote_plus(user)}:{quote_plus(password)}@{host}/?retryWrites=true&w=majority"
    return os.getenv("MONGODB_URI")


def db_enabled():
    return bool(_uri("app"))


def get_db(role="app"):
    if role not in _clients:
        _clients[role] = MongoClient(_uri(role))
    return _clients[role][os.getenv("MONGODB_DB", "Audit_AI_Db")]  # Bogdan's database
