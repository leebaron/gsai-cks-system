#!/usr/bin/env python3
"""CKS test suite — production gate tests"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_cocs_gate():
    from cocs.gate_check import COCSGate
    g = COCSGate()
    r = g.check({"value": "valid_input", "confidence": 1.0})
    assert r["status"] == "PASS", f"Gate should PASS, got {r}"
    r2 = g.check({"value": "", "confidence": 0.0})
    assert r2["status"] == "BLOCKED", f"Empty input should BLOCK, got {r2}"
    print("[TEST] COCS gate: PASS")


def test_replay_engine():
    from replay.engine import ReplayEngine
    r = ReplayEngine()
    import json, hashlib
    block = {
        "genesis_hash": "0" * 16,
        "events": [{"action": "t1", "value": "a"}, {"action": "t2", "value": "b"}],
        "final_hash": "",
    }
    s = block["genesis_hash"]
    for e in block["events"]:
        s = hashlib.sha256((s + json.dumps(e, sort_keys=True)).encode()).hexdigest()[:16]
    block["final_hash"] = s
    assert r.verify(block)
    print("[TEST] Replay engine: PASS")


def test_sealing():
    from sealing.sealer import CryptoSealer
    c = CryptoSealer()
    s = c.seal({"index": 1, "data": "test"})
    assert len(s) == 64
    assert c.verify_seal({"index": 1, "data": "test"}, s)
    assert not c.verify_seal({"index": 2, "data": "fake"}, s)
    print("[TEST] Sealing: PASS")


def test_ral():
    from ral.validator import RALValidator
    r = RALValidator()
    result = r.validate({"hash": "abcdef1234567890"})
    assert result["aligned"]
    print("[TEST] RAL: PASS")


def test_csco():
    from csco.engine import CSCOEngine
    e = CSCOEngine()
    r = e.execute({"value": "test_input"})
    assert "EXECUTED" in r["output"]
    assert len(r["hash"]) == 16
    print("[TEST] CSCO: PASS")


if __name__ == "__main__":
    test_cocs_gate()
    test_replay_engine()
    test_sealing()
    test_ral()
    test_csco()
    print("\n=== ALL TESTS PASSED ===")
