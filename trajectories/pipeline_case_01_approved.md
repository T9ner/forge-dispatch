# Agent Trajectory — Forge Dispatch

- **Run ID:** `forge-case_01-58a85995`
- **Schema:** `1.0` (Canonical session log — see `trajectories/SCHEMA.md`)
- **Pipeline:** `forge-dispatch`
- **Case:** `case_01`
- **Model:** `minimax/minimax-m2.7:free` via `openrouter`
- **Mode:** mock
- **Auto-approve:** True
- **Graph:** `sense → decide → (gaps?) → report → approve → (approved?) → save | END`
- **Thread:** `forge-case_01`
- **Outcome:** `saved`

## Session log (projection)

### [1] run.start

Input the Pipeline saw (ground truth excluded):

```json
{
  "case_id": "case_01",
  "mock": true,
  "auto_approve": true,
  "mock_responses": {
    "github": {
      "merged_prs": [
        {
          "number": 42,
          "title": "Add user auth flow",
          "body": "Closes LIN-55. Implements the login and signup screens.",
          "merged_at": "2026-08-25T10:00:00Z"
        }
      ],
      "open_issues": []
    },
    "linear": {
      "tickets": [
        {
          "id": "LIN-55",
          "title": "Add user auth flow",
          "state": {
            "name": "In Progress"
          },
          "updatedAt": "2026-08-20T08:00:00Z",
          "labels": {
            "nodes": []
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
          "number": 42,
          "title": "Add user auth flow",
          "body": "Closes LIN-55. Implements the login and signup screens.",
          "merged_at": "2026-08-25T10:00:00Z"
        }
      ],
      "open_issues": []
    },
    "linear": {
      "tickets": [
        {
          "id": "LIN-55",
          "title": "Add user auth flow",
          "state": {
            "name": "In Progress"
          },
          "updatedAt": "2026-08-20T08:00:00Z",
          "labels": {
            "nodes": []
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
  "gaps": [
    {
      "id": "gap_1",
      "description": "PR #42 (Add user auth flow) was merged on 2026-08-25 with body stating 'Closes LIN-55', but the linked Linear ticket LIN-55 remains in 'In Progress' state and was last updated on 2026-08-20 (before the merge). The ticket should have been moved to 'Done' after the PR merged.",
      "evidence": {
        "github": "PR #42 merged 2026-08-25, body: 'Closes LIN-55. Implements the login and signup screens.'",
        "linear": "LIN-55 title 'Add user auth flow', state 'In Progress', updatedAt 2026-08-20T08:00:00Z"
      },
      "systems": [
        "github",
        "linear"
      ]
    }
  ],
  "usage_reasoning": {
    "prompt_tokens": 743,
    "completion_tokens": 396,
    "total_tokens": 1139
  }
}
```

### [4] edge.route

**decide→?** → `report`

### [5] node.complete — `report`

```json
{
  "brief": "---\n\n## Forge Stack Brief\n\n**Date:** August 31, 2026\n**Systems scanned:** GitHub, Linear\n\n### Gaps Detected (1 total)\n\n**[Gap 1]** Merged PR didn't close its linked Linear ticket\n\u2192 PR #42 was merged on August 25 and says \"Closes LIN-55\" in the description, but the Linear ticket is still showing as \"In Progress\" and hasn't been touched since August 20.\n\u2192 **Evidence:** PR #42 merged 2026-08-25 (body: \"Closes LIN-55. Implements the login and signup screens.\"); LIN-55 still \"In Progress\", last updated 2026-08-20\n\u2192 **Suggested action:** Move LIN-55 to \"Done\" in Linear \u2014 either manually or investigate if your automation failed.\n\n---",
  "usage_reporting": {
    "prompt_tokens": 426,
    "completion_tokens": 328,
    "total_tokens": 754
  }
}
```

### [6] node.complete — `approve`

```json
{
  "approved": true
}
```

### [7] checkpoint.skip

Reason: `auto_approve`

### [8] node.complete — `save`

```json
{
  "result": {
    "case_id": "case_01",
    "gaps_detected": [
      {
        "id": "gap_1",
        "description": "PR #42 (Add user auth flow) was merged on 2026-08-25 with body stating 'Closes LIN-55', but the linked Linear ticket LIN-55 remains in 'In Progress' state and was last updated on 2026-08-20 (before the merge). The ticket should have been moved to 'Done' after the PR merged."
      }
    ],
    "brief": "---\n\n## Forge Stack Brief\n\n**Date:** August 31, 2026\n**Systems scanned:** GitHub, Linear\n\n### Gaps Detected (1 total)\n\n**[Gap 1]** Merged PR didn't close its linked Linear ticket\n\u2192 PR #42 was merged on August 25 and says \"Closes LIN-55\" in the description, but the Linear ticket is still showing as \"In Progress\" and hasn't been touched since August 20.\n\u2192 **Evidence:** PR #42 merged 2026-08-25 (body: \"Closes LIN-55. Implements the login and signup screens.\"); LIN-55 still \"In Progress\", last updated 2026-08-20\n\u2192 **Suggested action:** Move LIN-55 to \"Done\" in Linear \u2014 either manually or investigate if your automation failed.\n\n---",
    "raw_gaps": [
      {
        "id": "gap_1",
        "description": "PR #42 (Add user auth flow) was merged on 2026-08-25 with body stating 'Closes LIN-55', but the linked Linear ticket LIN-55 remains in 'In Progress' state and was last updated on 2026-08-20 (before the merge). The ticket should have been moved to 'Done' after the PR merged.",
        "evidence": {
          "github": "PR #42 merged 2026-08-25, body: 'Closes LIN-55. Implements the login and signup screens.'",
          "linear": "LIN-55 title 'Add user auth flow', state 'In Progress', updatedAt 2026-08-20T08:00:00Z"
        },
        "systems": [
          "github",
          "linear"
        ]
      }
    ],
    "usage": {
      "prompt_tokens": 1169,
      "completion_tokens": 724,
      "total_tokens": 1893
    }
  }
}
```

### [9] run.end — `saved`

```json
{
  "case_id": "case_01",
  "gaps_detected": [
    {
      "id": "gap_1",
      "description": "PR #42 (Add user auth flow) was merged on 2026-08-25 with body stating 'Closes LIN-55', but the linked Linear ticket LIN-55 remains in 'In Progress' state and was last updated on 2026-08-20 (before the merge). The ticket should have been moved to 'Done' after the PR merged."
    }
  ],
  "brief": "---\n\n## Forge Stack Brief\n\n**Date:** August 31, 2026\n**Systems scanned:** GitHub, Linear\n\n### Gaps Detected (1 total)\n\n**[Gap 1]** Merged PR didn't close its linked Linear ticket\n\u2192 PR #42 was merged on August 25 and says \"Closes LIN-55\" in the description, but the Linear ticket is still showing as \"In Progress\" and hasn't been touched since August 20.\n\u2192 **Evidence:** PR #42 merged 2026-08-25 (body: \"Closes LIN-55. Implements the login and signup screens.\"); LIN-55 still \"In Progress\", last updated 2026-08-20\n\u2192 **Suggested action:** Move LIN-55 to \"Done\" in Linear \u2014 either manually or investigate if your automation failed.\n\n---",
  "raw_gaps": [
    {
      "id": "gap_1",
      "description": "PR #42 (Add user auth flow) was merged on 2026-08-25 with body stating 'Closes LIN-55', but the linked Linear ticket LIN-55 remains in 'In Progress' state and was last updated on 2026-08-20 (before the merge). The ticket should have been moved to 'Done' after the PR merged.",
      "evidence": {
        "github": "PR #42 merged 2026-08-25, body: 'Closes LIN-55. Implements the login and signup screens.'",
        "linear": "LIN-55 title 'Add user auth flow', state 'In Progress', updatedAt 2026-08-20T08:00:00Z"
      },
      "systems": [
        "github",
        "linear"
      ]
    }
  ],
  "usage": {
    "prompt_tokens": 1169,
    "completion_tokens": 724,
    "total_tokens": 1893
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