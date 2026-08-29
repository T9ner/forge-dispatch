# eval/

- Purpose: Evaluation harness — 10 synthetic startup test cases with known ground-truth Gaps, plus a scorer that runs both the baseline and Forge Pipeline and writes comparable results.
- Ownership: `score.py`, `cases/`, `results/` (generated — gitignored)

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
- Scoring metric: **Gap detection rate** = (correctly identified gaps) / (total ground truth gaps). A detected gap must match a ground truth gap by `id` — no fuzzy matching.
- All cases use synthetic data only. No real company names, repos, or people.
- `results/` is gitignored — judges run `score.py` themselves to reproduce.

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
