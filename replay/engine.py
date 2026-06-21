#!/usr/bin/env python3
"""Replay Engine — deterministic re-execution verification"""
import json, hashlib


class ReplayEngine:
    def verify(self, ledger_block: dict) -> bool:
        """Re-execute from genesis state and verify final hash matches"""
        events = ledger_block.get("events", [])
        genesis_hash = ledger_block.get("genesis_hash", "")
        expected_hash = ledger_block.get("final_hash", "")

        state_hash = genesis_hash
        for evt in events:
            payload = json.dumps(evt, sort_keys=True)
            state_hash = hashlib.sha256((state_hash + payload).encode()).hexdigest()[:16]

        match = state_hash == expected_hash
        return match

    def full_replay(self, trace_path: str) -> dict:
        with open(trace_path) as f:
            trace = json.load(f)
        ok = self.verify(trace)
        return {"replay_result": "MATCH" if ok else "MISMATCH", "ok": ok}
