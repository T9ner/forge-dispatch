"""
Evaluation scorer — runs both the baseline and Forge Pipeline
over all 10 test cases and computes Gap detection rates,
false-positive rates, wall-clock time, and token usage.

Usage:
    python eval/score.py

Output:
    eval/results/baseline.json
    eval/results/forge.json
    Summary table printed to stdout
"""

import json
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


CASES_DIR = Path(__file__).parent / "cases"
RESULTS_DIR = Path(__file__).parent / "results"
REPO_ROOT = Path(__file__).parent.parent


def run_case_baseline(case_path: Path) -> tuple[dict, float]:
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "baseline" / "run.py"), "--case", str(case_path)],
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - start
    if result.returncode != 0:
        raise RuntimeError(f"Baseline failed on {case_path.name}:\n{result.stderr}")
    return json.loads(result.stdout), duration


def run_case_forge(case_path: Path) -> tuple[dict, float]:
    start = time.perf_counter()
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "agents" / "pipeline.py"),
            "--case", str(case_path),
            "--mock",
            "--auto-approve",
        ],
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - start
    if result.returncode != 0:
        raise RuntimeError(f"Forge pipeline failed on {case_path.name}:\n{result.stderr}")
    # pipeline.py writes results to file; load from there
    with open(case_path) as f:
        case = json.load(f)
    case_id = case["id"]
    result_path = RESULTS_DIR / f"forge_{case_id}.json"
    with open(result_path) as f:
        return json.load(f), duration


def detection_rate(detected_ids: list[str], ground_truth: list[dict]) -> float:
    gt_ids = {g["id"] for g in ground_truth}
    if not gt_ids:
        return 1.0
    hits = sum(1 for d in detected_ids if d in gt_ids)
    return hits / len(gt_ids)


def false_positive_rate(detected_ids: list[str], ground_truth: list[dict]) -> float:
    """Share of detected Gaps that do NOT match any ground-truth Gap."""
    if not detected_ids:
        return 0.0
    gt_ids = {g["id"] for g in ground_truth}
    false_positives = [d for d in detected_ids if d not in gt_ids]
    return len(false_positives) / len(detected_ids)


def _sum_usage(entries: list[dict]) -> dict:
    totals = {}
    for usage in entries:
        for key, value in (usage or {}).items():
            totals[key] = totals.get(key, 0) + value
    return totals


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    case_files = sorted(CASES_DIR.glob("case_*.json"))

    if not case_files:
        print("No case files found in eval/cases/. Run is complete with no cases.")
        return

    baseline_results = []
    forge_results = []

    print(f"\nRunning evaluation over {len(case_files)} cases...\n")
    print(f"{'Case':<10} {'GT':<4} {'Base rate':<10} {'Forge rate':<11} "
          f"{'Forge FP':<9} {'Base s':<8} {'Forge s':<8}")
    print("─" * 62)

    for case_path in case_files:
        with open(case_path) as f:
            case = json.load(f)

        gt = case.get("ground_truth_gaps", [])
        case_id = case["id"]

        try:
            b_result, b_duration = run_case_baseline(case_path)
            b_detected = [g["id"] for g in b_result.get("gaps_detected", [])]
            b_rate = detection_rate(b_detected, gt)
            b_fpr = false_positive_rate(b_detected, gt)
            b_usage = b_result.get("usage", {})
        except Exception as e:
            print(f"  [WARN] Baseline error on {case_id}: {e}")
            b_detected, b_rate, b_fpr, b_usage, b_duration = [], 0.0, 0.0, {}, 0.0

        try:
            f_result, f_duration = run_case_forge(case_path)
            f_detected = [g["id"] for g in f_result.get("gaps_detected", [])]
            f_rate = detection_rate(f_detected, gt)
            f_fpr = false_positive_rate(f_detected, gt)
            f_usage = f_result.get("usage", {})
        except Exception as e:
            print(f"  [WARN] Forge error on {case_id}: {e}")
            f_detected, f_rate, f_fpr, f_usage, f_duration = [], 0.0, 0.0, {}, 0.0

        baseline_results.append({
            "case_id": case_id,
            "detection_rate": b_rate,
            "false_positive_rate": b_fpr,
            "duration_sec": round(b_duration, 2),
            "usage": b_usage,
            "detected": b_detected,
            "ground_truth": gt,
        })
        forge_results.append({
            "case_id": case_id,
            "detection_rate": f_rate,
            "false_positive_rate": f_fpr,
            "duration_sec": round(f_duration, 2),
            "usage": f_usage,
            "detected": f_detected,
            "ground_truth": gt,
        })

        print(f"{case_id:<10} {len(gt):<4} {b_rate:<10.0%} {f_rate:<11.0%} "
              f"{f_fpr:<9.0%} {b_duration:<8.1f} {f_duration:<8.1f}")

    # Aggregate
    n = len(case_files)
    b_avg = sum(r["detection_rate"] for r in baseline_results) / n
    f_avg = sum(r["detection_rate"] for r in forge_results) / n
    b_fpr_avg = sum(r["false_positive_rate"] for r in baseline_results) / n
    f_fpr_avg = sum(r["false_positive_rate"] for r in forge_results) / n
    b_time = sum(r["duration_sec"] for r in baseline_results) / n
    f_time = sum(r["duration_sec"] for r in forge_results) / n
    b_tokens = _sum_usage([r["usage"] for r in baseline_results])
    f_tokens = _sum_usage([r["usage"] for r in forge_results])

    print("─" * 62)
    print(f"{'AVERAGE':<10} {'':<4} {b_avg:<10.0%} {f_avg:<11.0%} "
          f"{f_fpr_avg:<9.0%} {b_time:<8.1f} {f_time:<8.1f}")
    print(f"\nDetection rate: {b_avg:.0%} → {f_avg:.0%} ({(f_avg - b_avg):+.0%})")
    print(f"False positive rate: {b_fpr_avg:.0%} → {f_fpr_avg:.0%}")
    print(f"Avg time per case: baseline {b_time:.1f}s | forge {f_time:.1f}s")
    print(f"Total tokens: baseline {b_tokens.get('total_tokens', 0)} | "
          f"forge {f_tokens.get('total_tokens', 0)}\n")

    # Write result files
    with open(RESULTS_DIR / "baseline.json", "w") as f:
        json.dump({
            "avg_detection_rate": b_avg,
            "avg_false_positive_rate": b_fpr_avg,
            "avg_duration_sec": round(b_time, 2),
            "total_usage": b_tokens,
            "cases": baseline_results,
        }, f, indent=2)

    with open(RESULTS_DIR / "forge.json", "w") as f:
        json.dump({
            "avg_detection_rate": f_avg,
            "avg_false_positive_rate": f_fpr_avg,
            "avg_duration_sec": round(f_time, 2),
            "total_usage": f_tokens,
            "cases": forge_results,
        }, f, indent=2)

    print(f"Results written to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
