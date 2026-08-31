"""
Baseline agent — single LLM prompt with pre-fetched context.
No live API calls. Uses mock_responses from the case file.

Usage:
    python baseline/run.py --case eval/cases/case_01.json
    python baseline/run.py --case eval/cases/case_01.json \
        --trace trajectories/baseline_case_01
"""

import argparse
import json
import re
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

# Ensure agents/ is importable for llm.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.llm import chat, get_client, get_model, usage_of
from agents.trace import new_baseline_log, write_session_log

load_dotenv()


SYSTEM_PROMPT = """You are a startup operations assistant.
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

Only include real gaps you can identify from the data. Do not invent gaps."""


# Strategy pattern: same approach as reasoning.py — fence → raw JSON → stripped text
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


def build_context(case: dict) -> str:
    """Format mock GitHub and Linear data from the case into a structured prompt context."""
    github = case["mock_responses"]["github"]
    linear = case["mock_responses"]["linear"]
    return (
        f"=== GitHub Data ===\n{json.dumps(github, indent=2)}\n\n"
        f"=== Linear Data ===\n{json.dumps(linear, indent=2)}"
    )


def run_baseline(case_path: str, trace_path: str | None = None) -> dict:
    """Run the single-prompt baseline agent on a single case with optional session logging."""
    with open(case_path) as f:
        case = json.load(f)

    log = new_baseline_log(case) if trace_path else None
    if log is not None:
        log.run_start()

    client = get_client()
    context = build_context(case)

    response = chat(
        client,
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = (response.choices[0].message.content or "").strip()
    candidate = _extract_json(raw)
    try:
        parsed = json.loads(candidate) if candidate else {}
    except json.JSONDecodeError:
        parsed = {}

    result = {
        "case_id": case["id"],
        "gaps_detected": parsed.get("gaps_detected", []),
        "usage": usage_of(response),
        "raw_response": raw,
    }

    if log is not None:
        log.llm_complete({
            "gaps_detected": result["gaps_detected"],
            "usage": result["usage"],
        })
        log.finish(outcome="completed", result={
            "case_id": result["case_id"],
            "gaps_detected": result["gaps_detected"],
            "usage": result["usage"],
        })
        json_path, md_path = write_session_log(
            trace_path,
            log,
            agent_prompts={"Baseline — system prompt": SYSTEM_PROMPT},
        )
        print(f"Session log written to {json_path}", file=sys.stderr)
        print(f"Trajectory projection written to {md_path}", file=sys.stderr)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Dispatch — baseline agent")
    parser.add_argument("--case", required=True, help="Path to case JSON file")
    parser.add_argument("--trace", default=None,
                        help="Write DSH-inspired session log (.json) + markdown projection (.md)")
    args = parser.parse_args()

    result = run_baseline(args.case, trace_path=args.trace)
    print(json.dumps(result, indent=2))
