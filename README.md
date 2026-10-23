# GovCheck

**An AI agent that checks if a website follows UK government compliance rules, and tells you how to fix it.**

Built at Encode London (23–25 Oct 2026) by a team of four cybersecurity & digital forensics students.

You paste a URL. GovCheck opens the site in a real browser, inspects it like an auditor would,
runs our own trained ML model on its privacy policy, looks up the actual law in MongoDB, and Gemini
writes a report: what's wrong, how bad it is, which regulation it breaks, and how to fix it.

---

## Contents
1. [What we check](#1-what-we-check)
2. [How it works](#2-how-it-works)
3. [Project structure](#3-project-structure)
4. [Who does what](#4-who-does-what)
5. [How the pieces connect](#5-how-the-pieces-connect-the-contracts)
6. [Setup (PyCharm, step by step)](#6-setup-pycharm-step-by-step)
7. [Git: how we work together](#7-git-how-we-work-together)
8. [Timeline](#8-timeline)
9. [Hackathon tracks we are entering](#9-hackathon-tracks-we-are-entering)

---

## 1. What we check

"Government compliant" = the rules a UK website (especially a public-sector one) legally has to follow.

| Category | The rule | In plain English | How we check it |
|---|---|---|---|
| **Accessibility** | Public Sector Bodies Accessibility Regulations 2018 → WCAG 2.2 AA | Disabled people must be able to use the site | axe-core scan of each page + "is there an accessibility statement?" |
| **Cookies** | PECR (Privacy and Electronic Communications Regs) | No tracking cookies until the user says yes | Record cookies set *before* anything is clicked; check banner has a "reject" option |
| **Privacy** | UK GDPR + Data Protection Act 2018 | The privacy policy must say who you are, why you collect data, people's rights, how long you keep it, who to contact | **Our own ML classifier** reads the privacy policy and finds which required parts are missing |
| **Security** | NCSC guidance | Basic web security | HTTPS, HSTS, CSP, X-Frame-Options, X-Content-Type-Options, mixed content |

---

## 2. How it works

```
 ┌──────────────┐  POST /scan {url}   ┌──────────────────────────────────────────────────────┐
 │   Frontend   │ ──────────────────► │  API  (backend/api/main.py, FastAPI)                 │
 │   (Dwan)     │ ◄────────────────── │                                                      │
 └──────────────┘   ScanResult JSON   │  1. db: scanned this URL in the last hour? → return  │
                                      │  2. agent.analyse(url):                              │
                                      │       a. scanner.run_scan(url)        ← Rolef        │
                                      │          opens site in Chromium, runs all checks     │
                                      │       b. ml.missing_clauses(policy)   ← AI lead      │
                                      │          our model reads the privacy policy          │
                                      │       c. Gemini explains every finding ← AI lead     │
                                      │          calls search_regulations()  ← Bogdan        │
                                      │          to quote the real law (Vector Search)       │
                                      │       d. scoring → 0-100 per category                │
                                      │  3. db.save_scan(result)              ← Bogdan       │
                                      └──────────────────────────────────────────────────────┘
                                                              │
                                                     ┌────────▼────────┐
                                                     │  MongoDB Atlas  │
                                                     │  scans, sites,  │
                                                     │  regulations,   │
                                                     │  labels         │
                                                     └─────────────────┘
```

**Everything passes around one JSON shape: the `ScanResult`** (see `docs/scan_result.schema.json`
and a full example in `docs/example_scan.json`). If your code produces or reads that shape correctly,
it will plug into everyone else's.

---

## 3. Project structure

```
gov-compliance-agent/
│
├── README.md                     ← you are here
├── TASKS.md                      ← checklist version of section 4 (tick things off)
├── CONTRIBUTING.md               ← git cheat sheet
├── .env.example                  ← copy to .env and fill in keys (.env is NEVER committed)
├── .gitignore
│
├── docs/
│   ├── scan_result.schema.json   ← THE CONTRACT: the shape of a scan result
│   └── example_scan.json         ← fake result, used by the frontend before the backend works
│
├── data/                         ← datasets (big/raw files are gitignored)
│   ├── labels.csv                ← ML training data: sentence,label        (AI lead)
│   └── regulations/              ← plain-text copies of the laws            (Bogdan)
│
├── backend/                      ← all Python. Open THIS folder's parent in PyCharm.
│   ├── requirements.txt          ← Python packages
│   ├── try_scan.py               ← run a scan from PyCharm without the API (great for testing)
│   │
│   ├── api/                      ── shared, AI lead wires it up
│   │   └── main.py               ← FastAPI app: /scan, /scans, /scans/{id}, /health
│   │
│   ├── scanner/                  ── ROLEF
│   │   ├── scan.py               ← run_scan(url): runs everything below, returns findings
│   │   ├── crawler.py            ← opens the site in Chromium, finds privacy/cookie/a11y pages
│   │   ├── cookies.py            ← PECR checks
│   │   ├── accessibility.py      ← axe-core / WCAG checks
│   │   ├── security.py           ← HTTPS + security header checks
│   │   └── findings.py           ← finding(...) helper so every finding has the same shape
│   │
│   ├── ml/                       ── AI LEAD (our own model)
│   │   ├── label.py              ← builds data/labels.csv (Gemini pre-labels, we correct)
│   │   ├── train.py              ← trains TF-IDF + LogisticRegression, prints accuracy
│   │   └── classify.py           ← missing_clauses(text): which GDPR parts are missing
│   │
│   ├── agent/                    ── AI LEAD (Gemini)
│   │   ├── agent.py              ← analyse(url): the whole pipeline end to end
│   │   ├── prompts.py            ← system prompt for Gemini
│   │   └── scoring.py            ← findings → 0-100 scores
│   │
│   └── db/                       ── BOGDAN
│       ├── client.py             ← get_db(): connects to MongoDB Atlas
│       ├── repository.py         ← save_scan, get_scan, list_scans, find_recent_scan
│       ├── regulations.py        ← search_regulations(query): Atlas Vector Search
│       └── load_regulations.py   ← one-off script: chunk + embed laws into MongoDB
│
└── frontend/                     ── DWAN  (React + Vite, created on day 1)
```

---

## 4. Who does what

Each person **owns** a folder. You can read anyone's code, but only change files you own.
If you need something changed in someone else's file, tell them.

### 🧠 AI / ML lead: `backend/ml/`, `backend/agent/`, `backend/api/`
**Your job: make the "intelligence": our own trained model + the Gemini agent, and glue it all together.**

| # | Task | File | Done when |
|---|---|---|---|
| 1 | Get Gemini working: one test call with the API key | `agent/agent.py` | Gemini replies to "hello" from PyCharm |
| 2 | Collect ~400 sentences from 20–30 real privacy policies | `ml/label.py` | `data/labels.csv` exists |
| 3 | Gemini pre-labels each sentence; **you check & correct them by hand** | `ml/label.py` | labels look right when you skim them |
| 4 | Train the classifier, write down the scores | `ml/train.py` | prints precision/recall; you paste them into `docs/model_results.md` |
| 5 | `missing_clauses(text)` returns which required clauses are missing | `ml/classify.py` | try it on a gov.uk privacy page → few missing |
| 6 | Gemini explains each finding + quotes the law via `search_regulations` | `agent/agent.py`, `agent/prompts.py` | findings have `fix` and `regulation` filled in |
| 7 | Tune scoring so a gov.uk page scores high, a random site scores lower | `agent/scoring.py` | numbers feel fair |
| 8 | Wire the API, turn off mock mode | `api/main.py` | Dwan's frontend shows a real scan |
| 9 | *Stretch:* fine-tune DistilBERT and compare with the baseline | `ml/` | better numbers in `docs/model_results.md` |

The 9 labels the classifier uses: `controller` (who runs the site), `purpose` (why data is collected),
`lawful_basis`, `rights` (access, deletion…), `retention` (how long it's kept), `contact_dpo`,
`third_parties` (who it's shared with), `complaints_ico` (right to complain to the ICO), `other`.

### 🔍 Rolef: scanner + Saint: `backend/scanner/`
**Your job: be the auditor. Open the site and collect hard evidence of what's wrong.**

| # | Task | File | Done when |
|---|---|---|---|
| 1 | Run `try_scan.py https://www.gov.uk`: the crawler basics are already written | `crawler.py` | prints pages it visited |
| 2 | Cookies: flag tracking cookies set before consent (starter code is there) | `cookies.py` | a site with Google Analytics gets a critical finding |
| 3 | Cookies: detect the cookie banner and whether it has a "Reject" button | `cookies.py` | finding when there's no reject option |
| 4 | Accessibility: run axe-core on each page, turn violations into findings | `accessibility.py` | findings list WCAG problems with counts |
| 5 | Accessibility: finding if there's no accessibility statement page | `accessibility.py` | |
| 6 | Security: headers (started), plus mixed content + TLS version | `security.py` | http-only site gets a critical finding |
| 7 | **Saint track:** read the Saint brief; make Saint use GovCheck (e.g. "watch my council's site and message me if it stops being compliant") | new file, e.g. `backend/integrations/saint.py` | a 30-second demo of Saint doing it |

Rule for every finding: **always include `evidence`** (what exactly you saw: cookie names, header
values, element counts). Evidence is what makes this look like a forensics tool and not a guess.

### 🎨 Dwan: frontend: `frontend/`
**Your job: make it usable and make the demo look great. Judges see this first.**

| # | Task | Done when |
|---|---|---|
| 1 | Create the app: `npm create vite@latest frontend -- --template react` (Node is installed) | `npm run dev` shows a page |
| 2 | Home page: a big URL box + "Scan" button | |
| 3 | Loading state while the scan runs (scans take 20–60 s; show steps: "Crawling… Checking cookies… Asking AI…") | |
| 4 | Report page: overall score, 4 category scores, findings grouped by severity with `fix` + `regulation` | works using `docs/example_scan.json` |
| 5 | Connect to the real API (see section 5) | real scans show up |
| 6 | History page: list of past scans from `GET /scans` | |
| 7 | *Stretch:* search page (Bogdan's Atlas Search), PDF export of a report | |

Start with the fake data in `docs/example_scan.json`: you don't need to wait for anyone.
The backend also has a mock mode (`MOCK_SCAN=1` in `.env`) that returns that file from `POST /scan`.

### 🍃 Bogdan: MongoDB Atlas: `backend/db/`
**Your job: store everything, and give the AI a searchable copy of the law. The more Atlas features, the more MongoDB-track points.**

| # | Task | File | Done when |
|---|---|---|---|
| 1 | Get the $100 Atlas credit at the MongoDB booth; create a cluster | | |
| 2 | Put the connection string in your `.env` and share it privately (DM, not git!) | `.env` | `python -c "from db.client import get_db; print(get_db().list_collection_names())"` works |
| 3 | `save_scan`, `get_scan`, `list_scans`, `find_recent_scan` | `repository.py` | already drafted, test them |
| 4 | Index on `url` + `scanned_at` | | |
| 5 | Copy the law text into `data/regulations/*.txt` (UK GDPR Art. 5, 6, 12–22; PECR reg. 6; WCAG 2.2 AA success criteria; Accessibility Regs 2018) | `data/regulations/` | |
| 6 | Chunk + embed them with Voyage AI into `regulations` collection | `load_regulations.py` | collection has documents with `embedding` |
| 7 | Create the **Atlas Vector Search** index, finish `search_regulations` | `regulations.py` | `search_regulations("cookies without consent")` returns PECR reg. 6 |
| 8 | **Atlas Search** index on scans → "find all sites with pre-consent cookies" | `repository.py` + API route | |
| 9 | *Stretch:* Change Streams for live scan progress, Hybrid Search | | |

### 👥 Everyone
- First hour: read this README, set up PyCharm (section 6), make your branch (section 7).
- Every few hours: merge your working code into `main` so others can use it.
- Sunday: help with the pitch and the demo video.

---

## 5. How the pieces connect (the contracts)

**Don't change these function names/shapes without telling the team.**

### A finding (one problem found on the site)
```json
{
  "id": "ck-1",
  "category": "cookies",            // accessibility | cookies | privacy | security
  "severity": "critical",           // critical | high | medium | low | pass
  "title": "Tracking cookies set before consent",
  "evidence": "_ga, _gid set on first page load",
  "page": "https://example.com/",
  "regulation": "PECR reg. 6",      // filled in by the agent
  "fix": "Only load Google Analytics after the user accepts."  // filled in by the agent
}
```

### Python functions
| Owner | Function | Returns |
|---|---|---|
| Rolef | `scanner.scan.run_scan(url)` | `{"pages_crawled": [...], "findings": [...], "privacy_text": "..."}` |
| AI lead | `ml.classify.missing_clauses(text)` | `["retention", "contact_dpo"]`, or `None` if the model isn't trained yet |
| AI lead | `agent.agent.analyse(url)` | a full `ScanResult` dict |
| Bogdan | `db.regulations.search_regulations(query)` | `[{"source": "PECR", "section": "reg. 6", "text": "..."}]` |
| Bogdan | `db.repository.save_scan(result)` | the new scan's id (string) |
| Bogdan | `db.repository.get_scan(id)` / `list_scans()` / `find_recent_scan(url)` | scan dict(s) or `None` |

### HTTP API (for Dwan). Runs at `http://127.0.0.1:8000`; interactive docs at `/docs`
| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/scan` | `{"url": "https://..."}` | `ScanResult` |
| `GET` | `/scans` | | list of recent `ScanResult`s |
| `GET` | `/scans/{id}` | | one `ScanResult` |
| `GET` | `/health` | | `{"ok": true}` |

```js
// frontend example
const res = await fetch("http://127.0.0.1:8000/scan", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ url }),
});
const report = await res.json();
```

---

## 6. Setup (PyCharm, step by step)

Already installed on the AI lead's laptop: Python 3.12, Git, GitHub CLI, Node. Teammates: install
[Python 3.12](https://www.python.org/downloads/) (tick "Add to PATH"), [Git](https://git-scm.com/), and Node if you're on frontend.

1. **Get the code**: in a terminal:
   ```
   git clone https://github.com/mariustudor07/gov-compliance-agent.git
   ```
2. **Open in PyCharm**: File → Open → select the `gov-compliance-agent` folder.
3. **Create the virtual environment**: Settings → Project → Python Interpreter → Add Interpreter →
   Add Local Interpreter → Virtualenv → *New*, location `gov-compliance-agent\backend\.venv`, base Python 3.12 → OK.
4. **Mark `backend` as the source root**: right-click the `backend` folder → Mark Directory as → Sources Root.
   (This makes `from scanner.scan import run_scan` work.)
5. **Install packages**: open PyCharm's Terminal tab (bottom), then:
   ```
   cd backend
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
6. **Secrets**: copy `.env.example` to `.env` (in the project root) and fill in the keys you have.
   Leave `MOCK_SCAN=1` until the real pipeline works.
7. **Try the scanner** (no API needed): open `backend/try_scan.py` → right-click → Run. Edit the
   run configuration to add a URL as a parameter, or it defaults to `https://www.gov.uk`.
8. **Run the API**: in the Terminal:
   ```
   cd backend
   uvicorn api.main:app
   ```
   Open http://127.0.0.1:8000/docs and try `POST /scan`.

---

## 7. Git: how we work together

**`main` must always work.** Nobody commits straight to `main`.

```
# once, at the start
git checkout -b rolef/scanner            # your branch: name/what

# whenever you've got something working (often!)
git add .
git commit -m "cookies: detect tracking cookies before consent"
git push                                  # first time: git push -u origin rolef/scanner

# when it's ready for the team
#   → go to GitHub → "Compare & pull request" → someone glances at it → Merge

# get everyone else's latest work into your branch
git checkout main
git pull
git checkout rolef/scanner
git merge main
```
PyCharm can do all of this from the **Git** menu / the branch name in the bottom-right corner.

Never commit: `.env`, API keys, the Mongo connection string, `.venv/`, `node_modules/`.

---

## 8. Timeline

| When | Goal |
|---|---|
| **Fri afternoon** | Everyone set up. Scanner finds pages + cookies. Frontend shows the fake report. Atlas cluster up. Gemini says hello. |
| **Fri night** | Rest. Backend already scans end to end; classifier trained (72% vs 63% baseline). |
| **Sat daytime** | Label review. Frontend calls the real API. Scans saved in Atlas. Saint brief read. |
| **Sat ~19:00: CHECKPOINT** 🚩 | **Rough but working** demo: URL in → real findings on screen. No polish needed. Show what each person built. |
| **Sat night** | After the checkpoint: Vector Search over the laws, Gemini (if we have a key), Saint, start polishing. Test on 5 sites. |
| **Sun 10:00** | 🧊 **Feature freeze.** Bugs only. Record the backup demo video. Build the pitch. |
| **Sun** | Submit to every track separately. Pitch. |

**Pitch outline (3 min):** the problem (public-sector sites are legally required to comply and many
don't) → live demo on a real site → "our own model" slide with metrics → how we use Gemini, Atlas and Saint → what's next.

---

## 9. Hackathon tracks we are entering

| Track | Why we fit | Owner |
|---|---|---|
| **Agents That Ship** (main) | Does a real job end to end: audit → evidence → report → fixes | everyone |
| **Google DeepMind: Gemini 4 Argon** | Gemini is the agent's brain, calling tools to look up the law | AI lead |
| **MongoDB Atlas** | Atlas is the core store + Vector Search, Atlas Search, Voyage AI embeddings | Bogdan |
| **Saint** | Saint watches sites for the user and reports compliance changes | Rolef |

Read every track's full brief: each one has its own judging criteria and submission form.
