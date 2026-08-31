# Agent Trajectory — Forge Dispatch

- **Run ID:** `baseline-case_01-0508a31a`
- **Schema:** `1.0` (DSH-inspired session log — see `trajectories/SCHEMA.md`)
- **Pipeline:** `forge-dispatch-baseline`
- **Case:** `case_01`
- **Model:** `minimax/minimax-m2.7:free` via `openrouter`
- **Outcome:** `completed`

## Session log (projection)

### [1] run.start

Input the Pipeline saw (ground truth excluded):

```json
{
  "case_id": "case_01",
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

### [2] llm.complete

```json
{
  "gaps_detected": [
    {
      "id": "gap_1",
      "description": "PR #42 'Add user auth flow' was merged on 2026-08-25 with 'Closes LIN-55' in the body, but Linear ticket LIN-55 remains in 'In Progress' state instead of being closed/completed. The ticket state was last updated on 2026-08-20, prior to the merge."
    }
  ],
  "usage": {
    "prompt_tokens": 336,
    "completion_tokens": 304,
    "total_tokens": 640
  }
}
```

### [3] run.end — `completed`

```json
{
  "case_id": "case_01",
  "gaps_detected": [
    {
      "id": "gap_1",
      "description": "PR #42 'Add user auth flow' was merged on 2026-08-25 with 'Closes LIN-55' in the body, but Linear ticket LIN-55 remains in 'In Progress' state instead of being closed/completed. The ticket state was last updated on 2026-08-20, prior to the merge."
    }
  ],
  "usage": {
    "prompt_tokens": 336,
    "completion_tokens": 304,
    "total_tokens": 640
  }
}
```

## Agent instructions used in this run

### Baseline — system prompt

```
You are a startup operations assistant.
You will be given a snapshot of a team's GitHub and Linear activity.
Your job is to identify gaps — discrepancies between the stated state
and the actual state of work across these tools.

A gap is any meaningful inconsistency, such as:
- A pull request that was merged but the corresponding ticket is still open
- A ticket marked Done but with open bugs still filed against it
- A feature branch that has been inactive for over 5 days with no linked ticket update

Respond with a JSON object in this exact format:
{
  "gaps_detected": [
    {"id": "gap_1", "description": "..."}
  ]
}

Only include real gaps you can identify from the data. Do not invent gaps.
```

All data in this trajectory is synthetic.