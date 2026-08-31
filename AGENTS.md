# Forge Dispatch

- Purpose: Hackathon submission — a working multi-agent Stack Audit pipeline that senses cross-tool signal gaps in a startup's Stack and produces an actionable status brief.
- Ownership: Root config, shared env, top-level docs.

## Repository-Wide Contracts

- **Language**: All code is Python 3.11+. No JavaScript/TypeScript.
- **LLM calls**: Use `agents/llm.py`. `get_client()` returns the configured provider client (OpenRouter, OpenAI, Anthropic, or any custom OpenAI-compatible endpoint), and `get_model()` returns the active model name. Never instantiate raw client constructors directly in agent files.
- **Model selection**: Set `FORGE_MODEL` in `.env`. Supports open-source models via OpenRouter (e.g. `minimax/minimax-m2.7:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `meta-llama/llama-3.3-70b-instruct`), direct OpenAI models (`gpt-4o`, `gpt-4o-mini`), direct Anthropic models (`claude-3-5-sonnet-latest`), or custom local endpoints.
- **Env vars**: Never hardcode secrets. All credentials come from `.env` (loaded via `python-dotenv`). See `.env.example` for required vars.
- **Output format**: All agent outputs are plain Python dicts. No raw string parsing between agents — pass structured data.
- **Error handling**: Agents must never crash silently. On tool call failure, raise with a descriptive message that names the System that failed.
- **Domain language**: Follow `CONTEXT.md` strictly. The terms Agent, AI Worker, Pipeline, Workflow, System, Stack Audit, and Engagement have precise meanings — do not substitute synonyms.

## Security Invariants (no child AGENTS.md may weaken these)

- No write actions to any external System without an explicit human-approval checkpoint.
- No credentials may appear in any output file, log, or eval case.
- All eval cases use synthetic data only — no real company data.

## Child DOX Index

- [baseline/](./baseline/AGENTS.md): Single-prompt baseline agent for before/after comparison
- [agents/](./agents/AGENTS.md): Forge multi-agent Pipeline (Sensing → Reasoning → Reporting)
- [eval/](./eval/AGENTS.md): Evaluation harness — 10 test cases and scorer
- [trajectories/](./trajectories/AGENTS.md): Canonical session logs and trajectory projections
