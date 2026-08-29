# eval/cases/

- Purpose: Synthetic test case definitions with ground-truth Gaps. Used by both the baseline and Forge Pipeline during scored evaluation.
- Ownership: All `case_NN.json` files.

## Local Contracts

- Files are named `case_01.json` through `case_10.json`.
- All data is synthetic — fictional team names, repo names, ticket IDs.
- Each case must have at least one ground-truth Gap. Cases 08–10 should have at least two Gaps requiring cross-System reasoning to detect.
- Do not add any real API tokens, user data, or PII to case files.
