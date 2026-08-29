"""
Pipeline orchestrator — runs the three-Agent Forge Dispatch Workflow:
  Sensing → Reasoning → Reporting

Includes a human-approval checkpoint before Brief delivery.

Usage:
    python agents/pipeline.py --case eval/cases/case_01.json [--mock] [--auto-approve]
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Add repo root to path so agents can be imported cleanly
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import sensing, reasoning, reporting


def run_pipeline(case_path: str, mock: bool = False, auto_approve: bool = False) -> dict:
    with open(case_path) as f:
        case = json.load(f)

    case_id = case["id"]
    print(f"\n{'='*60}")
    print(f"Forge Dispatch Pipeline — Case: {case_id}")
    print(f"Mode: {'mock' if mock else 'live'}")
    print(f"{'='*60}\n")

    # ── Phase 1: Sense ──────────────────────────────────────────
    print("[ Sense ] Collecting Signals from GitHub and Linear...")
    sensing_output = sensing.run({"case": case, "mock": mock})
    n_github = len(sensing_output["signals"].get("github", {}).get("merged_prs", []))
    n_linear = len(sensing_output["signals"].get("linear", {}).get("tickets", []))
    print(f"          ✓ {n_github} GitHub Signals, {n_linear} Linear Signals\n")

    # ── Phase 2: Decide ─────────────────────────────────────────
    print("[ Decide ] Cross-referencing Signals for Gaps...")
    reasoning_output = reasoning.run({"signals": sensing_output["signals"]})
    gaps = reasoning_output["gaps"]
    print(f"           ✓ {len(gaps)} Gap(s) detected\n")

    # ── Phase 3: Act ────────────────────────────────────────────
    print("[ Act ] Generating Brief...")
    reporting_output = reporting.run({"gaps": gaps})
    brief = reporting_output["brief"]
    print()
    print(brief)
    print()

    # ── Human Approval Checkpoint ───────────────────────────────
    if not auto_approve:
        print("─" * 60)
        answer = input("Approve this Brief for delivery? [y/N] ").strip().lower()
        if answer != "y":
            print("Brief not approved. Exiting without saving.")
            sys.exit(0)

    result = {
        "case_id": case_id,
        "gaps_detected": [{"id": g["id"], "description": g["description"]} for g in gaps],
        "brief": brief,
        "raw_gaps": gaps,
    }

    # Write results
    results_dir = Path(__file__).parent.parent / "eval" / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f"forge_{case_id}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n✓ Results saved to {out_path}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Dispatch — multi-agent Pipeline")
    parser.add_argument("--case", required=True, help="Path to case JSON file")
    parser.add_argument("--mock", action="store_true", help="Use mock_responses from case file")
    parser.add_argument("--auto-approve", action="store_true", help="Skip human approval (for eval runs)")
    args = parser.parse_args()

    run_pipeline(args.case, mock=args.mock, auto_approve=args.auto_approve)
