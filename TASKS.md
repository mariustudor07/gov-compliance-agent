# Tasks: Fri 23 -> Sun 25 Oct

Tracks we're entering with one project:
**Agents That Ship** (main), **Google DeepMind / Gemini 4 Argon**, **MongoDB Atlas**.
Read each track's full brief and judging criteria. Each track needs its own submission.

Rule: all parts talk to each other through `docs/scan_result.schema.json`. In the first hour, agree on it, then split up.

## Everyone, first hour
- [ ] Accept the GitHub invite, clone, make your branch (see CONTRIBUTING.md)
- [ ] Agree on the scan result schema (15 min max)
- [ ] Pick 5 test sites: 2 gov.uk pages (should pass), 3 small random sites (should fail)
- [ ] Bogdan: collect the $100 Atlas credit at the MongoDB booth

## AI / ML lead (`backend/agent`, `backend/ml`): Gemini track
- [x] Review the 285 flagged labels (284 reviewed, 40 corrected)
- [ ] **Review the 135 sentences moved into the new categories:** double-click `review.bat`, then retrain.
      Why this matters: see "Why we review labels by hand" in `docs/model_results.md`.
- [x] Our own ML model: privacy-clause classifier, 13 labels, 765 sentences. TF-IDF + sentence embeddings
      + linear SVM: 70% per sentence, ~95% per policy (tested on 233 UK sites). See `docs/model_results.md`.
- [x] Gemini 4 Argon (`gemini-4-argon`): site-specific fixes + summary, cookie banner judged from a
      screenshot, and for sites that block us it reads the privacy notice via Google (our model checks the quotes)
- [x] Score function (0-100 per category + overall), built-in fix library so reports work without Gemini
- [ ] After the checkpoint: every finding cites the regulation text from Atlas Vector Search (needs Bogdan's DB)
- [ ] After the checkpoint: `security.txt` check; port Rolef's sitemap discovery onto the current crawler

## Rolef: scanner (`backend/scanner`)
- [x] Playwright crawler: find the privacy, cookie and accessibility statement pages
- [x] Cookie check: cookies set *before* consent; banner and reject button present
- [x] Accessibility: inject axe-core, map violations to WCAG 2.2 AA
- [x] Security: HTTPS, HSTS, CSP, X-Frame-Options, TLS version, mixed content

## Bogdan: MongoDB Atlas (`backend/db`): MongoDB track (more Atlas features = more points)
- [ ] Atlas cluster; connection string shared privately, never in git
- [ ] Collections: `scans`, `sites`, `labels` (ML training data), `regulations`
- [ ] **Vector Search + Voyage AI / Automated Embedding:** chunk UK GDPR, PECR, WCAG 2.2 and the
      2018 accessibility regulations into `regulations`, embed them, and expose `search_regulations(query)` for the agent (RAG)
- [ ] **Atlas Search / Hybrid Search:** search across past scans ("sites with pre-consent cookies")
- [ ] **Change Streams / Stream Processing:** push live scan progress to the frontend
- [ ] `GET /scans`, `GET /scans/{id}`, `GET /search`; cache: skip the re-scan if the URL was scanned < 1h ago

## Dawan: frontend (`frontend/`)
- [ ] URL input -> live progress (agent steps streaming in) -> report page
- [ ] Scores per category, findings by severity, fix text + regulation quote
- [ ] Scan history + search page (Bogdan's endpoints)
- [ ] Use the mock `docs/example_scan.json` until the backend is ready
- [ ] Make the demo look good: it's the first thing judges see

## Sunday morning, everyone
- [ ] Freeze features at 10:00; bug fixes only after that
- [ ] Record a backup demo video
- [ ] One pitch, with a slide per track: agent does a real job / Gemini / Atlas features used
- [ ] Submit to every track separately before the deadline
