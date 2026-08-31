"""
Pipeline orchestrator — LangGraph StateGraph implementation.

Models the Forge Dispatch Workflow as a directed graph:

  sense → decide → (gaps?) → report → approve → (approved?) → save
                      ↓ (no gaps)               ↓ (refused)
                     save                       END

Nodes are agent phases; edges are transitions. The human-approval
checkpoint is a real LangGraph interrupt(): the graph pauses at
APPROVE and surfaces the Brief, the CLI collects the reviewer's
y/N decision, and the graph resumes. A refusal ends the run without
saving. --auto-approve (used by all evaluation runs) bypasses the
checkpoint entirely.

Usage:
    python agents/pipeline.py --case eval/cases/case_01.json [--mock]
        [--auto-approve] [--trace trajectories/run]

--trace writes a canonical session log (.json) and a
markdown projection (.md). See trajectories/SCHEMA.md.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.types import Command, interrupt

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import reasoning, reporting, sensing
from agents.trace import (
    infer_outcome,
    new_pipeline_log,
    write_session_log,
)


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
    usage_reasoning: dict
    usage_reporting: dict
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
    return {"gaps": gaps, "usage_reasoning": output.get("usage", {})}


def report_node(state: PipelineState) -> dict:
    """Act phase: convert Gaps into a human-readable Brief."""
    print("[ Act ] Generating Brief...")
    output = reporting.run({"gaps": state["gaps"]})
    brief = output["brief"]
    print(f"\n{brief}\n")
    return {"brief": brief, "usage_reporting": output.get("usage", {})}


def approve_node(state: PipelineState) -> dict:
    """Human-approval checkpoint — a real LangGraph interrupt.

    Auto-approve runs (evaluation) skip the checkpoint. Interactive
    runs pause the graph here; the CLI resumes it with the
    reviewer's decision.
    """
    if state.get("auto_approve"):
        return {"approved": True}

    decision = interrupt({
        "prompt": "Approve this Brief for delivery? [y/N]",
        "case_id": state["case_id"],
        "n_gaps": len(state.get("gaps", [])),
    })
    return {"approved": bool(decision)}


def save_node(state: PipelineState) -> dict:
    """Persist results to eval/results/."""
    case_id = state["case_id"]
    gaps = state.get("gaps", [])
    brief = state.get("brief", "No gaps detected. No brief generated.")

    usage = _sum_usage(state.get("usage_reasoning"), state.get("usage_reporting"))

    result = {
        "case_id": case_id,
        "gaps_detected": [{"id": g["id"], "description": g["description"]} for g in gaps],
        "brief": brief,
        "raw_gaps": gaps,
    }
    if usage:
        result["usage"] = usage

    results_dir = Path(__file__).parent.parent / "eval" / "results"
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f"forge_{case_id}.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n✓ Results saved to {out_path}")

    return {"result": result}


def _sum_usage(*usage_dicts) -> dict:
    """Sum token counts across usage dicts, ignoring empty ones."""
    totals = {}
    for usage in usage_dicts:
        for key, value in (usage or {}).items():
            totals[key] = totals.get(key, 0) + value
    return totals


# ── Conditional edges ───────────────────────────────────────────

def should_report(state: PipelineState) -> str:
    """Skip reporting if no gaps were found."""
    if state.get("gaps"):
        return "report"
    print("           No gaps found, skipping Brief generation.\n")
    return "save"


def should_save(state: PipelineState) -> str:
    """Persist results only on approval; refusal ends the run."""
    return "save" if state.get("approved") else "end"


# ── Build the graph ─────────────────────────────────────────────

def build_graph(checkpointer=None):
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
    graph.add_conditional_edges("approve", should_save, {"save": "save", "end": END})
    graph.add_edge("save", END)

    return graph.compile(checkpointer=checkpointer)


# ── Execution with interrupt handling + optional tracing ────────

def _record_node(log, node: str, delta: dict, run_input: dict) -> None:
    """Log a node completion and infer conditional-edge routes."""
    if log is None:
        return
    log.node_complete(node, delta)
    if node == "decide" and not delta.get("gaps"):
        log.edge_route("decide→?", "save", "no_gaps")
    elif node == "decide" and delta.get("gaps"):
        log.edge_route("decide→?", "report", "gaps_found")
    elif node == "approve":
        if run_input.get("auto_approve"):
            log.checkpoint_skip("auto_approve")
        elif delta.get("approved"):
            log.edge_route("approve→?", "save", "approved")
        else:
            log.edge_route("approve→?", "end", "refused")


def _execute(app, run_input: dict, config: dict, log) -> dict:
    """Stream the graph to completion, pausing at the approval
    interrupt for a terminal y/N decision. Returns the merged state.
    """
    pending = run_input
    merged_state: dict = {}

    if log is not None:
        log.run_start()

    while True:
        interrupted = False
        for chunk in app.stream(pending, config=config, stream_mode="updates"):
            for node, delta in chunk.items():
                if node == "__interrupt__":
                    interrupted = True
                    payload = delta[0].value
                    if log is not None:
                        log.checkpoint_interrupt(payload)
                    print("─" * 60)
                    answer = input(f"{payload['prompt']} ").strip().lower()
                    approved = answer == "y"
                    if log is not None:
                        log.checkpoint_resume(approved)
                    if not approved:
                        print("Brief not approved. Nothing will be saved.")
                        if log is not None:
                            log.edge_route("approve→?", "end", "refused")
                    pending = Command(resume=approved)
                else:
                    _record_node(log, node, delta, run_input)
                    merged_state.update(delta)
        if not interrupted:
            return merged_state


def _agent_prompts() -> dict[str, str]:
    return {
        "Reasoning Agent (Decide phase) — system prompt": reasoning.SYSTEM_PROMPT,
        "Reporting Agent (Act phase) — system prompt": reporting.SYSTEM_PROMPT,
        "Sensing Agent (Sense phase)": (
            "No LLM prompt — collects raw Signals from the GitHub REST API and "
            "Linear GraphQL API (or from the case file's mock_responses in mock mode). "
            "See agents/sensing.py."
        ),
    }


# ── Entry point ─────────────────────────────────────────────────

def run_pipeline(case_path: str, mock: bool = False, auto_approve: bool = False,
                 trace_path: str = None) -> dict:
    with open(case_path) as f:
        case = json.load(f)

    case_id = case["id"]
    print(f"\n{'='*60}")
    print(f"Forge Dispatch Pipeline (LangGraph)")
    print(f"Case: {case_id} | Mode: {'mock' if mock else 'live'}")
    print(f"{'='*60}\n")

    app = build_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": f"forge-{case_id}"}}

    log = new_pipeline_log(case, mock, auto_approve) if trace_path else None

    run_input = {
        "case": case,
        "case_id": case_id,
        "mock": mock,
        "auto_approve": auto_approve,
    }

    final_state = _execute(app, run_input, config, log)

    if log is not None:
        outcome = infer_outcome(final_state)
        log.finish(outcome=outcome, result=final_state.get("result"))
        json_path, md_path = write_session_log(
            trace_path,
            log,
            agent_prompts=_agent_prompts(),
        )
        print(f"\n✓ Session log written to {json_path}")
        print(f"✓ Trajectory projection written to {md_path}")

    return final_state.get("result", {})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forge Dispatch — LangGraph multi-agent Pipeline")
    parser.add_argument("--case", required=True, help="Path to case JSON file")
    parser.add_argument("--mock", action="store_true", help="Use mock_responses from case file")
    parser.add_argument("--auto-approve", action="store_true", help="Skip human approval (for eval runs)")
    parser.add_argument("--trace", default=None,
                        help="Write canonical session log (.json) + markdown projection (.md)")
    args = parser.parse_args()

    run_pipeline(args.case, mock=args.mock, auto_approve=args.auto_approve, trace_path=args.trace)
