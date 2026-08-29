"""
Evaluation scorer — runs both the baseline and Forge Pipeline
over all 10 test cases and computes Gap detection rates.

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
from pathlib import Path


CASES_DIR = Path(__file__).parent / "cases"
RESULTS_DIR = Path(__file__).parent / "results"
REPO_ROOT = Path(__file__).parent.parent


def run_case_baseline(case_path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "baseline" / "run.py"), "--case", str(case_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Baseline failed on {case_path.name}:\n{result.stderr}")
    return json.loads(result.stdout)


def run_case_forge(case_path: Path) -> dict:
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
    if result.returncode != 0:
        raise RuntimeError(f"Forge pipeline failed on {case_path.name}:\n{result.stderr}")
    # pipeline.py writes results to file; load from there
    with open(case_path) as f:
        case = json.load(f)
    case_id = case["id"]
    result_path = RESULTS_DIR / f"forge_{case_id}.json"
    with open(result_path) as f:
        return json.load(f)


def detection_rate(detected_ids: list[str], ground_truth: list[dict]) -> float:
    gt_ids = {g["id"] for g in ground_truth}
    if not gt_ids:
        return 1.0
    hits = sum(1 for d in detected_ids if d in gt_ids)
    return hits / len(gt_ids)


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    case_files = sorted(CASES_DIR.glob("case_*.json"))

    if not case_files:
        print("No case files found in eval/cases/. Run is complete with no cases.")
        return

    baseline_results = []
    forge_results = []

    print(f"\nRunning evaluation over {len(case_files)} cases...\n")
    print(f"{'Case':<12} {'GT Gaps':<10} {'Baseline':<12} {'Forge':<10}")
    print("─" * 46)

    for case_path in case_files:
        with open(case_path) as f:
            case = json.load(f)

        gt = case.get("ground_truth_gaps", [])
        case_id = case["id"]

        try:
            b_result = run_case_baseline(case_path)
            b_detected = [g["id"] for g in b_result.get("gaps_detected", [])]
            b_rate = detection_rate(b_detected, gt)
        except Exception as e:
            print(f"  [WARN] Baseline error on {case_id}: {e}")
            b_detected, b_rate = [], 0.0

        try:
            f_result = run_case_forge(case_path)
            f_detected = [g["id"] for g in f_result.get("gaps_detected", [])]
            f_rate = detection_rate(f_detected, gt)
        except Exception as e:
            print(f"  [WARN] Forge error on {case_id}: {e}")
            f_detected, f_rate = [], 0.0

        baseline_results.append({"case_id": case_id, "detection_rate": b_rate, "detected": b_detected, "ground_truth": gt})
        forge_results.append({"case_id": case_id, "detection_rate": f_rate, "detected": f_detected, "ground_truth": gt})

        print(f"{case_id:<12} {len(gt):<10} {b_rate:<12.0%} {f_rate:<10.0%}")

    # Aggregate
    b_avg = sum(r["detection_rate"] for r in baseline_results) / len(baseline_results)
    f_avg = sum(r["detection_rate"] for r in forge_results) / len(forge_results)

    print("─" * 46)
    print(f"{'AVERAGE':<12} {'':<10} {b_avg:<12.0%} {f_avg:<10.0%}")
    print(f"\nImprovement: {(f_avg - b_avg):+.0%} ({b_avg:.0%} → {f_avg:.0%})\n")

    # Write result files
    with open(RESULTS_DIR / "baseline.json", "w") as f:
        json.dump({"avg_detection_rate": b_avg, "cases": baseline_results}, f, indent=2)

    with open(RESULTS_DIR / "forge.json", "w") as f:
        json.dump({"avg_detection_rate": f_avg, "cases": forge_results}, f, indent=2)

    print(f"Results written to eval/results/")


if __name__ == "__main__":
    main()
