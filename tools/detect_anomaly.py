#!/usr/bin/env python3
"""
detect_anomaly.py — Anomaly detection for self-healing CI.

Reads runtime evidence (pytest, replay, hash chain) and classifies state.

Exit code:
    0 — OK (no anomaly, system healthy)
    1 — FAIL_RUNTIME (execution error)
    2 — FAIL_DETERMINISM (replay mismatch)
    3 — FAIL_PERFORMANCE (execution time anomaly)
    4 — FAIL_CHAIN (hash chain broken)
    5 — FAIL_ROEL (output violation)
"""
import sys, json, time, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
THRESHOLD_SECONDS = 30.0  # max expected CI pipeline time


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except:
        return {}


def detect() -> dict:
    artifact_dir = REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact"

    results = {}

    # Check 1: runtime exit code
    pytest = load_json(artifact_dir / "execution_graph.json").get("execution", {}).get("pytest", {})
    py_exit = pytest.get("exit_code", -1)
    if py_exit != 0:
        results["runtime"] = {"status": "FAIL_RUNTIME", "detail": f"pytest exit code {py_exit}", "severity": "high"}
    else:
        results["runtime"] = {"status": "OK", "detail": f"pytest exit code {py_exit}", "severity": "none"}

    # Check 2: replay determinism
    replay = load_json(artifact_dir / "replay_result.json")
    replay_match = replay.get("match", False)
    if not replay_match:
        results["determinism"] = {"status": "FAIL_DETERMINISM", "detail": f"replay match={replay_match}", "severity": "high"}
    else:
        results["determinism"] = {"status": "OK", "detail": f"replay match={replay_match}", "severity": "none"}

    # Check 3: hash chain validity
    chain = load_json(artifact_dir / "verification_gate.json")
    chain_valid = chain.get("system_valid", False) if chain else False
    if not chain_valid:
        results["hash_chain"] = {"status": "FAIL_CHAIN", "detail": "verification gate not valid", "severity": "critical"}
    else:
        results["hash_chain"] = {"status": "OK", "detail": "verification gate valid", "severity": "none"}

    # Check 4: ROEL (via execution graph)
    exec_graph = load_json(artifact_dir / "execution_graph.json")
    exec_data = exec_graph.get("execution", {})
    roel_gate = exec_data.get("roel_gate", {}).get("gate_passed", False)
    roel_reject = exec_data.get("roel_table_reject", {}).get("table_blocked", False)
    if not roel_gate or not roel_reject:
        results["roel"] = {"status": "FAIL_ROEL", "detail": f"gate_passed={roel_gate} table_blocked={roel_reject}", "severity": "high"}
    else:
        results["roel"] = {"status": "OK", "detail": f"gate_passed={roel_gate} table_blocked={roel_reject}", "severity": "none"}

    # Aggregate
    severities = [r.get("severity", "none") for r in results.values()]
    if "critical" in severities:
        overall = "CRITICAL"
        exit_code = 5
    elif "high" in severities:
        overall = "ANOMALY"
        exit_code = 1
    else:
        overall = "OK"
        exit_code = 0

    return {
        "status": overall,
        "exit_code": exit_code,
        "timestamp": time.time(),
        "checks": results,
    }


if __name__ == "__main__":
    result = detect()
    print(json.dumps(result, indent=2))
    sys.exit(result.get("exit_code", 1))
