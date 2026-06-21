#!/usr/bin/env python3
"""
consensus_kill_switch.py — Cluster-level kill switch for distributed CI.

Triggers:
  - Consensus failure (no 2/3 agreement)
  - Hash mismatch between nodes (split-brain)
  - Drift exceeding threshold
  - Any node returns CRITICAL anomaly

Behavior:
  - Freeze pipeline (in CI context: exit fail)
  - Write cluster freeze log
  - Report node-level status

Usage:
    python3 tools/consensus_kill_switch.py [consensus_result.json]

Exit:
    0 — cluster healthy
    1 — cluster frozen (kill switch engaged)
"""
import sys, json, time, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_consensus(path: str = None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    default = REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact" / "consensus_result.json"
    if default.exists():
        return json.loads(default.read_text())
    return {"decision": "UNKNOWN", "reason": "no consensus result found"}


def check(consensus: dict) -> dict:
    decision = consensus.get("decision", "UNKNOWN")

    if decision == "COMMIT":
        return {
            "status": "HEALTHY",
            "halted": False,
            "exit_code": 0,
            "reason": "cluster consensus reached: COMMIT",
            "cluster_hash": consensus.get("cluster_hash", ""),
        }
    elif decision == "KILL_SWITCH":
        return {
            "status": "HALTED",
            "halted": True,
            "exit_code": 1,
            "reason": consensus.get("reason", "kill switch triggered by consensus failure"),
            "cluster_hash": consensus.get("cluster_hash", ""),
        }
    elif decision == "REJECT":
        return {
            "status": "HALTED",
            "halted": True,
            "exit_code": 1,
            "reason": f"consensus reject: {consensus.get('pass_votes', 0)}/{consensus.get('total_nodes', 0)} nodes",
            "cluster_hash": consensus.get("cluster_hash", ""),
        }
    else:
        return {
            "status": "UNKNOWN",
            "halted": True,
            "exit_code": 1,
            "reason": f"unexpected decision: {decision}",
            "cluster_hash": consensus.get("cluster_hash", ""),
        }


def main():
    args = sys.argv[1:]
    path = args[0] if args else None
    consensus = load_consensus(path)
    result = check(consensus)

    # Write freeze record
    run_dir = REPO_ROOT / "CKS_RUN_OUTPUT" / "cluster_freeze"
    run_dir.mkdir(parents=True, exist_ok=True)
    freeze_path = run_dir / f"freeze_{int(time.time())}.json"
    freeze_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
