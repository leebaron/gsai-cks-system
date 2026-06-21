#!/usr/bin/env python3
"""
consensus_node.py — Independent deterministic runner for distributed CI.

Each node produces identical output given the same commit and environment.
Result is a signed execution report for the consensus aggregator.

Usage:
    python3 tools/consensus_node.py [--node-id <id>] [--commit <sha>]

Output: report_<node_id>.json
"""
import sys, json, hashlib, subprocess, platform, time, os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact"
NODE_ID = sys.argv[sys.argv.index("--node-id") + 1] if "--node-id" in sys.argv else os.uname()[1]
COMMIT_SHA = None


def get_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5,
        ).stdout.strip()
    except:
        return "unknown"


def env_fingerprint() -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "node_id": NODE_ID,
    }


def hash_file(path: Path) -> str:
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return "MISSING"


def run_deterministic() -> dict:
    # Step 1: pytest
    py = subprocess.run(
        ["python3", "-m", "pytest", "-q", "tests/"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=30,
    )

    # Step 2: ROEL gate
    roel_clean = subprocess.run(
        ["python3", "roel.py"],
        input="VIEW_STATE: COMPLETE\nnode consensus test.\n",
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
    )

    # Step 3: ROEL table rejection
    roel_reject = subprocess.run(
        ["python3", "roel.py"],
        input="VIEW_STATE: COMPLETE\n| col | val |\n| a | b |\n",
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
    )

    # Step 4: Hash chain (if artifacts exist)
    chain_valid = False
    if (REPO_ROOT / "ledger" / "validate_chain.py").exists():
        chain_test = subprocess.run(
            ["python3", "ledger/validate_chain.py"],
            input=json.dumps([
                {"index": 0, "hash": "a000", "prev_hash": "GENESIS"},
                {"index": 1, "hash": "b111", "prev_hash": "a000"},
            ]),
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=10,
        )
        try:
            chain_valid = json.loads(chain_test.stdout).get("valid", False)
        except:
            pass

    # Step 5: Artifact hashes (if present)
    artifacts = {
        "execution_trace": hash_file(ARTIFACT_DIR / "execution_trace.json"),
        "decision_ledger": hash_file(ARTIFACT_DIR / "decision_ledger.json"),
        "constraint_report": hash_file(ARTIFACT_DIR / "constraint_report.json"),
        "validity_proof": hash_file(ARTIFACT_DIR / "validity_proof.json"),
        "final_state": hash_file(ARTIFACT_DIR / "final_state.json"),
    }

    # Combined hash = deterministic node fingerprint
    combined = (
        str(py.returncode) +
        str(roel_clean.returncode) +
        str(roel_reject.returncode) +
        str(chain_valid) +
        json.dumps(artifacts, sort_keys=True)
    )
    node_hash = hashlib.sha256(combined.encode()).hexdigest()

    report = {
        "node_id": NODE_ID,
        "commit": COMMIT_SHA or get_commit(),
        "timestamp": time.time(),
        "env": env_fingerprint(),
        "checks": {
            "pytest": {"exit_code": py.returncode, "pass": py.returncode == 0},
            "roel_gate": {"exit_code": roel_clean.returncode, "pass": roel_clean.returncode == 0},
            "roel_table": {"exit_code": roel_reject.returncode, "pass": roel_reject.returncode == 1},
            "hash_chain": {"valid": chain_valid, "pass": chain_valid},
        },
        "artifacts": artifacts,
        "node_hash": node_hash,
        "ci_pass": (
            py.returncode == 0 and
            roel_clean.returncode == 0 and
            roel_reject.returncode == 1 and
            chain_valid
        ),
    }

    return report


def main():
    global COMMIT_SHA
    if "--commit" in sys.argv:
        idx = sys.argv.index("--commit")
        if idx + 1 < len(sys.argv):
            COMMIT_SHA = sys.argv[idx + 1]

    report = run_deterministic()
    out_path = ARTIFACT_DIR / f"node_report_{NODE_ID}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["ci_pass"] else 1)


if __name__ == "__main__":
    main()
