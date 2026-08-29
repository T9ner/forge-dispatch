"""
Reporting Agent — Act phase.

Converts detected Gaps into a plain-language Brief
that a founder or ops lead can read and act on immediately.

Public interface:
    run(context: dict) -> dict
    context keys: gaps (list from Reasoning Agent)
    returns: {"brief": str}
"""

import json
import os

from openai import OpenAI


SYSTEM_PROMPT = """You are Forge's reporting engine.

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
"""


def run(context: dict) -> dict:
    """
    Act phase: convert Gaps into a human-readable Brief.

    Args:
        context: {"gaps": [...]}

    Returns:
        {"brief": "<plain-text Brief>"}
    """
    gaps = context["gaps"]
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    from datetime import date
    today = date.today().strftime("%B %d, %Y")

    prompt = SYSTEM_PROMPT.replace("{today}", today).replace("{n}", str(len(gaps)))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Here are the detected Gaps:\n\n{json.dumps(gaps, indent=2)}",
            },
        ],
        temperature=0.3,
    )

    brief = response.choices[0].message.content
    return {"brief": brief}
