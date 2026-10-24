# Privacy clause classifier: results

**Task:** read a privacy notice sentence by sentence and say what each sentence covers. GovCheck
then reports the UK GDPR Article 13 requirements that no sentence covers.

## Data
- 765 sentences sampled from 20 real UK privacy notices (7 government/public sector, 3 charities, 10 companies). See `backend/ml/label.py`.
- 13 labels. The 8 that GovCheck checks for (`REQUIRED` in `ml/classify.py`): `controller`, `purpose`,
  `lawful_basis`, `rights`, `retention`, `contact_dpo`, `third_parties`, `complaints_ico`.
  Plus 4 we split out of `other` after reviewing it (our idea: `other` was a big mixed pile the model
  couldn't learn from): `data_collected`, `cookies`, `security`, `automated_decisions`. And `other`.

| Label | Sentences | | Label | Sentences |
|---|---|---|---|---|
| other | 201 | | cookies | 39 |
| purpose | 139 | | contact_dpo | 22 |
| third_parties | 96 | | retention | 22 |
| data_collected | 74 | | controller | 22 |
| lawful_basis | 65 | | security | 17 |
| rights | 52 | | complaints_ico | 11 |
| | | | automated_decisions | 5 |

### How the labels were made (human-in-the-loop)
1. An LLM pre-labelled every sentence.
2. Our keyword rules gave a second opinion; the 285 sentences where they disagreed were flagged.
3. **We reviewed all 284 of the flagged sentences by hand and corrected 40.**
4. Reviewing showed `other` was too broad, so we added 4 categories and moved 135 sentences into them.
   **Status: those 135 moved sentences still need a human check** (`python -m ml.review`).

**Honesty rule:** describe the data as "LLM-pre-labelled, disagreements reviewed by hand".
`human_checked = True` in `labels.csv` marks exactly which rows a person checked.

## Why we review labels by hand (don't skip this)
1. **The score is only as good as the labels.** The model is graded against `labels.csv`. If the LLM
   pre-labels are wrong, the model learns those mistakes and the score only measures agreement with
   the LLM, not correctness.
2. **Judges will ask how we got the data.** "An AI labelled it" is weak. "An LLM pre-labelled it, our
   keyword rules flagged the disagreements, and we reviewed every one by hand" is a real method.
3. **It makes the model ours.** Only true on a CV if we did the labelling.

## Model
Three kinds of features → linear SVM (class-balanced, C=0.5) → probability calibration:
- TF-IDF on words (1–3 word phrases)
- TF-IDF on character patterns (2–5 characters; catches "retain / retention / retained")
- Sentence embeddings from a small pretrained model (`BAAI/bge-base-en-v1.5`): captures meaning,
  so "how long we keep your data" and "retention period" look similar despite sharing no words.

The pretrained model only turns sentences into numbers; **the classifier on top is trained on our
labelled data** (transfer learning). Runs offline, costs nothing per scan.

## Results (5-fold cross-validation: every sentence tested once by a model that never saw it)

13 labels, after human review:

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Keyword rules (baseline) | 55% | 0.58 |
| TF-IDF + linear SVM (our first model) | 63–64% | 0.61 |
| **TF-IDF + sentence embeddings + linear SVM (ours)** | **70%** | **0.69** |

Embedding model and settings were chosen by cross-validation: all-MiniLM-L6 (69%), bge-small (69–70%),
bge-base (70–71%); embedding weight 2 and C=0.5 were best.

Per label (our model):

| Label | Precision | Recall | F1 |
|---|---|---|---|
| retention | 0.91 | 0.91 | 0.91 |
| cookies | 0.88 | 0.77 | 0.82 |
| security | 0.92 | 0.71 | 0.80 |
| contact_dpo | 0.77 | 0.77 | 0.77 |
| complaints_ico | 0.80 | 0.73 | 0.76 |
| third_parties | 0.77 | 0.76 | 0.76 |
| lawful_basis | 0.78 | 0.66 | 0.72 |
| data_collected | 0.72 | 0.65 | 0.68 |
| rights | 0.76 | 0.62 | 0.68 |
| other | 0.61 | 0.78 | 0.68 |
| purpose | 0.64 | 0.63 | 0.64 |
| controller | 0.78 | 0.32 | 0.45 |
| automated_decisions | 0.50 | 0.20 | 0.29 |

## Document-level results: what the app actually decides

The app doesn't need every sentence right. It needs to know, for a whole policy, whether each of the 8
required clauses appears at least once. `python -m ml.evaluate_documents` measures that fairly:
for each of the 20 policies, the model is trained on the **other 19 only** and then run on the full
text of the one it has never seen. Results are in `data/doc_eval.csv`.

| | |
|---|---|
| Decisions checked (20 policies × 8 clauses, 8 marked "unclear" and excluded) | 152 |
| **Correct** | **146 (96%)** |
| Real gaps correctly flagged | 15 of 16 (94%) |
| False alarms (flagged missing, but it's there) | 5 |
| Gaps missed | 1 |

All 6 errors are in the two weakest sentence-level classes, `controller` and `complaints_ico`, e.g.
Spotify says "your local data protection authority" instead of naming the ICO.

**How the correct answers were decided:** a clause counts as present if the page states it or clearly
links to a sub-page that does (the ICO-endorsed "layered notice" style). Borderline cases (partially
loaded pages, organisation named but no controller statement) were marked `unclear` and excluded.
**The truth column was judged by an AI assistant (Claude) and still needs a human spot-check**,
especially the 6 disagreements and 8 unclear rows.

**Possible next step:** add high-precision rules ("Information Commissioner", "data protection authority",
"company/charity number") as a backstop for the two weak clauses. If we do, re-test on *new* policies,
not these 20, so we don't tune to the test.

Earlier 9-label numbers (72% on unreviewed labels) aren't comparable: fewer categories, and graded
against LLM labels before human review.

## Limitations and next steps
- 135 recently moved sentences still need a human check.
- `controller` (22 examples) and `automated_decisions` (5) are weak: too few examples. More policies
  would help most; synthetic training sentences (`synthesize.py`, tested on real sentences only) are an option.
- Multi-label: some sentences cover two things. The review tool records a second label in `also`;
  a multi-label model is a next step.
