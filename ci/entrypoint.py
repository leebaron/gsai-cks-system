#!/usr/bin/env python3
"""
ci/entrypoint.py — Production CI entry point for CKS system.

Orchestrates the full execution pipeline:
  runtime → replay → consensus → hash → formal → deploy | reject

Usage:
    python ci/entrypoint.py [--commit <sha>]

Exit code:
    0 — ALL GATES PASS (deploy)
    1 — ANY GATE FAILS (reject/rollback)
"""
import sys, json, time, hashlib, subprocess, os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_step(name: str, cmd: list, timeout: int = 30) -> dict:
    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=timeout,
        )
        return {
            "step": name,
            "exit_code": result.returncode,
            "pass": result.returncode == 0,
            "duration_s": round(time.time() - start, 2),
            "stdout": result.stdout.strip()[-200:],
            "stderr": result.stderr.strip()[-200:],
        }
    except subprocess.TimeoutExpired:
        return {"step": name, "exit_code": -1, "pass": False, "duration_s": timeout, "error": "TIMEOUT"}
    except FileNotFoundError:
        return {"step": name, "exit_code": -2, "pass": False, "error": "CMD_NOT_FOUND"}


def run() -> dict:
    # Clean stale node reports from previous runs
    for f in (REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact").glob("node_report_*.json"):
        f.unlink()

    results = []

    # Step 1: pytest
    results.append(run_step("pytest", ["python3", "-m", "pytest", "-q", "tests/"]))

    # Step 2: ROEL gate
    roel_in = "VIEW_STATE: COMPLETE\nCI entrypoint test.\n"
    try:
        r = subprocess.run(
            ["python3", "roel.py"], input=roel_in,
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        results.append({"step": "roel_gate", "exit_code": r.returncode, "pass": r.returncode == 0})
    except:
        results.append({"step": "roel_gate", "exit_code": -1, "pass": False})

    # Step 3: Consensus nodes (simulated 3-node agreement)
    for nid in ["node-a", "node-b", "node-c"]:
        r = run_step(f"consensus_{nid}", ["python3", "tools/consensus_node.py", "--node-id", nid])
        results.append(r)

    # Step 4: Consensus aggregation
    results.append(run_step("consensus_aggregate", ["python3", "tools/consensus_aggregator.py", str(REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact")]))

    # Step 5: Formal verification
    results.append(run_step("formal_check", ["python3", "formal/verify_model.py"]))

    # Step 6: Hash binding
    results.append(run_step("hash_verify", ["python3", "tools/verify_chain.py"]))

    # Decision
    all_pass = all(r.get("pass") for r in results)
    total = len(results)
    passed = sum(1 for r in results if r.get("pass"))

    report = {
        "system_valid": all_pass,
        "steps_passed": passed,
        "steps_total": total,
        "pipeline": results,
        "timestamp": time.time(),
    }

    out_path = REPO_ROOT / "CKS_RUN_OUTPUT" / "ci" / "entrypoint_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["system_valid"] else 1)
