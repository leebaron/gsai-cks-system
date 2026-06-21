#!/usr/bin/env python3
"""
hash_artifacts.py — CI/CD tool.
Produces artifact_hash = sha256(execution_trace + decision_ledger + constraint_report + final_state + z3_result)

Outputs: artifacts.json with all hashes.
Usage:
    python3 tools/hash_artifacts.py [artifact_dir]
"""
import sys, json, hashlib
from pathlib import Path


ARTIFACT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("CKS_RUN_OUTPUT/artifact")
REQUIRED_FILES = [
    "execution_trace.json",
    "decision_ledger.json",
    "constraint_report.json",
    "validity_proof.json",
    "final_state.json",
]


def hash_file(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "hash": None, "size": 0}
    data = path.read_bytes()
    return {
        "path": str(path),
        "hash": hashlib.sha256(data).hexdigest(),
        "size": len(data),
    }


def main():
    if not ARTIFACT_DIR.exists():
        print(json.dumps({"error": f"artifact dir not found: {ARTIFACT_DIR}"}))
        sys.exit(1)

    file_hashes = {}
    combined = b""
    all_found = True

    for fname in REQUIRED_FILES:
        fp = ARTIFACT_DIR / fname
        h = hash_file(fp)
        file_hashes[fname] = h
        if h["hash"]:
            combined += h["hash"].encode()
        else:
            all_found = False

    artifact_hash = hashlib.sha256(combined).hexdigest() if combined else "ERROR"

    # Build ID: combine commit env if available, else use artifact_hash as seed
    build_id = hashlib.sha256((artifact_hash + "cks-proof-closure-v1").encode()).hexdigest()[:32]

    result = {
        "build_id": build_id,
        "artifact_hash": artifact_hash,
        "all_artifacts_found": all_found,
        "files": file_hashes,
    }

    # Write manifest
    manifest_path = ARTIFACT_DIR / "hash_manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

    sys.exit(0 if all_found else 1)


if __name__ == "__main__":
    main()
