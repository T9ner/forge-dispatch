# eval/

- Purpose: Evaluation harness — 10 synthetic startup test cases with known ground-truth Gaps, plus a scorer that runs both the baseline and Forge Pipeline and writes comparable results.
- Ownership: `score.py`, `cases/`, `results/` (generated — committed as evidence)

## Local Contracts

- `cases/case_NN.json` — each case file has this schema:
  ```json
  {
    "id": "case_01",
    "description": "...",
    "mock_responses": {
      "github": { ... },
      "linear": { ... }
    },
    "ground_truth_gaps": [
      { "id": "gap_1", "description": "...", "systems": ["github", "linear"] }
    ]
  }
  ```
- `score.py` runs both `baseline/run.py` and `agents/pipeline.py --mock` on all 10 cases and writes `eval/results/baseline.json` and `eval/results/forge.json`.
- Scoring metric: **Gap detection rate** = (correctly identified gaps) / (total ground truth gaps). A detected gap must match a ground truth gap by `id` — no fuzzy matching. Secondary metrics: **false-positive rate** (share of detected gaps not matching ground truth) and **wall-clock duration** per case; token usage is recorded in the results files.
- All cases use synthetic data only. No real company names, repos, or people.
- `results/` is committed as submission evidence (all synthetic). Judges can regenerate everything with `python eval/score.py`.

## Work Guidance

- Cases should cover a range: easy (single-system gap), medium (cross-system gap), hard (gap that requires multi-hop reasoning). Include at least one case where the baseline plausibly fails.
- Each case's `ground_truth_gaps` must be unambiguous — a human reviewing the mock data should agree the gap exists.

## Verification

```bash
python eval/score.py
# Writes eval/results/baseline.json and eval/results/forge.json
# Prints a summary table to stdout
```

## Child DOX Index

- [cases/](./cases/AGENTS.md): Synthetic test case definitions
