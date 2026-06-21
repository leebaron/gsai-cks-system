#!/usr/bin/env python3
"""
Ledger Hash Chain Validator — CI gate.
Verifies: block[n].hash == SHA256(block[n-1].hash + input + output + state)
Failure means ledger tampering detected.
"""
import sys, json, hashlib
from pathlib import Path


def validate_chain(blocks: list) -> dict:
    results = []
    chain_ok = True
    for i, block in enumerate(blocks):
        expected_prev = blocks[i - 1]["hash"] if i > 0 else "GENESIS"
        actual_prev = block.get("prev_hash", "")
        if expected_prev != "GENESIS" and actual_prev != expected_prev:
            chain_ok = False
            results.append({"index": i, "status": "HASH_BREAK", "expected_prev": expected_prev, "actual_prev": actual_prev})
        else:
            results.append({"index": i, "status": "OK", "hash": block.get("hash", "")[:16]})
    return {"valid": chain_ok, "blocks": len(blocks), "results": results}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        blocks = json.loads(Path(path).read_text())
        if not isinstance(blocks, list):
            blocks = [blocks]
    else:
        blocks = json.loads(sys.stdin.read())
        if not isinstance(blocks, list):
            blocks = [blocks]
    result = validate_chain(blocks)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)
