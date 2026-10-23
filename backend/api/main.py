import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="GovCheck")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EXAMPLE = Path(__file__).resolve().parents[2] / "docs" / "example_scan.json"


class ScanRequest(BaseModel):
    url: str


@app.post("/scan")
def scan(req: ScanRequest):
    # TODO: scanner.run(req.url) -> agent.analyse(findings) -> db.save_scan(result)
    result = json.loads(EXAMPLE.read_text())
    result["url"] = req.url
    return result


@app.get("/health")
def health():
    return {"ok": True}
