# GovCheck: pitch, demo and submissions (Encode London, Sunday)

Repo: https://github.com/mariustudor07/gov-compliance-agent · Tracks: **Agents That Ship**, **Google DeepMind (Gemini 4 Argon)**, **MongoDB Atlas**

## Before going on stage
- Run `start.bat`, then **scan motorlog.app and gov.uk in two tabs beforehand** (a scan takes 30–90 s with Gemini).
- Backup: the recorded demo video, plus History (latest scans are stored in Atlas and open instantly).
- Don't scan live: bbc.co.uk (one known false alarm), tesco.com (~5 min), hub.encodeclub.com (~3 min).

## 3-minute script

**1. The problem (20 s).** UK public-sector websites are legally required to be accessible (the 2018 Accessibility
Regulations), to ask before tracking anyone (PECR) and to tell people how their data is used (UK GDPR). Checking
that by hand takes an auditor hours per site, so most sites are never checked.

**2. What GovCheck does (15 s).** Paste a URL. An AI agent opens the site in a real browser, audits it like an
auditor would, and gives you a score, the evidence, the law each problem breaks, and how to fix it.

**3. Live demo: motorlog.app (60 s).** *"This is my own site."*
- Overall **60**, capped by one **critical** issue: an icon button screen readers can't name.
- Point at **evidence** (the actual HTML) and **"why critical"**.
- The privacy finding: *our own model* read the privacy policy and found it never says who the data controller is.
  That's UK GDPR Article 13(1)(a), quoted from the legislation stored in our database.
- **Improvement plan**: fixing the critical button alone gives +20. **Download PDF**.
- Switch tab: **gov.uk scores 100**.

**4. The AI (40 s).**
- **Our own model** reads privacy policies sentence by sentence: trained on 765 sentences from 20 real UK policies
  that we labelled (413 checked by hand). 70% per sentence against 55% for keyword rules, and **96% of decisions right
  on whole policies it had never seen**. We tested it on **233 UK websites**.
- **Gemini 4 Argon** does three jobs: writes site-specific fixes citing law our database retrieved; judges cookie
  banners from a **screenshot** (is "Reject" as easy as "Accept"?); and when a site blocks us, reads its privacy
  policy **through Google**, while **our model checks every quote it brings back**, so it can't make things up.

**5. MongoDB Atlas (25 s).** Atlas is the core store, designed by Bogdan: strict schema validation, **Voyage AI
embeddings + Vector Search** over the real legal text (fetched from legislation.gov.uk), **Atlas Search** across every
finding, and an **audit log of every action the AI takes**: nearly 1,000 events so far. The AI's permissions are
enforced twice: in our code and by an Atlas custom role. It can read the law but never change it, and nothing can
ever be deleted.

**6. Honest by design (10 s).** Sites that block bots get "couldn't scan", not a fake score; a missing security header
is never called a vulnerability; our accuracy numbers come from policies the model never saw.

**7. Team + close (10 s).** Dawan built the frontend, Rolef the scanner, Bogdan the database design, and [you] the AI.
*"GovCheck: the first pass a regulator would make, in under two minutes."*

## Likely questions
| Question | Answer |
|---|---|
| Where's the agent? | It decides when it's reading the wrong page and goes to Google via Gemini, judges banners visually, looks up the law by meaning, and logs every decision in an audit trail. It doesn't plan the whole crawl. |
| Does 100 mean compliant? | It means the required things are in place on paper. We can't see what happens to data behind the scenes; that needs an audit. GovCheck is the first step. |
| Isn't scanning sites legal risk? | It's passive: it visits public pages like a browser. No attacks, no XSS testing, no brute-forcing. Sites that block bots are reported, not bypassed. |
| Why your own model if you have Gemini? | Fast, free, offline, explainable, and it verifies Gemini's quotes. |
| How accurate? | 70% per sentence (13 categories), ~96% per policy on unseen policies (15 held out; 165 sites sampled). Weakest: "controller" and "ICO complaint" clauses. |
| What happens to data? | Scans are stored in Atlas; no visitor personal data; who requested a scan is recorded anonymously on purpose. |

---

## Submission: Agents That Ship
**GovCheck** audits any UK website for legal compliance (accessibility under the 2018 Accessibility Regulations,
cookie consent under PECR, privacy notices under UK GDPR Article 13, and basic web security) and hands back a scored,
evidence-backed report with the exact law broken and how to fix it, as a web page and a PDF.

It does a real job end to end: a real browser crawls the site and finds its privacy, cookie and accessibility
pages (via links or the sitemap); axe-core, header/TLS checks and a cookie audit collect evidence; our own trained
classifier reads the privacy policy; Gemini 4 Argon judges the cookie banner from a screenshot and writes
site-specific fixes grounded in legal text retrieved from MongoDB; scores follow one documented, benchmarked method.
The agent decides when it's read the wrong page and goes to find the real policy through Google, verifies Gemini's
quotes with its own model, and reports honestly when a site blocks it. Every action is written to an audit log.
Tested on 233 UK websites. Built in a weekend by four cybersecurity and digital forensics students.

## Submission: Google DeepMind (Gemini 4 Argon)
GovCheck uses **Gemini 4 Argon** (`gemini-4-argon`) for three jobs where a rule can't do the work:
1. **Grounded explanations:** for every problem found, MongoDB Vector Search retrieves the matching UK rule and its
   legal text; Argon writes a site-specific fix and cites the law it was given (e.g. "PECR reg. 6(2) and Schedule A1"),
   and is instructed never to cite law it wasn't given or claim an attack that wasn't found.
2. **Vision:** Argon looks at a screenshot of the first visit and judges whether the cookie banner gives a fair
   choice (is "Reject" as prominent as "Accept"? pre-ticked boxes?), which HTML rules can't judge.
3. **Google Search + URL context:** when a site blocks automated browsers (e.g. tesco.com), or we land on a privacy
   hub page, Argon finds and reads the real privacy notice through Google and returns a quote per legal requirement.
   **Our own classifier verifies every quote** before it counts, so hallucinated or off-topic quotes are rejected.
Without Gemini the app still works (built-in fixes); with it, reports become specific to each site.

## Submission: MongoDB Atlas
MongoDB Atlas is GovCheck's core data store, built from a design our team member drew on paper and implemented step
by step:
- **7 collections with strict `$jsonSchema` validation**: Projects, Code_Scans, Findings, Audit_Events,
  Legal_Sources, Compliance_Rules, Training_Labels.
- **Atlas Vector Search + Voyage AI** (`voyage-3.5`, 1024 dims): 19 compliance rules embedded with the **current
  legal text fetched from legislation.gov.uk**; every finding retrieves its matching law by meaning, and Gemini cites it.
- **Atlas Search** (`findings_text`): typo-tolerant search across every website's findings ("cookie polcy" works).
- **Security model enforced by Atlas itself**: the app connects as a restricted user with a custom role mirroring the
  AI permission table: it can read the law but never write it, can't delete anything, and can't see training data.
  Verified by attempting every operation directly against Atlas.
- **Full audit trail**: every read, create and update by the AI is an `Audit_Events` document recording what, why,
  which scan, who requested it and old → new values (~1,000 events so far), following the workflow order:
  project → legal sources → rules → scan → findings → processed.
- Admin-only scripts seed the law and rebuild the search indexes; the AI never writes the law.
