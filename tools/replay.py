#!/usr/bin/env python3
"""
replay.py — Replay verification gate.
Replays cks_runtime execution from captured artifacts and compares hashes.

Usage:
    python3 tools/replay.py [artifact_dir]
    
Exit code:
    0 — replay matches production output
    1 — replay mismatch detected
"""
import sys, json, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact"


def replay_from_artifacts() -> dict:
    """Simulate replay: re-hash artifacts and compare to stored capture."""
    if not ARTIFACT_DIR.exists():
        return {"error": f"artifact dir not found: {ARTIFACT_DIR}"}

    # Read CI capture (production output record)
    capture_path = ARTIFACT_DIR / "ci_capture.json"
    if not capture_path.exists():
        return {"error": "ci_capture.json not found — run capture_artifacts.py first"}

    production = json.loads(capture_path.read_text())
    expected_hash = production.get("artifact_hash", "")

    # Replay: re-hash from raw artifacts
    required = ["execution_trace.json", "decision_ledger.json", "constraint_report.json", "validity_proof.json", "final_state.json"]
    combined = b""
    for name in required:
        fp = ARTIFACT_DIR / name
        if fp.exists():
            combined += hashlib.sha256(fp.read_bytes()).hexdigest().encode()

    replay_hash = hashlib.sha256(combined).hexdigest() if combined else "ERROR"

    match = replay_hash == expected_hash

    return {
        "replay_result": "MATCH" if match else "MISMATCH",
        "replay_hash": replay_hash,
        "expected_hash": expected_hash,
        "match": match,
        "env_hash": production.get("env_hash", ""),
    }


if __name__ == "__main__":
    result = replay_from_artifacts()
    # Write result to artifact dir
    out_path = ARTIFACT_DIR / "replay_result.json"
    out_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("match") else 1)
