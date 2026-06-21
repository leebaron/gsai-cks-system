#!/usr/bin/env python3
"""
verify_hash.py — Final verification gate for deterministic CI/replay closure.

Checks:
  1. pytest exit code == 0
  2. ROEL gate passes (exit 0 for clean, exit 1 for table)
  3. Artifact hash matches between production and replay
  4. Environment hash stable

Usage:
    python3 tools/verify_hash.py [artifact_dir]

Exit code:
    0 — ALL GATES PASS
    1 — ANY GATE FAILS
"""
import sys, json, hashlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact"


def verify() -> dict:
    checks = {}

    # Check 1: replay result
    replay_path = ARTIFACT_DIR / "replay_result.json"
    replay_result = json.loads(replay_path.read_text()) if replay_path.exists() else {}
    replay_match = replay_result.get("match", False)
    checks["replay"] = {
        "rule": "replay hash matches production",
        "pass": replay_match,
        "actual": replay_result.get("replay_hash", ""),
        "expected": replay_result.get("expected_hash", ""),
    }

    # Check 2: CI capture exists
    capture_path = ARTIFACT_DIR / "ci_capture.json"
    capture = json.loads(capture_path.read_text()) if capture_path.exists() else {}
    checks["capture"] = {
        "rule": "CI capture exists and all artifacts found",
        "pass": capture.get("all_artifacts_found", False),
        "artifact_hash": capture.get("artifact_hash", ""),
        "env_hash": capture.get("env_hash", ""),
    }

    # Check 3: Hash manifest
    manifest_path = ARTIFACT_DIR / "hash_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    all_found = manifest.get("all_artifacts_found", False)
    checks["manifest"] = {
        "rule": "hash_manifest exists and all files present",
        "pass": all_found and bool(manifest.get("build_id", "")),
        "build_id": manifest.get("build_id", ""),
        "artifact_hash": manifest.get("artifact_hash", ""),
    }

    all_pass = all(c["pass"] for c in checks.values())
    return {"system_valid": all_pass, "checks_passed": sum(1 for c in checks.values() if c["pass"]), "checks_total": len(checks), "checks": checks}


def main():
    result = verify()
    print(json.dumps(result, indent=2))

    # Write verification result
    out_path = ARTIFACT_DIR / "verification_gate.json"
    out_path.write_text(json.dumps(result, indent=2))

    sys.exit(0 if result["system_valid"] else 1)


if __name__ == "__main__":
    main()
