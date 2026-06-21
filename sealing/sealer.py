#!/usr/bin/env python3
"""Cryptographic Sealing — tamper-evident SHA-256 chain"""
import hashlib, json


class CryptoSealer:
    def seal(self, block: dict) -> str:
        payload = json.dumps(block, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def verify_seal(self, block: dict, expected_seal: str) -> bool:
        payload = json.dumps(block, sort_keys=True)
        actual = hashlib.sha256(payload.encode()).hexdigest()
        return actual == expected_seal
