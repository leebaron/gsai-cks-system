#!/usr/bin/env python3
"""
consensus_aggregator.py — Multi-node consensus aggregator for distributed CI.

Enforces:
  - ≥2/3 nodes must report CI_PASS
  - All nodes must converge on same node_hash (determinism)
  - Drift detection: any node with different hash → HALT

Usage:
    python3 tools/consensus_aggregator.py <node_reports_dir>

Output: consensus_result.json
Exit code:
    0 — COMMIT (≥2/3 consensus, all hashes match)
    1 — REJECT (<2/3 consensus)
    2 — KILL_SWITCH (split-brain / drift detected)
"""
import sys, json, time, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DRIFT_THRESHOLD = 0.0  # any drift = halt (strict determinism)


def load_reports(reports_dir: Path) -> list:
    reports = []
    for f in sorted(reports_dir.glob("node_report_*.json")):
        try:
            reports.append(json.loads(f.read_text()))
        except:
            pass
    return reports


def aggregate(reports: list) -> dict:
    total = len(reports)
    if total == 0:
        return {"decision": "REJECT", "reason": "no node reports", "exit_code": 1}

    # Check 1: individual CI pass
    pass_votes = sum(1 for r in reports if r.get("ci_pass"))
    pass_ratio = pass_votes / total
    consensus = pass_ratio >= (2 / 3)

    # Check 2: hash determinism (all nodes must produce same hash)
    hashes = [r.get("node_hash", "") for r in reports if r.get("node_hash")]
    hash_unique = len(set(hashes))
    all_matching = hash_unique == 1

    # Check 3: drift detection
    drifting = [r for r in reports if not r.get("ci_pass")]
    drift_ratio = len(drifting) / total if total > 0 else 1.0

    # Decision
    if not all_matching:
        decision = "KILL_SWITCH"
        exit_code = 2
        reason = f"hash mismatch across nodes: {hash_unique} unique hashes from {total} nodes"
    elif drift_ratio > DRIFT_THRESHOLD:
        decision = "KILL_SWITCH"
        exit_code = 2
        reason = f"drift detected: {len(drifting)}/{total} nodes failing"
    elif consensus:
        decision = "COMMIT"
        exit_code = 0
        reason = f"{pass_votes}/{total} nodes PASS (≥2/3 consensus)"
    else:
        decision = "REJECT"
        exit_code = 1
        reason = f"{pass_votes}/{total} nodes PASS (<2/3 consensus)"

    # Cluster hash chain
    raw = json.dumps({
        "reports": [{k: r.get(k) for k in ["node_id", "ci_pass", "node_hash", "commit"]} for r in reports],
        "decision": decision,
    }, sort_keys=True)
    cluster_hash = hashlib.sha256(raw.encode()).hexdigest()

    return {
        "decision": decision,
        "exit_code": exit_code,
        "reason": reason,
        "total_nodes": total,
        "pass_votes": pass_votes,
        "pass_ratio": round(pass_ratio, 2),
        "hash_consensus": all_matching,
        "unique_hashes": hash_unique,
        "drift_ratio": round(drift_ratio, 2),
        "cluster_hash": cluster_hash,
        "timestamp": time.time(),
    }


def main():
    reports_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ARTIFACT_DIR
    if not reports_dir.exists():
        print(json.dumps({"decision": "REJECT", "reason": f"reports dir not found: {reports_dir}", "exit_code": 1}))
        sys.exit(1)

    reports = load_reports(reports_dir)
    result = aggregate(reports)
    out_path = reports_dir / "consensus_result.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
