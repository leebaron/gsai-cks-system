#!/usr/bin/env python3
"""
capture_artifacts.py — CI artifact capture with env binding.
Usage: python3 tools/capture_artifacts.py [output_dir]
Output: artifacts.json with env_hash + file hashes + replay input
"""
import sys, json, hashlib, platform, os, subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact"
REQUIRED = ["execution_trace.json", "decision_ledger.json", "constraint_report.json", "validity_proof.json", "final_state.json"]


def env_hash() -> str:
    """Deterministic env fingerprint for replay reproducibility."""
    raw = json.dumps({
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def capture() -> dict:
    if not OUTPUT_DIR.exists():
        return {"error": f"artifact dir not found: {OUTPUT_DIR}"}

    # Run hash_artifacts if available
    hasher = REPO_ROOT / "tools" / "hash_artifacts.py"
    if hasher.exists():
        subprocess.run(["python3", str(hasher), str(OUTPUT_DIR)], cwd=REPO_ROOT, capture_output=True)

    manifest_path = OUTPUT_DIR / "hash_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    # Read raw artifacts
    files = {}
    all_found = True
    for name in REQUIRED:
        fp = OUTPUT_DIR / name
        if fp.exists():
            data = fp.read_bytes()
            files[name] = {
                "size": len(data),
                "hash": hashlib.sha256(data).hexdigest(),
            }
        else:
            files[name] = {"size": 0, "hash": None}
            all_found = False

    # Combined artifact hash (replay input)
    combined = b""
    for f in REQUIRED:
        h = files.get(f, {}).get("hash")
        if h:
            combined += h.encode()

    artifact_hash = hashlib.sha256(combined).hexdigest() if combined else "ERROR"
    env = env_hash()

    result = {
        "artifact_hash": artifact_hash,
        "env_hash": env,
        "all_artifacts_found": all_found,
        "files": files,
        "manifest": manifest,
    }

    capture_path = OUTPUT_DIR / "ci_capture.json"
    capture_path.write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    result = capture()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("all_artifacts_found") else 1)
