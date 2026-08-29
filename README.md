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

Forge Dispatch is a **multi-agent Stack Audit Pipeline** built on Forge's architecture. Three Agents collaborate to deliver a weekly intelligence Brief without human assembly:

```
┌─────────────────────────────────────────────────────────┐
│                    Forge Dispatch Pipeline               │
│                                                         │
│  ┌──────────────┐  Signals  ┌──────────────┐  Gaps     │
│  │   Sensing    │ ────────► │  Reasoning   │ ────────► │
│  │    Agent     │           │    Agent     │           │
│  └──────────────┘           └──────────────┘           │
│    GitHub + Linear                Cross-ref             │
│    raw Signal pull             Gap detection            │
│                                                         │
│                               ┌──────────────┐          │
│                               │  Reporting   │          │
│                               │    Agent     │          │
│                               └──────────────┘          │
│                               Plain-language Brief       │
│                               + human checkpoint         │
└─────────────────────────────────────────────────────────┘
```

**Systems connected (this submission):** GitHub + Linear (via their public APIs, synthetic data)

---

## Improvement Changelog

| Stage | What We Tried & Why | Evidence | Decision |
|---|---|---|---|
| **Baseline** | Single GPT-4o prompt with manually assembled context | See `eval/results/baseline.json` | Starting point |
| **Iteration 1** | Added live GitHub + Linear API polling (Sensing Agent) | Gap detection rate: baseline → Sensing | Kept |
| **Iteration 2** | Added cross-agent Reasoning step to correlate Signals across Systems | False positive rate dropped | Kept |
| **Iteration 3** | Added human-approval checkpoint before Brief delivery | Trust + hackathon compliance | Kept |
| **Final** | Full 3-Agent Pipeline | See `eval/results/forge.json` | Ships |

*Changelog will be completed with real numbers after evaluation runs.*

---

## Evaluation

**Primary metric:** Gap detection rate — what fraction of injected Gaps does the solution correctly surface vs. miss?

**Secondary metrics:** Time per Brief (manual vs. automated), false positive rate.

**Test suite:** 10 synthetic startup scenarios in `eval/cases/`. Each case has a known ground-truth set of Gaps.

| Metric | Baseline | Forge Dispatch | Change |
|---|---|---|---|
| Gap detection rate | TBD | TBD | TBD |
| Time per Brief | ~45 min (manual) | ~60 sec | TBD |
| False positive rate | TBD | TBD | TBD |

*Results populated after eval run. See `eval/results/`.*

---

## Reproducibility — Run It Yourself

### Prerequisites

- Python 3.11+
- `OPENAI_API_KEY` (GPT-4o access)
- `GITHUB_TOKEN` (read-only, public repos fine)
- `LINEAR_API_KEY` (read-only)

### Setup

```bash
git clone https://github.com/T9ner/forge-dispatch
cd forge-dispatch
pip install -r requirements.txt
cp .env.example .env
# fill in your keys in .env
```

### Run the baseline

```bash
python baseline/run.py --case eval/cases/case_01.json
```

### Run the Forge Pipeline

```bash
python agents/pipeline.py --case eval/cases/case_01.json
```

### Run full evaluation

```bash
python eval/score.py
# outputs eval/results/baseline.json and eval/results/forge.json
```

---

## Main Failure Mode & Hot Take

*To be completed after evaluation runs.*

---

## What Existed Before This Competition

- [forgeaicore.com](https://www.forgeaicore.com) — Forge's product website and brand
- The Forge AI Worker architecture concept and the Stack Audit service offering

**What was built for this submission:**
Everything in this repository — the Pipeline code, evaluation harness, test cases, and baseline.
