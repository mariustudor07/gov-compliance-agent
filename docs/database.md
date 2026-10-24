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
