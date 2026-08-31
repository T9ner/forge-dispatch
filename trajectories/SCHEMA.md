# Session Log Schema

Forge Dispatch enforces an append-only event logging principle: **the session log is the run**. Markdown trajectories are human-readable projections rendered directly from the event stream. The JSON file is the canonical, reconstructable record.

## Files

| File | Role |
|---|---|
| `*.json` | Canonical append-only session log |
| `*.md` | Human-readable projection (generated from JSON) |

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

Pins the exact tuple needed to reproduce a run:

```json
{
  "pipeline": "forge-dispatch",
  "runner": "langgraph",
  "graph": "sense → decide → (gaps?) → report → approve → (approved?) → save | END",
  "model": "minimax/minimax-m2.7:free",
  "provider": "openrouter",
  "checkpoint": "MemorySaver",
  "thread_id": "forge-case_01",
  "mock": true,
  "auto_approve": true
}
```

### `input` — what the Pipeline saw

Ground-truth gaps are **never** included. Only mock or live system responses and run flags are recorded.

### `outcome` values

| Value | Meaning |
|---|---|
| `saved` | Brief approved (or auto-approved) and written to `eval/results/` |
| `refused` | Reviewer refused at the APPROVE checkpoint; nothing saved |
| `no_gaps_saved` | Zero gaps detected; report and approve skipped; save ran with empty gaps |
| `ended` | Run finished without a persisted result (fallback) |

## Event vocabulary

Every event has a monotonic sequence number `seq`, an ISO8601 timestamp `ts`, and a typed `payload`.

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

## Reconstruction rules

From a session log alone, you can rebuild:

1. **Signals** — from `node.complete` where `node == "sense"`
2. **Gaps** — from `node.complete` where `node == "decide"`
3. **Brief** — from `node.complete` where `node == "report"` (if present)
4. **Approval decision** — from `checkpoint.resume` or `checkpoint.skip`
5. **Final artifact** — from `run.end.result`

No informal secondary state is maintained outside this stream.
