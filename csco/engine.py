#!/usr/bin/env python3
"""CSCO Execution Engine"""
import hashlib, uuid


class CSCOEngine:
    def execute(self, observation: dict, trace_id: str = None) -> dict:
        trace_id = trace_id or uuid.uuid4().hex[:16]
        obs_val = observation.get("value", "")
        result = {
            "trace_id": trace_id,
            "output": f"EXECUTED:{obs_val}",
            "hash": hashlib.sha256(obs_val.encode()).hexdigest()[:16],
            "deterministic": True,
        }
        return result
