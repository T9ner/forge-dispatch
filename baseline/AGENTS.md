# baseline/

- Purpose: Single-prompt baseline agent. Represents the "naive" approach — one LLM call with manually assembled context — used as the before/after comparison point for judges.
- Ownership: `run.py`

## Local Contracts

- Accepts a single case JSON file path via `--case` CLI arg.
- Reads the case file, assembles a flat text context string, makes one LLM call via the shared OpenRouter client (`FORGE_MODEL`), and writes results to stdout as JSON.
- Must NOT make any live API calls to GitHub or Linear — it uses the pre-fetched snapshot data inside the case file. This keeps the comparison fair.
- Output schema: `{"gaps_detected": [...], "raw_response": "..."}` — same schema as the Forge Pipeline output so the scorer can compare them directly.

## Work Guidance

- Keep it intentionally simple. The point is to show what a non-agentic approach looks like.
- No tool calls, no multi-step reasoning, no retries. One prompt, one response.

## Verification

```bash
python baseline/run.py --case eval/cases/case_01.json
```
