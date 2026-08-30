# agents/

- Purpose: Forge multi-agent Pipeline built on LangGraph. Models the Sense → Decide → Act Workflow as a directed state graph with typed state, conditional edges, and a human-approval checkpoint.
- Ownership: `pipeline.py` (LangGraph graph definition + orchestrator), `sensing.py`, `reasoning.py`, `reporting.py`, `llm.py`

## Local Contracts

- `pipeline.py` defines the `StateGraph` and is the single entry point. Agent modules are registered as graph nodes.
- Pipeline state is typed via `PipelineState(TypedDict)`. Each node reads only the fields it needs and writes its output field. No shared global state.
- Each agent module exposes `run(context: dict) -> dict`. The pipeline nodes wrap these calls and map them to/from `PipelineState`.
- Conditional edge after `decide`: if no gaps found, skip `report` and go straight to `save`.
- Human-approval checkpoint is a graph node (`approve`), not a raw `input()` call in main. When `--auto-approve` is set, the node passes through without blocking.
- On any System API failure, agents must raise `SystemConnectionError(system_name, original_error)`.

## Graph structure

```
sense → decide →[gaps?]→ report → approve → save → END
                   ↓ (no gaps)
                  save → END
```

## Agent responsibilities

| Agent | Phase | Graph Node | Input | Output |
|---|---|---|---|---|
| `sensing.py` | Sense | `sense` | `PipelineState.case`, `.mock` | `signals` |
| `reasoning.py` | Decide | `decide` | `signals` | `gaps` |
| `reporting.py` | Act | `report` | `gaps` | `brief` |

## Work Guidance

- Sensing Agent makes real API calls (GitHub + Linear) OR reads from the case file's `mock_responses` field when `--mock` flag is set.
- Reasoning Agent uses the model from `llm.py` with a structured system prompt. Do not inline prompts in `pipeline.py`.
- Reporting Agent generates a plain-language Brief. It must not invent Gaps not present in its input.
- `llm.py` is the single source of truth for the OpenRouter client and model selection. Never instantiate `OpenAI()` directly.

## Verification

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock
python agents/pipeline.py --case eval/cases/case_04.json --mock --auto-approve  # no-gaps path
```

## Child DOX Index

*(no sub-packages, flat module structure)*
