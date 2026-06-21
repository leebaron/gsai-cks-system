#!/usr/bin/env python3
"""Replay engine test — CI/CD gate"""
import sys, json
sys.path.insert(0, "..")
from replay.engine import ReplayEngine


def test_replay():
    engine = ReplayEngine()
    test_block = {
        "genesis_hash": "0000000000000000",
        "events": [
            {"action": "observe", "value": "test_input"},
            {"action": "execute", "value": "test_output"},
        ],
        "final_hash": "",
    }
    import hashlib
    state = test_block["genesis_hash"]
    for evt in test_block["events"]:
        state = hashlib.sha256((state + json.dumps(evt, sort_keys=True)).encode()).hexdigest()[:16]
    test_block["final_hash"] = state

    result = engine.verify(test_block)
    print(f"[REPLAY TEST] verify: {result}")
    assert result, "Replay should match"
    print("[REPLAY TEST] PASSED")


if __name__ == "__main__":
    test_replay()
    sys.exit(0)
