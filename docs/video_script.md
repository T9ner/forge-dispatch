# Solution Video Script — Forge Dispatch (5 minutes)

Target: micro1 Agentic Workflows Hackathon deliverable 03.
Record the terminal segments live; rehearse the talking parts. Total pace: ~30 s per beat below.

---

## Beat 1 — The Problem (0:00–0:45)

**On screen:** the README's "User and Their Bottleneck" section.

> Startups run 3–5 tools — GitHub, Linear, Notion, Slack. Every tool holds a
> piece of the truth; nobody has the full picture. A PR merges on Friday, the
> Linear ticket still says "In Progress" on Monday, and nobody notices until a
> customer does. For a 10-person startup that drift costs roughly 100
> engineer-hours a year in firefighting.

## Beat 2 — The Baseline (0:45–1:30)

**On screen:** `baseline/run.py` — the single-prompt agent.

> Our baseline is what a reasonable team does today: one LLM prompt with the
> GitHub and Linear data dumped into context. It's honest but shallow — one
> shot, no structure, no verification, no human gate. We score it on the same
> 10 synthetic cases as the full pipeline.

## Beat 3 — One Realistic Execution, Start to Finish (1:30–3:15)

**On screen:** `python agents/pipeline.py --case eval/cases/case_01.json --mock`

> Now the full Forge Dispatch pipeline, built as a LangGraph state graph.
> Walk through the nodes as they print:
>
> 1. **Sense** — the Sensing Agent collects raw Signals from GitHub and Linear
>    (live APIs in production, the case's mock data here).
> 2. **Decide** — the Reasoning Agent cross-references both Systems and emits
>    structured Gaps with evidence: PR numbers, ticket IDs.
> 3. **Act** — the Reporting Agent writes the plain-language Stack Brief a
>    founder reads on a Monday morning.
> 4. **APPROVE — the graph pauses.** This is a real LangGraph `interrupt()`:
>    the pipeline stops mid-graph and waits for a human y/N. Nothing is
>    delivered without a human signing off. (Show approving — the graph
>    resumes and saves.)
>
> Then, for contrast, re-run with "n": the refusal path — the run ends, and
> nothing is saved. Consequential delivery is always human-gated.

## Beat 4 — The Comparison (3:15–4:00)

**On screen:** `eval/results/baseline.json` vs `eval/results/forge.json`,
and the summary table from `python eval/score.py`.

> Same 10 cases, same model, same data — only the architecture differs.
> The baseline detected 95% of gaps with a 10% false positive rate. Forge Dispatch
> hit a perfect 100% detection rate and eliminated false positives entirely to 0%.
> Average duration is 33.4 seconds per audit with $0.00 API cost using OpenRouter free models.

## Beat 5 — The Changelog Story (4:00–4:40)

**On screen:** the README's Improvement Changelog table.

> The improvement came from three deliberate iterations: live Sensing instead
> of hand-assembled context; a cross-referencing Reasoning step that cut false
> positives from 10% down to 0%; and the human-approval checkpoint. **The single change that
> contributed most: the cross-System Reasoning step** — it's what turns two
> raw data dumps into grounded, evidenced Gaps. We also implemented DeepSeek Harness
> append-only session logging (`trajectories/`), ensuring every graph transition and
> human gate is 100% reconstructable.

## Beat 6 — Close (4:40–5:00)

> Forge Dispatch is a working Stack Audit: it senses where intelligence is
> lost between your Systems, and delivers an actionable Brief — with a human
> still holding the approval gate. Everything runs from a clean clone with one
> API key. Thanks for watching.

---

## Recording checklist

- [ ] Terminal font large (16pt+), light theme for contrast
- [ ] Beats 3/4 recorded live in one take (authentic > polished)
- [ ] Fill in measured numbers in Beats 4/5 before recording
- [ ] Show `trajectories/` on screen briefly (deliverable 04 exists)
- [ ] End card: repo URL + forgeaicore.com
