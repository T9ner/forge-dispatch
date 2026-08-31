# Agent Trajectory — Forge Dispatch

- **Run ID:** `forge-case_04-6425ce0d`
- **Schema:** `1.0` (DSH-inspired session log — see `trajectories/SCHEMA.md`)
- **Pipeline:** `forge-dispatch`
- **Case:** `case_04`
- **Model:** `minimax/minimax-m2.7:free` via `openrouter`
- **Mode:** mock
- **Auto-approve:** True
- **Graph:** `sense → decide → (gaps?) → report → approve → (approved?) → save | END`
- **Thread:** `forge-case_04`
- **Outcome:** `saved`

## Session log (projection)

### [1] run.start

Input the Pipeline saw (ground truth excluded):

```json
{
  "case_id": "case_04",
  "mock": true,
  "auto_approve": true,
  "mock_responses": {
    "github": {
      "merged_prs": [
        {
          "number": 55,
          "title": "Refactor database layer",
          "body": "Closes LIN-12. Migrates to async connection pool.",
          "merged_at": "2026-08-24T11:00:00Z"
        },
        {
          "number": 56,
          "title": "Update README",
          "body": "No ticket \u00e2\u20ac\u201d docs update only.",
          "merged_at": "2026-08-24T15:00:00Z"
        }
      ],
      "open_issues": []
    },
    "linear": {
      "tickets": [
        {
          "id": "LIN-12",
          "title": "Refactor database layer",
          "state": {
            "name": "Done"
          },
          "updatedAt": "2026-08-24T12:00:00Z",
          "labels": {
            "nodes": [
              {
                "name": "tech-debt"
              }
            ]
          }
        }
      ]
    }
  }
}
```

### [2] node.complete — `sense`

```json
{
  "signals": {
    "github": {
      "merged_prs": [
        {
          "number": 55,
          "title": "Refactor database layer",
          "body": "Closes LIN-12. Migrates to async connection pool.",
          "merged_at": "2026-08-24T11:00:00Z"
        },
        {
          "number": 56,
          "title": "Update README",
          "body": "No ticket \u00e2\u20ac\u201d docs update only.",
          "merged_at": "2026-08-24T15:00:00Z"
        }
      ],
      "open_issues": []
    },
    "linear": {
      "tickets": [
        {
          "id": "LIN-12",
          "title": "Refactor database layer",
          "state": {
            "name": "Done"
          },
          "updatedAt": "2026-08-24T12:00:00Z",
          "labels": {
            "nodes": [
              {
                "name": "tech-debt"
              }
            ]
          }
        }
      ]
    }
  }
}
```

### [3] node.complete — `decide`

```json
{
  "gaps": [],
  "usage_reasoning": {
    "prompt_tokens": 818,
    "completion_tokens": 377,
    "total_tokens": 1195
  }
}
```

### [4] edge.route

**decide→?** → `save`

### [5] node.complete — `save`

```json
{
  "result": {
    "case_id": "case_04",
    "gaps_detected": [],
    "brief": "No gaps detected. No brief generated.",
    "raw_gaps": [],
    "usage": {
      "prompt_tokens": 818,
      "completion_tokens": 377,
      "total_tokens": 1195
    }
  }
}
```

### [6] run.end — `saved`

```json
{
  "case_id": "case_04",
  "gaps_detected": [],
  "brief": "No gaps detected. No brief generated.",
  "raw_gaps": [],
  "usage": {
    "prompt_tokens": 818,
    "completion_tokens": 377,
    "total_tokens": 1195
  }
}
```

## Agent instructions used in this run

### Reasoning Agent (Decide phase) — system prompt

```
You are Forge's reasoning engine.

You receive structured Signals from two Systems:
- GitHub: merged pull requests and open issues
- Linear: project management tickets and their states

Your job is to detect Gaps — meaningful discrepancies between the stated
state and the actual state of work across these Systems.

Examples of Gaps to detect:
1. A PR was merged but the linked Linear ticket is still "In Progress" or "Todo"
2. A ticket is marked "Done" in Linear but GitHub still has open bug issues
   referencing the same feature or module, OR a software feature/code ticket is
   marked "Done" without any merged PR or code delivery in GitHub
3. A PR title or body references a ticket ID that does not exist in Linear
4. A high-priority or critical ticket is open in Linear but has no visible
   GitHub counterpart — no PR or issue references it, and it has not been
   updated in over a week. Work that is invisible in one System is itself a Gap.
5. A cluster of new bug issues opened around the time a PR merged and its
   ticket closed may indicate a regression caused by that change — connect them.

Rules:
- Only identify Gaps you can substantiate from the provided data
- Each Gap must reference specific evidence (PR number, ticket ID, etc.)
- Do not invent Gaps or speculate beyond the data given
- A "linked" relationship is established when: a PR body/title contains a
   ticket ID (e.g. "LIN-123", "Fixes #123"), a ticket's title matches a PR
   title closely, OR an open GitHub issue clearly targets the same feature or
   module as a Linear ticket (matching title words or labels, e.g. both
   mention "dark mode" or "billing")
- If an engineering or code feature ticket (e.g. labeled "feature", "bug", or
   describing software implementation such as "Implement CSV export") is marked
   "Done" in Linear but has no corresponding merged PR in GitHub, flag it as a Gap.
- Non-code tasks (e.g. documentation, process tasks, or tickets labeled "docs")
   marked "Done" without GitHub PRs are normal and should NOT be flagged as Gaps.

Respond with a JSON object:
{
  "gaps": [
    {
      "id": "gap_1",
      "description": "...",
      "evidence": {
        "github": "...",
        "linear": "..."
      },
      "systems": ["github", "linear"]
    }
  ]
}

If no gaps are found, return {"gaps": []}.
```

### Reporting Agent (Act phase) — system prompt

```
You are Forge's reporting engine.

You receive a list of detected Gaps — discrepancies between the stated
state and actual state of work across a startup's tools.

Write a plain-language Weekly Stack Brief. It should read as something
a founder or ops lead would actually want to open on a Monday morning.

Format:
---
## Forge Stack Brief

**Date:** {today}
**Systems scanned:** GitHub, Linear

### Gaps Detected ({n} total)

For each gap:
**[Gap N]** <one-line title>
→ <what the gap is, in plain English>
→ Evidence: <specific PR number / ticket ID>
→ Suggested action: <one concrete next step>

---

Rules:
- Use plain English. No jargon.
- Be specific — name the PR numbers and ticket IDs.
- Suggested actions should be concrete ("Close ticket LIN-42" not "resolve the discrepancy").
- If there are no gaps, say so clearly: "No gaps detected this week."
- Do not invent gaps. Only report what you received.
```

### Sensing Agent (Sense phase)

```
No LLM prompt — collects raw Signals from the GitHub REST API and Linear GraphQL API (or from the case file's mock_responses in mock mode). See agents/sensing.py.
```

All data in this trajectory is synthetic.