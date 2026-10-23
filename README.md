# GovCheck: an AI compliance agent for websites (Encode London 2026)

Give it a URL. It crawls the site, checks it against UK government and public-sector
rules, and an AI agent explains what fails and how to fix it.

## What "compliant" means here (UK scope)
| Area | Law / standard | What we check |
|---|---|---|
| Accessibility | Public Sector Bodies Accessibility Regs 2018 -> WCAG 2.2 AA | axe-core violations, accessibility statement present |
| Cookies | PECR | non-essential cookies set *before* consent, banner has a reject option |
| Privacy | UK GDPR / DPA 2018 | privacy notice exists, names controller, lawful basis, rights, retention, contact/DPO |
| Security | NCSC guidance | HTTPS, HSTS, CSP, X-Frame-Options, TLS version, mixed content |

## Architecture
```
frontend (Dwan) --> api (FastAPI) --> scanner (Rolef)  : Playwright crawl + rule checks
                                  --> ml + agent (AI)  : our trained classifier + Gemini reasoning
                                  --> db (Bogdan)      : MongoDB Atlas, stores scans
```
Everyone shares one contract: `docs/scan_result.schema.json`. Build against that, not against each other's code.
The frontend can use `docs/example_scan.json` as mock data until the backend is ready.

## Run (backend)
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy ..\.env.example ..\.env   # fill in keys
uvicorn api.main:app --reload
```
See `TASKS.md` for who does what and `CONTRIBUTING.md` for the git workflow.
