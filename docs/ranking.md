# How GovCheck ranks findings

All severities come from one place, `backend/agent/ranking.py`, applied to every finding after the scan.
Gemini may reword the explanation but never changes a severity.

## Severity = "if this finding is real, how bad is it?"
| Level | Meaning |
|---|---|
| **Critical** | Direct breach of the law affecting every visitor, or traffic that can be read or forged |
| **High** | Breach of a specific legal requirement, or a real attack path |
| **Medium** | Weakens compliance or security, but isn't a breach on its own (a missing safety net) |
| **Low** | Good practice |

Benchmarks: the legal text (UK GDPR, PECR, PSBAR 2018, Equality Act 2010), axe-core's impact rating for
accessibility, OWASP ZAP's passive-scan risk levels for security headers.

## The rules
| Area | Finding | Severity | Why |
|---|---|---|---|
| Cookies | Known tracking cookies before consent | Critical | PECR reg. 6, every visitor |
| | Unrecognised third-party cookies before consent | High | May be essential: check, else PECR breach |
| | No way to reject / pre-ticked boxes | High | Consent not freely given |
| | Reject less prominent or hidden in settings, no cookie policy | Medium | Weakens consent |
| Privacy | No privacy notice at all | Critical | UK GDPR Art. 13 not met (only after Gemini also found none) |
| | A required item missing (controller, retention, ICO...) | High | Direct breach of Art. 13 |
| | Couldn't read a full notice | Medium | Can't confirm |
| Accessibility | axe-core critical / serious / moderate / minor | Critical / High / Medium / Low | axe's own rating, worst page |
| | No accessibility statement, **public sector** | High | PSBAR 2018 reg. 8 |
| | No accessibility statement, other sites | Low | Not legally required for them |
| Security | No HTTPS, invalid certificate | Critical | Traffic readable / forgeable |
| | TLS older than 1.2, active mixed content | High | Real interception risk |
| | No HSTS, no CSP, no clickjacking protection, passive mixed content, certificate expiring | Medium | Missing safety net (ZAP: CSP Medium, X-Frame-Options Medium, HSTS Low) |
| | No X-Content-Type-Options | Low | Narrow attack class (ZAP: Low) |

**Missing security headers are not vulnerabilities.** GovCheck doesn't test for XSS or any attack (that would
be penetration testing and needs the owner's permission). A missing CSP means "if an XSS bug existed, nothing
would limit the damage", so it's Medium, the same as OWASP ZAP.

**Public sector** = `.gov.uk`, `.nhs.uk`, `.police.uk`, `.ac.uk`, `.sch.uk`, `.mod.uk`, `.parliament.uk`, `.gov.scot`,
`.gov.wales`, `.llyw.cymru`. For other sites, accessibility findings cite the Equality Act 2010 s.20 (duty to make
adjustments), with WCAG 2.2 AA as the benchmark.

## Scores
- Each category starts at 100 and loses **40 / 20 / 10 / 3** points per critical / high / medium / low finding (min 0).
- Overall = average of the 4 categories, **capped by the worst finding: 60 with any critical, 80 with any high**.
  A site breaking the law for every visitor shouldn't score 84 because its other areas are fine
  (the same idea as SSL Labs capping a grade for a serious flaw).

## Changes from the first version (24 Oct)
HSTS High → Medium; accessibility statement High → Low for non-public-sector sites; unrecognised third-party
cookies Critical → High (known trackers stay Critical); overall score capped by the worst finding; "no privacy
notice" is only Critical after Gemini also failed to find one via Google; Gemini told never to change a severity
or claim a vulnerability that wasn't found.
