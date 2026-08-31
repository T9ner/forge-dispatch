# Forge Dispatch

**micro1 Agentic Workflows Hackathon submission**

---

## The User and Their Bottleneck

**Who has this problem?**
Startup founders and ops leads at 5–50 person companies running 3–5 tools simultaneously (GitHub, Linear, Notion, Slack, CRM). Every tool tracks a piece of the truth. Nobody has the full picture.

**What bottleneck makes it worth solving?**
Pulling a coherent status picture across a startup's Stack takes 30–60 minutes manually, happens reactively (usually when something has already gone wrong), and misses drift between stated and actual state. A PR merged three days ago but the Linear ticket is still "In Progress." A feature is marked done in Notion but has three open bugs in GitHub. These gaps are invisible until they cause a problem.

**Why solving it matters:**
Each missed gap is a compounding cost — delayed decisions, surprise regressions, misaligned teams. For a 10-person startup, one gap-induced incident per week at 2 hours of firefighting is ~100 engineer-hours lost per year.

---

## The Forge Solution

Forge Dispatch is a **multi-agent Stack Audit Pipeline** built on LangGraph. Three Agents collaborate as nodes in a state graph to deliver a weekly intelligence Brief without human assembly:

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
│                        │              human ✓│               │
│                        ▼                     ▼               │
│                   ┌────────┐           ┌────────┐            │
│                   │  SAVE  │           │  SAVE  │            │
│                   │  node  │           │  node  │            │
│                   └────────┘           └────────┘            │
│                       ▼                    ▼                 │
│                      END                  END                │
└──────────────────────────────────────────────────────────────┘
```

**State flows as a typed dict** through every node. Each node reads only what it needs and writes its output field. The conditional edge after DECIDE skips reporting entirely when no gaps are found.

---

## Improvement Changelog

| Stage | What We Tried & Why | Evidence | Decision |
|---|---|---|---|
| **Baseline** | Single LLM prompt with flat context dump | 95% detection, 10% false positives (`eval/results/baseline.json`) | Starting point |
| **Iteration 1** | Added live GitHub + Linear API polling (Sensing Agent) | Clean structured Signals extracted directly from tool APIs | Kept |
| **Iteration 2** | Added cross-agent Reasoning step to correlate Signals across Systems | Detection rate reached **100%**, False Positive Rate dropped from **10% → 0%** | Kept |
| **Iteration 3** | Added human-approval checkpoint before Brief delivery | Real LangGraph `interrupt()`, consequential delivery is 100% human-gated | Kept |
| **Final** | Full 3-Agent Pipeline with DeepSeek Harness tracing | **100% detection, 0% FPR**, 33.4s avg (`eval/results/forge.json`) | Ships |

---

## Evaluation

**Primary metric:** Gap detection rate — what fraction of injected Gaps does the solution correctly surface vs. miss?

**Secondary metrics:** False positive rate, wall-clock duration, token usage.

**Test suite:** 10 synthetic startup scenarios in `eval/cases/`. Each case has a known ground-truth set of Gaps across GitHub and Linear.

| Metric | Baseline (Single-Prompt) | Forge Dispatch (LangGraph) | Change |
|---|---|---|---|
| **Gap detection rate** | 95% | **100%** | **+5%** |
| **False positive rate** | 10% | **0%** | **-10% (eliminated)** |
| **Avg time per case** | 23.7s | 33.4s | +9.7s (multi-agent verification) |
| **Total token usage** | 9,052 tokens | 20,845 tokens | +11,793 (graph decomposition) |
| **Cost per Brief** | $0.00 (free models) | $0.00 (free models) | $0.00 |

*Full machine-readable results in `eval/results/baseline.json` and `eval/results/forge.json`.*

---

## Reproducibility — Run It Yourself

### Prerequisites

- Python 3.11+
- `OPENROUTER_API_KEY` (Free model access via OpenRouter)
- `GITHUB_TOKEN` (read-only, for live mode)
- `LINEAR_API_KEY` (read-only, for live mode)

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
python agents/pipeline.py --case eval/cases/case_01.json --mock
```

### Run full evaluation

```bash
python eval/score.py
# outputs eval/results/baseline.json and eval/results/forge.json
```

### Generate DSH Trajectories

```bash
python agents/pipeline.py --case eval/cases/case_01.json --mock --auto-approve --trace trajectories/pipeline_case_01_approved
python baseline/run.py --case eval/cases/case_01.json --trace trajectories/baseline_case_01
```

---

## Main Failure Mode & Hot Take

**Main Failure Mode:** Single-shot baseline prompts suffer from cross-tool confusion and false positives (10% FPR) — frequently hallucinating gaps on legitimate non-code tickets (like documentation updates closed without PRs) or missing subtler cross-system regressions. By decomposing the workflow into dedicated **Sensing** (data extraction), **Reasoning** (evidence-based cross-referencing with strict grounding), and **Reporting** (actionable synthesis), Forge Dispatch eliminated all false positives (0% FPR) and achieved 100% gap detection.

**Hot Take:** Monolithic prompts dumping raw JSON into huge context windows look deceptively easy, but they cannot provide consequential reliability in production stacks. Real-world agentic workflows require state graph decomposition, verifiable evidence extraction, and real human-in-the-loop interrupt checkpoints before any intelligence brief reaches leadership.

---

## What Existed Before This Competition

- [forgeaicore.com](https://www.forgeaicore.com) — Forge's product website and brand
- The Forge AI Worker architecture concept and the Stack Audit service offering

**What was built for this submission:**
Everything in this repository — the Pipeline code, evaluation harness, test cases, and baseline.
