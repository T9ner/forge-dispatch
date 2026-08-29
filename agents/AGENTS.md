# agents/

- Purpose: Forge multi-agent Pipeline — the three-Agent Workflow that senses cross-tool Gaps, reasons about them, and produces a Brief.
- Ownership: `pipeline.py` (orchestrator), `sensing.py`, `reasoning.py`, `reporting.py`

## Local Contracts

- `pipeline.py` is the single entry point. It orchestrates the three Agents in sequence and handles the human-approval checkpoint before Brief delivery.
- Each Agent module exposes exactly one public function: `run(context: dict) -> dict`. No side effects outside of that return value.
- Agents communicate via plain dicts only — no shared global state, no file I/O between agents mid-run.
- The human-approval checkpoint in `pipeline.py` must print the Brief to stdout and wait for `y/n` input before writing `eval/results/`. This satisfies hackathon ground rule #4.
- On any System API failure, agents must raise `SystemConnectionError(system_name, original_error)` — never swallow exceptions.

## Agent Responsibilities

| Agent | Phase | Input | Output |
|---|---|---|---|
| `sensing.py` | Sense | Case JSON (repo + project IDs) | `{"signals": [...]}` |
| `reasoning.py` | Decide | Signals dict | `{"gaps": [...]}` |
| `reporting.py` | Act | Gaps dict | `{"brief": "..."}` |

## Work Guidance

- Sensing Agent makes real API calls (GitHub + Linear) OR reads from the case file's `mock_responses` field when `--mock` flag is set. Always support `--mock` for eval runs.
- Reasoning Agent uses GPT-4o with a structured system prompt — see `reasoning.py` for the prompt. Do not inline prompts in `pipeline.py`.
- Reporting Agent generates a plain-language Brief. It must not invent Gaps not present in its input.

## Verification

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock
```

## Child DOX Index

*(no sub-packages — flat module structure)*
