# Privacy clause classifier: results

**Task:** read a privacy notice sentence by sentence and say which UK GDPR Article 13 requirement
each sentence covers. GovCheck then reports the requirements that no sentence covers.

## Data
- 765 sentences sampled from 20 real UK privacy notices (7 government/public sector, 3 charities, 10 companies). See `backend/ml/label.py`.
- 9 labels: `controller`, `purpose`, `lawful_basis`, `rights`, `retention`, `contact_dpo`, `third_parties`, `complaints_ico`, `other`.
- Pre-labelled by an LLM. Each sentence also got a second opinion from our keyword rules; the 285 sentences (37%) where they disagree are flagged `needs_review` for human checking.

| Label | Sentences |
|---|---|
| other | 374 |
| purpose | 117 |
| third_parties | 92 |
| lawful_basis | 57 |
| rights | 50 |
| contact_dpo | 22 |
| retention | 22 |
| controller | 22 |
| complaints_ico | 9 |

## Model
TF-IDF on words (1–2 grams) + character patterns (2–5 chars) → linear SVM (class-balanced) with
probability calibration. Trains in seconds, runs offline, costs nothing per scan.

## Results (5-fold cross-validation: every sentence tested once by a model that never saw it)

| | Accuracy | Macro-F1 |
|---|---|---|
| Keyword rules (baseline) | 62.7% | 0.57 |
| Logistic regression, words only | 65.4% | 0.64 |
| **Linear SVM, words + characters (ours)** | **72%** | **0.66** |

Per label (our model):

| Label | Precision | Recall | F1 |
|---|---|---|---|
| contact_dpo | 0.89 | 0.77 | 0.83 |
| other | 0.71 | 0.89 | 0.79 |
| complaints_ico | 0.86 | 0.67 | 0.75 |
| lawful_basis | 0.86 | 0.65 | 0.74 |
| third_parties | 0.69 | 0.62 | 0.65 |
| retention | 0.75 | 0.55 | 0.63 |
| rights | 0.67 | 0.60 | 0.63 |
| purpose | 0.66 | 0.44 | 0.53 |
| controller | 0.60 | 0.27 | 0.38 |

## Limitations and next steps
- Labels are LLM pre-labels; the 285 flagged rows still need human review. Numbers will be updated after review.
- `controller` and `complaints_ico` have very few examples. Next: synthetic training sentences for rare labels (`synthesize.py`), always tested on real sentences only.
- Small dataset: more policies would help most.
