"""
Canonical session log engine for Forge Dispatch runs.

Treats the append-only session log as the canonical record of a run;
human-readable Markdown trajectories are projections from that event stream.

  *.json  - canonical, machine-readable session log (reconstructable)
  *.md    - human-readable projection for review

See trajectories/SCHEMA.md for the event vocabulary.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = "1.0"

GRAPH_TOPOLOGY = (
    "sense → decide → (gaps?) → report → approve → (approved?) → save | END"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trace_input(case: dict, mock: bool, auto_approve: bool) -> dict:
    """Pipeline-visible input only — ground truth is excluded."""
    return {
        "case_id": case.get("id"),
        "mock": mock,
        "auto_approve": auto_approve,
        "mock_responses": case.get("mock_responses"),
    }


def pipeline_composition(case_id: str, mock: bool, auto_approve: bool) -> dict:
    """Composition manifest — pins the runtime tuple for reproducibility."""
    from agents.llm import get_model, get_provider

    return {
        "pipeline": "forge-dispatch",
        "runner": "langgraph",
        "graph": GRAPH_TOPOLOGY,
        "model": get_model(),
        "provider": get_provider(),
        "checkpoint": "MemorySaver",
        "thread_id": f"forge-{case_id}",
        "mock": mock,
        "auto_approve": auto_approve,
    }


def baseline_composition(case_id: str) -> dict:
    from agents.llm import get_model, get_provider

    return {
        "pipeline": "forge-dispatch-baseline",
        "runner": "single-shot",
        "model": get_model(),
        "provider": get_provider(),
        "case_id": case_id,
    }


class SessionLog:
    """Append-only session log with monotonic sequence numbers."""

    def __init__(self, *, run_id: str, composition: dict, run_input: dict):
        self.run_id = run_id
        self.composition = composition
        self.run_input = run_input
        self.started_at = _now()
        self.ended_at: str | None = None
        self.outcome: str | None = None
        self.result: dict | None = None
        self.events: list[dict] = []
        self._seq = 0

    def _append(self, event_type: str, payload: dict) -> None:
        self._seq += 1
        self.events.append({
            "seq": self._seq,
            "type": event_type,
            "ts": _now(),
            "payload": payload,
        })

    def record_legacy(self, event: dict) -> None:
        """Adapt legacy stream events into the session log vocabulary."""
        kind = event["event"]
        if kind == "invoke":
            self._append("run.start", {"input": event["value"]})
        elif kind == "node":
            self._append("node.complete", {
                "node": event["node"],
                "output": event["output"],
            })
        elif kind == "interrupt":
            self._append("checkpoint.interrupt", event["value"])
        elif kind == "resume":
            self._append("checkpoint.resume", {"approved": event["value"]})
        elif kind == "checkpoint.skip":
            self._append("checkpoint.skip", event["value"])
        elif kind == "edge.route":
            self._append("edge.route", event["value"])

    def node_complete(self, node: str, output: dict) -> None:
        self._append("node.complete", {"node": node, "output": output})

    def edge_route(self, edge: str, target: str, reason: str) -> None:
        self._append("edge.route", {"edge": edge, "target": target, "reason": reason})

    def checkpoint_interrupt(self, payload: dict) -> None:
        self._append("checkpoint.interrupt", payload)

    def checkpoint_resume(self, approved: bool) -> None:
        self._append("checkpoint.resume", {"approved": approved})

    def checkpoint_skip(self, reason: str) -> None:
        self._append("checkpoint.skip", {"reason": reason})

    def llm_complete(self, payload: dict) -> None:
        self._append("llm.complete", payload)

    def run_start(self) -> None:
        self._append("run.start", {"input": self.run_input})

    def finish(self, *, outcome: str, result: dict | None = None) -> None:
        self.ended_at = _now()
        self.outcome = outcome
        self.result = result
        self._append("run.end", {"outcome": outcome, "result": result})

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "outcome": self.outcome,
            "composition": self.composition,
            "input": self.run_input,
            "events": self.events,
        }


def new_pipeline_log(case: dict, mock: bool, auto_approve: bool) -> SessionLog:
    case_id = case["id"]
    return SessionLog(
        run_id=f"forge-{case_id}-{uuid4().hex[:8]}",
        composition=pipeline_composition(case_id, mock, auto_approve),
        run_input=_trace_input(case, mock, auto_approve),
    )


def new_baseline_log(case: dict) -> SessionLog:
    case_id = case["id"]
    return SessionLog(
        run_id=f"baseline-{case_id}-{uuid4().hex[:8]}",
        composition=baseline_composition(case_id),
        run_input={
            "case_id": case_id,
            "mock_responses": case.get("mock_responses"),
        },
    )


def resolve_trace_paths(trace_path: str) -> tuple[Path, Path]:
    """Return (json_path, md_path) for a --trace argument."""
    path = Path(trace_path)
    if path.suffix.lower() == ".md":
        return path.with_suffix(".json"), path
    if path.suffix.lower() == ".json":
        return path, path.with_suffix(".md")
    return path.with_suffix(".json"), path.with_suffix(".md")


def write_session_log(
    trace_path: str,
    log: SessionLog,
    *,
    agent_prompts: dict[str, str] | None = None,
) -> tuple[Path, Path]:
    """Write canonical JSON and markdown projection. Returns both paths."""
    json_path, md_path = resolve_trace_paths(trace_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(log.to_dict(), f, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(log, agent_prompts=agent_prompts))

    return json_path, md_path


def render_markdown(log: SessionLog, *, agent_prompts: dict[str, str] | None = None) -> str:
    """Project a session log into a judge-readable markdown trajectory."""
    comp = log.composition
    lines = [
        "# Agent Trajectory — Forge Dispatch",
        "",
        f"- **Run ID:** `{log.run_id}`",
        f"- **Schema:** `{SCHEMA_VERSION}` (Canonical session log — see `trajectories/SCHEMA.md`)",
        f"- **Pipeline:** `{comp.get('pipeline', 'unknown')}`",
        f"- **Case:** `{log.run_input.get('case_id', comp.get('case_id', 'unknown'))}`",
        f"- **Model:** `{comp.get('model', 'unknown')}` via `{comp.get('provider', 'unknown')}`",
    ]

    if comp.get("runner") == "langgraph":
        lines += [
            f"- **Mode:** {'mock' if comp.get('mock') else 'live'}",
            f"- **Auto-approve:** {comp.get('auto_approve')}",
            f"- **Graph:** `{comp.get('graph', GRAPH_TOPOLOGY)}`",
            f"- **Thread:** `{comp.get('thread_id', 'n/a')}`",
        ]

    if log.outcome:
        lines.append(f"- **Outcome:** `{log.outcome}`")

    lines += ["", "## Session log (projection)", ""]

    for event in log.events:
        etype = event["type"]
        payload = event["payload"]
        seq = event["seq"]

        if etype == "run.start":
            lines += [
                f"### [{seq}] run.start",
                "",
                "Input the Pipeline saw (ground truth excluded):",
                "",
                "```json",
                json.dumps(payload.get("input", {}), indent=2),
                "```",
                "",
            ]
        elif etype == "node.complete":
            node = payload.get("node", "?")
            lines += [
                f"### [{seq}] node.complete — `{node}`",
                "",
                "```json",
                json.dumps(payload.get("output", {}), indent=2),
                "```",
                "",
            ]
        elif etype == "edge.route":
            lines += [
                f"### [{seq}] edge.route",
                "",
                f"**{payload.get('edge')}** → `{payload.get('target')}`",
                "",
            ]
        elif etype == "checkpoint.interrupt":
            lines += [
                f"### [{seq}] checkpoint.interrupt",
                "",
                "Graph paused at APPROVE (LangGraph `interrupt()`):",
                "",
                "```json",
                json.dumps(payload, indent=2),
                "```",
                "",
            ]
        elif etype == "checkpoint.resume":
            approved = payload.get("approved")
            lines += [
                f"### [{seq}] checkpoint.resume — **{'approved' if approved else 'refused'}**",
                "",
            ]
        elif etype == "checkpoint.skip":
            lines += [
                f"### [{seq}] checkpoint.skip",
                "",
                f"Reason: `{payload.get('reason', 'unknown')}`",
                "",
            ]
        elif etype == "llm.complete":
            lines += [
                f"### [{seq}] llm.complete",
                "",
                "```json",
                json.dumps(payload, indent=2),
                "```",
                "",
            ]
        elif etype == "run.end":
            lines += [
                f"### [{seq}] run.end — `{payload.get('outcome', 'unknown')}`",
                "",
            ]
            if payload.get("result"):
                lines += [
                    "```json",
                    json.dumps(payload["result"], indent=2),
                    "```",
                    "",
                ]

    if agent_prompts:
        lines += ["## Agent instructions used in this run", ""]
        for title, prompt in agent_prompts.items():
            lines += [f"### {title}", "", "```", prompt.strip(), "```", ""]

    lines.append("All data in this trajectory is synthetic.")
    return "\n".join(lines)


def infer_outcome(final_state: dict) -> str:
    """Derive run outcome from merged pipeline state."""
    if final_state.get("result"):
        return "saved"
    if final_state.get("approved") is False:
        return "refused"
    if final_state.get("gaps") == [] and "brief" not in final_state:
        return "no_gaps_saved"
    return "ended"
