# Tasks: Fri 23 -> Sun 25 Oct

Rule: all parts talk to each other through `docs/scan_result.schema.json`. In the first hour, agree on it, then split up.

## Everyone, first hour
- [ ] Accept the GitHub invite, clone, make your branch (see CONTRIBUTING.md)
- [ ] Agree on the scan result schema (15 min max)
- [ ] Pick 5 test sites: 2 gov.uk pages (should pass), 3 small random sites (should fail)

## AI / ML lead (`backend/ml`, `backend/agent`)
- [ ] **Our own ML model (the "from scratch" part):** a classifier for privacy-policy clauses
  - label ~300-500 sentences from real privacy policies as: controller, lawful_basis,
    rights, retention, contact_dpo, third_parties, other (have Gemini pre-label, then correct by hand)
  - baseline: TF-IDF + LogisticRegression (scikit-learn); put precision/recall in `docs/`
  - stretch goal: fine-tune a small model (DistilBERT) and compare it with the baseline
- [ ] Gemini agent: takes the scanner findings and classifier output and writes a plain-English report,
      with severity, fix suggestions and the regulation it cites. Use Flash to keep costs down; cache results per URL.
- [ ] Score function (0-100 per category + overall)
- [ ] Wire up `POST /scan` with Rolef

## Rolef: scanner / security checks (`backend/scanner`)
- [ ] Playwright crawler: load the homepage and up to N internal links; find the privacy, cookie and accessibility pages
- [ ] Cookie check: record cookies *before* clicking anything; detect the banner and its reject button
- [ ] Accessibility: inject axe-core and collect WCAG violations
- [ ] Security headers, TLS and mixed content checks
- [ ] Output findings in the schema format

## Dwan: frontend (`frontend/`)
- [ ] URL input -> loading state -> report page
- [ ] Score per category, findings grouped by severity, "how to fix" text from the agent
- [ ] Scan history page (from Bogdan's endpoints)
- [ ] Use the mock `docs/example_scan.json` until the backend is ready
- [ ] Make the demo look good: it's the first thing judges see

## Bogdan: MongoDB (`backend/db`)
- [ ] MongoDB Atlas free cluster; share the connection string privately (NOT in git)
- [ ] Collections: `scans` (full result), `sites` (url, last score), `labels` (ML training data)
- [ ] Functions: save_scan, get_scan, list_scans, save_label
- [ ] `GET /scans` and `GET /scans/{id}` endpoints
- [ ] Index on url + created_at; cache: skip the re-scan if the same URL was scanned < 1h ago

## Sunday morning, everyone
- [ ] Freeze features at 10:00; bug fixes only after that
- [ ] Record a backup demo video in case the wifi dies
- [ ] Pitch: the problem (public-sector sites are legally required to comply) -> live demo -> our model's metrics -> next steps
