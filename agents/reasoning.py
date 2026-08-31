"""
Reasoning Agent — Decide phase.

Cross-references GitHub and Linear Signals to detect Gaps.
Uses the shared OpenRouter client with JSON structured output.

Public interface:
    run(context: dict) -> dict
    context keys: signals (dict from Sensing Agent)
    returns: {"gaps": [...]}
"""

import json
import re

from agents.llm import chat, get_client, get_model, usage_of


SYSTEM_PROMPT = """You are Forge's reasoning engine.

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
"""


# Strategy pattern: fence extraction tries code-block then raw JSON, then falls
# back to empty gaps — avoids crashing on malformed model output.
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> str:
    """Extract the JSON payload from a model response.

    Tries three strategies in order:
    1. Content inside a markdown code fence (```json ... ```)
    2. First {...} block in the raw text
    3. The stripped text itself (already plain JSON)
    """
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    m = _JSON_RE.search(text)
    if m:
        return m.group(0).strip()
    return text.strip()


def run(context: dict) -> dict:
    """Decide phase: cross-reference Signals to produce a list of Gaps.

    Args:
        context: {"signals": {"github": {...}, "linear": {...}}}

    Returns:
        {"gaps": [...], "usage": {...}}
    """
    signals = context["signals"]
    client = get_client()

    payload = json.dumps(signals, indent=2)

    response = chat(
        client,
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here are the Signals:\n\n{payload}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = (response.choices[0].message.content or "").strip()
    candidate = _extract_json(raw)
    if not candidate:
        # Model returned empty or unparseable output; treat as no gaps found.
        return {"gaps": [], "usage": usage_of(response)}
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        # Fallback: treat parse failure as no gaps rather than crashing.
        return {"gaps": [], "usage": usage_of(response)}

    return {"gaps": parsed.get("gaps", []), "usage": usage_of(response)}
