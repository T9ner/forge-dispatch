# Forge Dispatch

micro1 Agentic Workflows Hackathon submission.

Forge Dispatch is a multi-agent stack audit pipeline built on LangGraph. It senses cross-tool discrepancies across GitHub and Linear, resolves status drift, and generates an actionable weekly brief with human-in-the-loop approval.

---

## Contents

- [The User and Their Bottleneck](#the-user-and-their-bottleneck)
- [System Architecture](#the-forge-solution)
- [Improvement Changelog](#improvement-changelog)
- [Evaluation and Benchmarks](#evaluation)
- [The Expanding Potential of Forge](#the-expanding-potential-of-forge)
- [Reproducibility Guide](#reproducibility--run-it-yourself)
- [Failure Mode and Hot Take](#main-failure-mode--hot-take)
- [Prior Work Disclosure](#what-existed-before-this-competition)
- [Important Files and Directories](#important-files-and-directories)

---

## The User and Their Bottleneck

**Who has this problem?**  
Founders and operations leads at 5 to 50 person startups running multiple tools at the same time, including GitHub, Linear, Notion, Slack, and CRMs. Every tool tracks a piece of the truth, but no single dashboard gives the full picture.

**What bottleneck makes it worth solving?**  
Pulling a coherent status picture across a company's tools takes 30 to 60 minutes when done by hand. Teams do it reactively, usually after something breaks. Status drifts quietly between tools: a pull request merges on Friday, but the Linear ticket stays marked "In Progress" on Monday. A feature is marked done in Linear, but two critical bug issues remain open in GitHub. These gaps stay invisible until they delay a release or cause an incident.

**Why solving it matters:**  
Each missed gap compounds into delayed decisions, surprise regressions, and misaligned teams. For a 10-person startup, losing two hours a week to cross-tool firefighting wastes roughly 100 engineer-hours every year.

---

## The Forge Solution

Forge Dispatch runs as a directed state graph built on LangGraph. Three specialized agents collaborate as nodes in the graph to deliver a verified weekly intelligence brief:

```
┌──────────────────────────────────────────────────────────────┐
│              Forge Dispatch Pipeline (LangGraph)             │
│                                                              │
│  ┌────────┐       ┌─────────┐       ┌──────────┐            │
│  │ SENSE  │──────▶│ DECIDE  │──────▶│  REPORT  │            │
│  │ node   │       │  node   │ gaps? │   node   │            │
│  └────────┘       └─────────┘  yes  └──────────┘            │
│   GitHub +             │                  │                  │
│   Linear API           │ no gaps          ▼                  │
│                        │            ┌──────────┐             │
│                        │            │ APPROVE  │             │
│                        │            │  node    │             │
│                        │            └──────────┘             │
│                        │              human  │               │
│                        ▼                     ▼               │
│                   ┌────────┐           ┌────────┐            │
│                   │  SAVE  │           │  SAVE  │            │
│                   │  node  │           │  node  │            │
│                   └────────┘           └────────┘            │
│                       ▼                    ▼                 │
│                      END                  END                │
└──────────────────────────────────────────────────────────────┘
```

State flows through every node as a typed dictionary (`PipelineState`). Each node reads only the fields it needs and writes its own output field. If the decide node finds zero gaps, the pipeline skips brief generation entirely and routes straight to saving.

Before any brief is saved or delivered, the graph pauses at the `approve` node using a real LangGraph `interrupt()`. A human reviewer in the terminal enters `y` or `N`. Refusal terminates the run immediately without writing data.

---

## Improvement Changelog

| Stage | What We Tried and Why | Evidence | Decision |
|---|---|---|---|
| **Baseline** | Single prompt with a flat text context dump | 95% detection rate, 10% false positive rate ([`eval/results/baseline.json`](./eval/results/baseline.json)) | Starting point |
| **Iteration 1** | Added live GitHub and Linear API extraction in a dedicated sensing node | Clean structured signals extracted directly from tool APIs | Kept |
| **Iteration 2** | Added a cross-system reasoning step to correlate signals across tools | Detection reached **100%**, false positive rate dropped from **10% to 0%** | Kept |
| **Iteration 3** | Added a human approval checkpoint before brief delivery | Real LangGraph `interrupt()`, delivery is fully human-gated | Kept |
| **Final** | Full 3-agent pipeline with canonical append-only session logging | **100% detection, 0% false positives**, 33.4s average run time ([`eval/results/forge.json`](./eval/results/forge.json)) | Ships |

---

## Evaluation

**Primary metric:** Gap detection rate, measuring the fraction of injected discrepancies the agent surfaces correctly.

**Secondary metrics:** False positive rate, wall-clock run time, token usage.

**Test suite:** 10 synthetic startup scenarios in [`eval/cases/`](./eval/cases/). Each case contains ground-truth discrepancies across GitHub pull requests, issues, and Linear tickets.

| Metric | Baseline (Single-Prompt) | Forge Dispatch (LangGraph) | Change |
|---|---|---|---|
| **Gap detection rate** | 95% | **100%** | **+5%** |
| **False positive rate** | 10% | **0%** | **-10% (eliminated)** |
| **Average run time** | 23.7s | 33.4s | +9.7s (multi-node verification) |
| **Total token usage** | 9,052 tokens | 20,845 tokens | +11,793 (graph decomposition) |
| **Cost per audit** | $0.00 (free models) | $0.00 (free models) | $0.00 |

Detailed per-case results are stored in [`eval/results/baseline.json`](./eval/results/baseline.json) and [`eval/results/forge.json`](./eval/results/forge.json).

---

## The Expanding Potential of Forge

While this submission focuses on GitHub and Linear, the Forge Dispatch architecture is built as an open, tool-agnostic state machine. The `Sense` node accepts plug-and-play collectors, feeding structured signals into the shared `PipelineState` without changing the reasoning graph or approval contracts.

Here is how Forge extends across the full modern startup stack:

1. **Customer Support and Chat (Slack, Discord, Zendesk, Intercom):**  
   Correlates customer-reported bugs in Slack channels or Zendesk tickets against active engineering sprints. If a high-priority bug is reported five times in support but no ticket exists in Linear or Jira, Forge surfaces the missing ticket immediately.

2. **Product Documentation (Notion, Confluence, Coda):**  
   Detects drift between product roadmaps and reality. For example, a feature marked "Shipped" in a Notion PRD when no matching pull request has been merged in GitHub.

3. **Production Observability (Sentry, Datadog, PagerDuty):**  
   Links production error spikes to recent deployments. If a critical Sentry issue appears within two hours of a merged pull request, Forge connects the code commit to the regression and alerts ops leads before customers complain.

4. **Sales and CRM (HubSpot, Salesforce, Stripe):**  
   Identifies promises made in sales deals that have no corresponding engineering deliverables, or detects enterprise contracts signed with custom features that were never scheduled into a sprint.

Because every new tool integration is simply a connector returning structured dictionary signals, expanding Forge to cover new systems requires only a lightweight adapter in `agents/sensing.py`.

---

## Reproducibility — Run It Yourself

### Prerequisites

- Python 3.11+
- `OPENROUTER_API_KEY` (Free model access via OpenRouter)
- `GITHUB_TOKEN` (Read-only, required only for live API mode)
- `LINEAR_API_KEY` (Read-only, required only for live API mode)

### Setup

```bash
git clone https://github.com/T9ner/forge-dispatch
cd forge-dispatch
pip install -r requirements.txt
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env
```

### Run the baseline

```bash
python baseline/run.py --case eval/cases/case_01.json
```

### Run the Forge Pipeline

```bash
# Interactive mode (pauses at the human approval checkpoint)
python agents/pipeline.py --case eval/cases/case_01.json --mock

# Auto-approve mode (bypasses checkpoint for automated tests)
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve
```

### Run the full benchmark evaluation

```bash
python eval/score.py
# Evaluates all 10 cases, updates eval/results/, and prints the summary table
```

### Generate session trajectory logs

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve --trace trajectories/pipeline_case_01_approved
python baseline/run.py --case eval/cases/case_01.json --trace trajectories/baseline_case_01
```

---

## Main Failure Mode & Hot Take

**Main Failure Mode:** Single-shot baseline prompts suffer from cross-tool confusion and false positives (10% FPR). They regularly hallucinate gaps on legitimate non-code tasks, such as documentation updates closed without pull requests, or miss subtler cross-system regressions. By splitting the task into dedicated sensing, reasoning, and reporting nodes, Forge Dispatch eliminated all false positives and reached 100% gap detection.

**Hot Take:** Monolithic prompts dumping raw JSON into huge context windows look simple, but they are unreliable in production stacks. Real agentic workflows need state graph decomposition, verifiable evidence extraction, and real human-in-the-loop checkpoints before any report reaches company leadership.

---

## What Existed Before This Competition

- [forgeaicore.com](https://www.forgeaicore.com), Forge's product website and brand
- The high-level concept of stack audits for AI workers

**What was built specifically for this submission:**  
Everything in this repository, including the LangGraph pipeline, the evaluation harness and test cases, the single-prompt baseline, the canonical session logging engine, and the benchmark results.

---

## Important Files and Directories

- [`agents/pipeline.py`](./agents/pipeline.py): LangGraph orchestrator and state graph definition.
- [`agents/reasoning.py`](./agents/reasoning.py): Decide node with cross-system correlation logic.
- [`agents/trace.py`](./agents/trace.py): Canonical append-only session logging engine.
- [`baseline/run.py`](./baseline/run.py): Single-prompt comparison agent.
- [`eval/score.py`](./eval/score.py): Benchmark evaluation harness.
- [`eval/cases/`](./eval/cases/): 10 synthetic test scenarios with ground-truth data.
- [`trajectories/`](./trajectories/): Dual-file session logs (`.json`) and markdown projections (`.md`).
