# Quality and scope review: Saturday night, before the Sunday 10:00 freeze

## Scope: what we set out to do vs where we are
**Goal (Friday):** paste a URL, GovCheck audits it against UK rules, our own model reads the privacy policy,
the law comes from MongoDB, Gemini explains what's wrong and how to fix it. **Still exactly what we built.**

| Planned (README, Friday) | Status |
|---|---|
| Accessibility: axe-core + accessibility statement | ✅ (Rolef) |
| Cookies: before-consent + reject option | ✅ (Rolef + Gemini screenshot check) |
| Privacy: our own trained classifier | ✅ 70% per sentence, ~96% per policy, tested on 233 sites |
| Security: HTTPS, HSTS, CSP, frame protection, TLS, mixed content | ✅ (Rolef) |
| Gemini 4 Argon | ✅ fixes + summary, cookie-banner vision check, Google fallback for blocked sites |
| MongoDB Atlas as core store | ✅ Bogdan's design: validators, restricted role, audit trail |
| Vector Search + Voyage AI over the law | ✅ Gemini cites the matched legal text |
| Atlas Search | ⚠️ index built, not used by the app yet |
| Frontend: report, history | ✅ + PDF, improvement plan, own compliance pages (Dawan) |
| "Agent decides which pages to inspect" (agent loop with tools) | ⚠️ partial: mostly a fixed pipeline (see risk 3) |
| Saint track | ❌ dropped (Rolef) |
| Change Streams, Hybrid Search, multi-label model | ❌ not done (stretch) |

## What's good
- **Works end to end**, tested at scale: 233 UK homepages, 165 readable, ~95–97% of privacy decisions correct.
- **Honest by design**: blocked sites get "couldn't scan", missing headers aren't called vulnerabilities, the model's
  numbers were tested on policies it never saw, and the evaluation method + its limits are written down.
- **Grounded AI**: our model checks Gemini's quotes; Gemini cites legal text from our database.
- **Security story**: permissions enforced twice (code + Atlas role), every agent action audited, secrets out of git,
  secret scanning on, 27 automated tests for the rules that must not change.
- **One documented ranking method** (docs/ranking.md) benchmarked on the law, axe-core and OWASP ZAP.

## What isn't (risks, most important first)
1. **Speed.** 40–90 s per scan with Gemini; Tesco ~5 min. *Demo: scan before going on stage.*
2. **Known false alarms.** Weakest clauses: `controller`, `complaints_ico`. bbc.co.uk shows "doesn't mention
   the ICO", which is wrong. *Demo motorlog.app and gov.uk; don't scan the BBC live.*
3. **"Agents That Ship" framing.** Judges may ask "where's the agent?". The agentic parts: it decides when a page
   is the wrong one and goes to Google via Gemini, judges banners visually, looks up the law by meaning, and
   writes an audited trail of every decision. Say that clearly; don't claim it plans the whole crawl.
4. **Lots of late changes, thin tests.** Unit tests cover ranking/scoring/permissions only; no automated end-to-end
   test. Freeze at 10:00 and only fix bugs after.
5. **Setup drift on teammates' laptops.** New dependencies this weekend: sentence-transformers, scrapling
   (+ `scrapling install`), jspdf, pytest. `start.bat` now installs frontend packages; backend needs
   `pip install -r requirements.txt` after pulling.
6. **History mixes old and new scoring.** Scans saved before the ranking remake keep their old scores (audit
   records are never rewritten). New scans are correct.
7. **Free-tier limits.** Voyage: 3 requests/min (one per scan, fine for a demo; two scans within a minute lose the
   law lookups, gracefully). Gemini quota has run out once already.
8. **Evaluation truth was judged by an AI** (Claude), and the held-out set is small. A human spot-check is still open.
9. **Public repo**: teammates' personal emails are in old commits (not secrets; history not rewritten).

## Before 10:00 Sunday
1. Everyone: pull, `pip install -r requirements.txt`, `scrapling install`, `start.bat`, scan motorlog.app once.
2. Rehearse with motorlog.app (60 → shows the cap and the improvement plan) and gov.uk (100).
3. Optional, only if time: search box on History using the `findings_text` index (Atlas Search).
4. Freeze. Record a backup demo video.
