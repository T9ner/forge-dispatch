# eval/cases/

- Purpose: Synthetic test case definitions with ground-truth Gaps. Used by both the baseline and Forge Pipeline during scored evaluation.
- Ownership: All `case_NN.json` files.

## Local Contracts

- Files are named `case_01.json` through `case_10.json`.
- All data is synthetic — fictional team names, repo names, ticket IDs.
- Ground-truth Gaps use ordinal IDs (`gap_1`, `gap_2`) per case. The scorer
  (`eval/score.py`) matches detected Gaps to ground truth by exact `id` —
  no fuzzy matching.
- Case design:
  - `case_04` and `case_07` are **no-gap negative controls** (zero ground-truth
    Gaps) — they measure false positives and exercise the skip-Brief path.
  - `case_08`, `case_09`, `case_10` are the **multi-gap hard cases** (two
    ground-truth Gaps each, requiring cross-System reasoning to detect).
  - All other cases have exactly one ground-truth Gap.
- Do not add any real API tokens, user data, or PII to case files.
