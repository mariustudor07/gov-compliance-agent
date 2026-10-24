# Database: Bogdan's MongoDB Atlas design, connected

Cluster `legalsources`, database **`Audit_AI_Db`**. Connection string goes in `.env` as `MONGODB_URI`
(never in code). Collections: `Projects`, `Code_Scans`, `Findings`, `Audit_Events`, `Legal_Sources`,
`Compliance_Rules`, each with a strict `$jsonSchema` validator (inserts that break the rules are rejected).

## Workflow (from Bogdan's design)
1. **Create project**: ID, creation date, `Project_Status = "unscanned"`, `Src_ID`, `Compliance_Scope` → *created* event
2. **Compliance scope decides what's scanned**: read `Legal_Sources`, then `Compliance_Rules` → *accessed* events
3. **Scan**: create a `Code_Scans` record → *created* event
4. **Findings**: create `Findings` records → *created* events; project → `"scanned"` → *update* event

**Every** read, create or update by the AI agent writes an `Audit_Events` entry (except creating events themselves).

## AI permissions (R read, W write, M modify, D delete)
| Collection | R | W | M | D |
|---|---|---|---|---|
| Audit_Events | yes | yes | no | no |
| Code_Scans | yes | yes | no | no |
| Compliance_Rules | yes | no | no | no |
| Findings | yes | yes | yes | no |
| Legal_Sources | yes | no | no | no |
| Projects | yes | yes | yes | no |

**Recommended (Bogdan):** enforce this in Atlas itself, not just in our code: create a separate database user
for the app with a custom role: `find` on all six; `insert` on Audit_Events, Code_Scans, Findings, Projects;
`update` on Findings and Projects; **no `remove` anywhere**; nothing but `find` on Legal_Sources and
Compliance_Rules. Then even buggy code can't change the law or delete records.

## How website scans map onto the code-scan schema (decided: map, no schema change)
| Field | GovCheck stores |
|---|---|
| `Projects.Repository_URL` | the website address |
| `Code_Scans.Commit_Sha` | the scan timestamp (websites have no commits) |
| `Code_Scans.Files_Scanned` | number of pages crawled |
| `Findings.File_Path` | the page URL the finding is on |
| `Findings.Line_Start` | `null` (allowed) |

## Changes made to the validators (24 Oct, ~20:40)
The collections were empty, so nothing was lost. Original validators: `docs/db_validators_original.json`.
1. `Legal_Sources`: `required` listed `Src_Punlisher`, the property is `Src_Publisher` → required now `Src_Publisher`.
   `required` listed `Src_Version`, the property was `Src_version` → property renamed `Src_Version`.
2. `Compliance_Rules`: `required` listed `Src_ID`, the property was `Source_ID` → property renamed `Src_ID`
   (same name as in Projects and Legal_Sources).
3. `Audit_Events`: `Entity_Type` had no value for legal sources, so "accessed Legal_Sources" events
   (step 2 of the workflow) couldn't be stored → added `"Source"`.

## Not changed (Bogdan's call)
- `Compliance_Rules.Category` uses `lawful_basics`; our model's label is `lawful_basis`.
- Severity casing: `low` in Compliance_Rules vs `Low` in Findings; Entity_Type `finding` vs `Project`/`Scan`.
- Spelling: `archhived`, `Reccomendation`, `Juristiction`, `Environnement`.
- `Audit_Events.Timestamp`, `Code_Scans.Started_At/Finished_At` use BSON `timestamp` (MongoDB-internal);
  `date` is the usual type for "when it happened".

## Before the app can save scans
`Legal_Sources` and `Compliance_Rules` are empty, and the AI may not write to them. **A person** has to fill
them (Bogdan, or an admin script run by hand, never by the app). Every finding needs a `Rule_ID`, so we need
at least one rule per finding type (privacy clauses, cookies, accessibility, security).

## How the app uses it (built 24 Oct)
- `backend/db/seed.py`: **admin script, run by hand** (`python -m db.seed`): fills Legal_Sources (7: UK GDPR,
  DPA 2018, PECR, PSBAR 2018, WCAG 2.2, NCSC TLS guidance, ICO PECR guidance) and Compliance_Rules (18, one per
  kind of finding). Safe to re-run. NCSC/ICO guidance dates aren't verified, so those two are `under review`.
- `backend/db/agent_store.py`: the AI agent's only way into the database. `save_scan()` runs the workflow
  above; every operation goes through the permission table (forbidden ones raise `PermissionError`) and
  writes an Audit_Events entry. Tested: writing the law, changing a rule, deleting, modifying a scan and
  editing the audit log are all refused.
- `POST /scan` saves each result (a database error never breaks the report); `GET /scans` and
  `GET /scans/{id}` feed the History page (website reads, not the agent, so not audited).
- First data: motorlog.app, gov.uk, bbc.co.uk, theguardian.com: 4 projects, 4 scans, 35 findings, 143 events.

## Added 24 Oct, ~21:30
- **Compliance_Rules** gained `Legal_Text` (the current wording, fetched from legislation.gov.uk by the seed),
  `Legal_Text_URLs` and `Legal_Text_Fetched_At`. Extra fields are allowed by the validators; nothing removed.
  A11Y-WCAG now cites PSBAR **reg. 6** (the duty); reg. 3 is only definitions.
- **Legal_Sources** +2: Data (Use and Access) Act 2025 (amended PECR, e.g. Schedule A1) and Equality Act 2010.
  Dates checked on legislation.gov.uk: Royal Assent for Acts, "made" date for regulations.
- **Training_Labels** (new collection, own validator, unique `Label_ID`): our labelled sentences
  (`data/labels.csv`, 765 rows -> 750 unique). Not in the agent's permission table, so the agent can't touch it.
- **Audit_Events.details** now records what the agent did (Bogdan's note): `what`, `reason`, `collection`,
  `agent`, `scan_id`, `website`, plus `query` (reads), `fields_set` (creates) or `changes` from/to (updates).
  Updates that change nothing are neither written nor logged. Events from before this change have the
  older short `details`; audit records are never rewritten.

## Vector Search (24 Oct, ~22:00)
- `python -m db.embed_rules` (admin, by hand): Voyage AI `voyage-3.5` embeddings (1024 dims) of each rule's
  title, requirement, description and legal text, stored in `Compliance_Rules.Embedding`; creates the Atlas
  Vector Search index **`rules_vector`** (cosine) if missing. Re-run after `db.seed` if the legal text changes.
- The Voyage account has no payment method, so it's limited to 3 requests / 10K tokens a minute: the script
  embeds in batches, and a scan embeds all its findings in **one** request (`AgentStore.search_rules_batch`).
- During a scan, every finding gets the closest rules + legal text from Vector Search, and Gemini cites them
  (e.g. "PECR reg. 6(2) and Schedule A1"). Each rule read is an `accessed` audit event with the similarity score.

## Database users (.env)
`MONGODB_HOST`, `MONGODB_APP_USER`/`MONGODB_APP_PASSWORD` (restricted role, used by the app and the agent) and
`MONGODB_ADMIN_USER`/`MONGODB_ADMIN_PASSWORD` (full access, only for `db.seed` / `db.embed_rules`). Passwords
are URL-encoded by `db/client.py`. While the app user is empty, `MONGODB_URI` is used for everything.

## Search indexes (if one gets deleted)
Run `python -m db.search_indexes` (admin, from `backend/`). It recreates any missing index and leaves existing
ones alone: **`rules_vector`** (Vector Search on `Compliance_Rules.Embedding`, 1024 dims, cosine) and
**`findings_text`** (Atlas Search on `Findings`: Explanation, Reccomendation, Evidence.title/text as text;
Rule_ID, Severity as tokens). 24 Oct ~22:30: `rules_vector` had been deleted; recreated, and `findings_text` added.
