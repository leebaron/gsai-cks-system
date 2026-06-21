#!/usr/bin/env python3
"""Ledger — append-only blockchain with hash chaining"""
import hashlib, json, time, uuid


class LedgerBlockchain:
    def __init__(self, chain_path=None):
        self.chain = []
        self.chain_path = chain_path
        if chain_path:
            try:
                self.chain = json.loads(open(chain_path).read())
            except:
                self.chain = []

    def append(self, trace_id, observation, execution, ral_result) -> dict:
        index = len(self.chain)
        prev_hash = self.chain[-1]["hash"] if self.chain else "0" * 16
        payload = {
            "index": index,
            "trace_id": trace_id,
            "observation": observation,
            "execution": execution,
            "ral": ral_result,
            "timestamp": time.time(),
        }
        payload_str = json.dumps(payload, sort_keys=True)
        block_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]

        block = {**payload, "prev_hash": prev_hash, "hash": block_hash, "genesis_hash": self.chain[0]["hash"] if self.chain else block_hash}
        block["events"] = [{"action": "observe", "value": observation.get("value", "")},
                           {"action": "execute", "value": execution.get("output", "")}]
        block["final_hash"] = block_hash

        self.chain.append(block)
        return block
