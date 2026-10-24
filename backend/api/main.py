import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from agent.agent import analyse  # noqa: E402
from db import agent_store  # noqa: E402
from db.agent_store import AgentStore  # noqa: E402
from db.client import db_enabled  # noqa: E402

app = FastAPI(title="GovCheck")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXAMPLE = ROOT / "docs" / "example_scan.json"


class ScanRequest(BaseModel):
    url: str


@app.post("/scan")
def scan(req: ScanRequest):
    if os.getenv("MOCK_SCAN") == "1":
        result = json.loads(EXAMPLE.read_text())
        result["url"] = req.url
        return result

    # Bogdan's workflow: project + law in scope first, then the scan, then the scan record and findings.
    store = None
    if db_enabled():
        try:
            store = AgentStore(requested_by="an individual via the website")  # IND -> AI on Bogdan's diagram
            store.begin(req.url)
        except Exception as e:  # the database must never cost the user their report
            print(f"MongoDB unavailable, scanning without saving: {e}")
            store = None
    result = analyse(req.url, store)
    if store:
        try:
            result["id"] = store.finish(result)
        except Exception as e:
            print(f"Could not save scan to MongoDB: {e}")
    return result


@app.get("/scans")
def scans():
    return agent_store.list_scans() if db_enabled() else []


@app.get("/scans/{scan_id}")
def scan_by_id(scan_id: str):
    result = agent_store.get_scan(scan_id) if db_enabled() else None
    if not result:
        raise HTTPException(404, "Scan not found")
    return result


@app.get("/health")
def health():
    return {"ok": True, "mock": os.getenv("MOCK_SCAN") == "1", "db": db_enabled()}
