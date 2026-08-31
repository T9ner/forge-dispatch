# trajectories/

- Purpose: DeepSeek Harness (DSH) inspired session logs and markdown trajectory projections.
- Ownership: `SCHEMA.md`, `README.md`, all `*.json` and `*.md` trajectory files.

## Local Contracts

- Dual-file projection: Every run produces a canonical append-only `.json` session log and a human-readable `.md` markdown projection.
- Strict schema adherence to `SCHEMA.md` with monotonic event sequence numbering (`seq`).
- Zero company PII or credentials in logs (synthetic data only).
- Ground truth is never visible in input logs (`run.start`).

## Verification

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve --trace trajectories/pipeline_case_01_approved
python baseline/run.py --case eval/cases/case_01.json --trace trajectories/baseline_case_01
```
