"""
Pipeline orchestrator — LangGraph StateGraph implementation.

Models the Forge Dispatch Workflow as a directed graph:

  sense → decide → (gaps?) → report → approve → save
                      ↓ (no gaps)
                     save

Nodes are agent phases. Edges are transitions.
Human-approval checkpoint is a graph interrupt, not a raw input() call.

Usage:
    python agents/pipeline.py --case eval/cases/case_01.json [--mock] [--auto-approve]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import sensing, reasoning, reporting


# ── Typed pipeline state ────────────────────────────────────────
# This is the shared state object that flows through every node.
# Each node reads what it needs and writes its output field.

class PipelineState(TypedDict, total=False):
    case: dict
    case_id: str
    mock: bool
    auto_approve: bool
    signals: dict
    gaps: list
    brief: str
    approved: bool
    result: dict


# ── Graph nodes ─────────────────────────────────────────────────

def sense_node(state: PipelineState) -> dict:
    """Sense phase: collect Signals from GitHub and Linear."""
    print("[ Sense ] Collecting Signals from GitHub and Linear...")
    output = sensing.run({"case": state["case"], "mock": state.get("mock", False)})
    signals = output["signals"]
    n_github = len(signals.get("github", {}).get("merged_prs", []))
    n_linear = len(signals.get("linear", {}).get("tickets", []))
    print(f"          ✓ {n_github} GitHub Signals, {n_linear} Linear Signals\n")
    return {"signals": signals}


def decide_node(state: PipelineState) -> dict:
    """Decide phase: cross-reference Signals to detect Gaps."""
    print("[ Decide ] Cross-referencing Signals for Gaps...")
    output = reasoning.run({"signals": state["signals"]})
    gaps = output["gaps"]
    print(f"           ✓ {len(gaps)} Gap(s) detected\n")
    return {"gaps": gaps}


def report_node(state: PipelineState) -> dict:
    """Act phase: convert Gaps into a human-readable Brief."""
    print("[ Act ] Generating Brief...")
    output = reporting.run({"gaps": state["gaps"]})
    brief = output["brief"]
    print(f"\n{brief}\n")
    return {"brief": brief}


def approve_node(state: PipelineState) -> dict:
    """Human-approval checkpoint. Blocks pipeline until approved."""
    if state.get("auto_approve"):
        return {"approved": True}

    print("─" * 60)
    answer = input("Approve this Brief for delivery? [y/N] ").strip().lower()
    if answer != "y":
        print("Brief not approved. Exiting without saving.")
        sys.exit(0)
    return {"approved": True}


def save_node(state: PipelineState) -> dict:
    """Persist results to eval/results/."""
    case_id = state["case_id"]
    gaps = state.get("gaps", [])
    brief = state.get("brief", "No gaps detected. No brief generated.")

    result = {
        "case_id": case_id,
        "gaps_detected": [{"id": g["id"], "description": g["description"]} for g in gaps],
        "brief": brief,
        "raw_gaps": gaps,
    }

    results_dir = Path(__file__).parent.parent / "eval" / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f"forge_{case_id}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n✓ Results saved to {out_path}")

    return {"result": result}


# ── Conditional edge ────────────────────────────────────────────

def should_report(state: PipelineState) -> str:
    """Skip reporting if no gaps were found."""
    if state.get("gaps"):
        return "report"
    print("           No gaps found, skipping Brief generation.\n")
    return "save"


# ── Build the graph ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("sense", sense_node)
    graph.add_node("decide", decide_node)
    graph.add_node("report", report_node)
    graph.add_node("approve", approve_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("sense")
    graph.add_edge("sense", "decide")
    graph.add_conditional_edges("decide", should_report, {"report": "report", "save": "save"})
    graph.add_edge("report", "approve")
    graph.add_edge("approve", "save")
    graph.add_edge("save", END)

    return graph.compile()


# ── Entry point ─────────────────────────────────────────────────

def run_pipeline(case_path: str, mock: bool = False, auto_approve: bool = False) -> dict:
    with open(case_path) as f:
        case = json.load(f)

    case_id = case["id"]
    print(f"\n{'='*60}")
    print(f"Forge Dispatch Pipeline (LangGraph)")
    print(f"Case: {case_id} | Mode: {'mock' if mock else 'live'}")
    print(f"{'='*60}\n")

    app = build_graph()
    final_state = app.invoke({
        "case": case,
        "case_id": case_id,
        "mock": mock,
        "auto_approve": auto_approve,
    })

    return final_state.get("result", {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Dispatch — LangGraph multi-agent Pipeline")
    parser.add_argument("--case", required=True, help="Path to case JSON file")
    parser.add_argument("--mock", action="store_true", help="Use mock_responses from case file")
    parser.add_argument("--auto-approve", action="store_true", help="Skip human approval (for eval runs)")
    args = parser.parse_args()

    run_pipeline(args.case, mock=args.mock, auto_approve=args.auto_approve)
