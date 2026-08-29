"""
Baseline agent — single GPT-4o prompt with pre-fetched context.
No live API calls. Uses mock_responses from the case file.

Usage:
    python baseline/run.py --case eval/cases/case_01.json
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

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


def build_context(case: dict) -> str:
    github = case["mock_responses"]["github"]
    linear = case["mock_responses"]["linear"]
    return (
        f"=== GitHub Data ===\n{json.dumps(github, indent=2)}\n\n"
        f"=== Linear Data ===\n{json.dumps(linear, indent=2)}"
    )


def run_baseline(case_path: str) -> dict:
    with open(case_path) as f:
        case = json.load(f)

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    context = build_context(case)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    return {
        "case_id": case["id"],
        "gaps_detected": parsed.get("gaps_detected", []),
        "raw_response": raw,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Dispatch — baseline agent")
    parser.add_argument("--case", required=True, help="Path to case JSON file")
    args = parser.parse_args()

    result = run_baseline(args.case)
    print(json.dumps(result, indent=2))
