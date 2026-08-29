"""
Reasoning Agent — Decide phase.

Cross-references GitHub and Linear Signals to detect Gaps.
Uses GPT-4o with structured output.

Public interface:
    run(context: dict) -> dict
    context keys: signals (dict from Sensing Agent)
    returns: {"gaps": [...]}
"""

import json

from agents.llm import get_client, get_model


SYSTEM_PROMPT = """You are Forge's reasoning engine.

You receive structured Signals from two Systems:
- GitHub: merged pull requests and open issues
- Linear: project management tickets and their states

Your job is to detect Gaps — meaningful discrepancies between the stated
state and the actual state of work across these Systems.

Examples of Gaps to detect:
1. A PR was merged but the linked Linear ticket is still "In Progress" or "Todo"
2. A ticket is marked "Done" in Linear but GitHub still has open bug issues referencing it
3. A PR title or body references a ticket ID that does not exist in Linear
4. A Linear ticket is marked "Done" but its linked PR was never merged

Rules:
- Only identify Gaps you can substantiate from the provided data
- Each Gap must reference specific evidence (PR number, ticket ID, etc.)
- Do not invent Gaps or speculate beyond the data given
- A "linked" relationship is established when: a PR body/title contains a ticket ID
  (e.g. "LIN-123", "Fixes #123"), or a ticket's title matches a PR title closely

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
"""


def run(context: dict) -> dict:
    """
    Decide phase: cross-reference Signals to produce a list of Gaps.

    Args:
        context: {"signals": {"github": {...}, "linear": {...}}}

    Returns:
        {"gaps": [...]}
    """
    signals = context["signals"]
    client = get_client()

    payload = json.dumps(signals, indent=2)

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here are the Signals:\n\n{payload}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    return {"gaps": parsed.get("gaps", [])}
