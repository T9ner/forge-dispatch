# Agent Trajectories

Representative execution traces for every agent in Forge Dispatch. Each
run produces two files following a dual-format session log architecture:

| Extension | Role |
|---|---|
| `.json` | **Canonical** append-only session log (reconstructable) |
| `.md` | Human-readable projection for review |

See [SCHEMA.md](./SCHEMA.md) for the full event vocabulary.

## How to generate

```bash
# Pipeline — writes both .json and .md from the same --trace stem
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve \
    --trace trajectories/pipeline_case_01_approved

python agents/pipeline.py --case eval/cases/case_08.json --mock --auto-approve \
    --trace trajectories/pipeline_case_08_multi_gap

python agents/pipeline.py --case eval/cases/case_04.json --mock --auto-approve \
    --trace trajectories/pipeline_case_04_no_gap_skip

# Interactive refusal path — answer "n" at the checkpoint
python agents/pipeline.py --case eval/cases/case_01.json --mock \
    --trace trajectories/pipeline_case_01_refused

# Baseline — single-shot session log
python baseline/run.py --case eval/cases/case_01.json \
    --trace trajectories/baseline_case_01
```

## Expected trajectory set

| File stem | What it shows |
|---|---|
| `baseline_case_01` | Baseline: one LLM call, no graph structure |
| `pipeline_case_01_approved` | Full Pipeline happy path with `checkpoint.skip` (auto-approve) |
| `pipeline_case_01_refused` | Reviewer refuses at `checkpoint.interrupt` → `checkpoint.resume` |
| `pipeline_case_04_no_gap_skip` | Conditional edge: `edge.route` to save with `reason: no_gaps` |
| `pipeline_case_08_multi_gap` | Hard multi-gap case across both Systems |

## Reading the session log

Events are typed and sequenced (`seq` 1, 2, 3...):

- **`run.start`** — input the Pipeline saw (mock System responses; no ground truth)
- **`node.complete`** — output delta from each graph node (`sense`, `decide`, `report`, …)
- **`edge.route`** — conditional edge decision (`no_gaps`, `approved`, `refused`)
- **`checkpoint.interrupt` / `checkpoint.resume`** — real LangGraph interrupt at APPROVE
- **`checkpoint.skip`** — eval runs with `--auto-approve`
- **`run.end`** — final outcome and persisted result

The `composition` block pins model, graph topology, and thread ID so runs
are completely reproducible.

All data in every trajectory is synthetic.
