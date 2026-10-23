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

## Why we review labels by hand (don't skip this)

**Status: 285 flagged rows NOT yet reviewed.** Run `python -m ml.review` from `backend/` (≈25 min), then retrain.

1. **The score is only as good as the labels.** The model is graded against `labels.csv`. If the LLM
   pre-labels are wrong, the model learns those mistakes and the score only measures agreement with
   the LLM, not correctness. Reviewing the disputed rows turns guesses into checked labels the score can rest on.
2. **Judges will ask how we got the data.** "An AI labelled it" is weak. "An LLM pre-labelled it, our
   keyword rules flagged the 285 disagreements, and we reviewed every one by hand" is a real
   human-in-the-loop method.
3. **It makes the model ours.** On a CV: "built and labelled a dataset of 765 sentences from UK
   privacy notices; trained a classifier that beats a keyword baseline by 9 points". Only true if we did the labelling.

**Honesty rule:** until the review is done, describe the data as "LLM-labelled, not yet human-reviewed".
`human_checked = True` in `labels.csv` marks exactly which rows a person checked.

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
