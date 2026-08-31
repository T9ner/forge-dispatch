# Session Log Schema (DSH-inspired)

Forge Dispatch adopts the same principle as [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness): **the session log is the run**. Markdown trajectories are a human-readable projection; the JSON file is canonical and reconstructable.

## Files

| File | Role |
|---|---|
| `*.json` | Canonical append-only session log |
| `*.md` | Judge-readable projection (generated from JSON) |

Generate both with:

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve \
    --trace trajectories/pipeline_case_01_approved
```

## Top-level shape

```json
{
  "schema_version": "1.0",
  "run_id": "forge-case_01-a1b2c3d4",
  "started_at": "2026-08-31T02:00:00+00:00",
  "ended_at": "2026-08-31T02:00:45+00:00",
  "outcome": "saved",
  "composition": { ... },
  "input": { ... },
  "events": [ ... ]
}
```

### `composition` — runtime manifest

Pins the tuple needed to reproduce a run (DSH's "composition identity"):

```json
{
  "pipeline": "forge-dispatch",
  "runner": "langgraph",
  "graph": "sense → decide → (gaps?) → report → approve → (approved?) → save | END",
  "model": "nvidia/nemotron-3-super-120b-a12b:free",
  "provider": "openrouter",
  "checkpoint": "MemorySaver",
  "thread_id": "forge-case_01",
  "mock": true,
  "auto_approve": true
}
```

### `input` — what the Pipeline saw

Ground-truth gaps are **never** included. Only mock/live System responses and run flags.

### `outcome` values

| Value | Meaning |
|---|---|
| `saved` | Brief approved (or auto-approved) and written to `eval/results/` |
| `refused` | Reviewer refused at the APPROVE checkpoint; nothing saved |
| `no_gaps_saved` | Zero gaps detected; report/approve skipped; save ran with empty gaps |
| `ended` | Run finished without a persisted result (fallback) |

## Event vocabulary

Every event has monotonic `seq`, ISO8601 `ts`, and a typed `payload`.

| Type | When | Payload |
|---|---|---|
| `run.start` | Run begins | `{ "input": { case_id, mock, mock_responses, ... } }` |
| `node.complete` | A graph node finishes | `{ "node": "sense", "output": { ...delta } }` |
| `edge.route` | Conditional edge fires | `{ "edge": "decide→?", "target": "save", "reason": "no_gaps" }` |
| `checkpoint.interrupt` | LangGraph pauses at APPROVE | `{ "prompt", "case_id", "n_gaps" }` |
| `checkpoint.resume` | Reviewer decision applied | `{ "approved": true \| false }` |
| `checkpoint.skip` | Eval bypasses checkpoint | `{ "reason": "auto_approve" }` |
| `llm.complete` | Baseline single-shot LLM call | `{ "gaps_detected", "usage" }` |
| `run.end` | Run finishes | `{ "outcome", "result" }` |

## DSH mapping

| DeepSeek Harness concept | Forge Dispatch equivalent |
|---|---|
| Append-only session log | `events[]` in `*.json` |
| Composition manifest | `composition` block |
| Model-visible state reconstructable from log | `input` + node outputs + LLM deltas |
| Approval as policy, not loop hack | `checkpoint.interrupt` / `resume` / `skip` |
| UI/transcript as projection | `*.md` generated from JSON |

## Reconstruction rules

From a session log alone you can rebuild:

1. **Signals** — from `node.complete` where `node == "sense"`
2. **Gaps** — from `node.complete` where `node == "decide"`
3. **Brief** — from `node.complete` where `node == "report"` (if present)
4. **Approval decision** — from `checkpoint.resume` or `checkpoint.skip`
5. **Final artifact** — from `run.end.result`

No second informal buffer is maintained outside this stream.
