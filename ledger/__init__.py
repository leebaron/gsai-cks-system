"""
gsai_verifier/violation_reporter.py — Non-repudiation violation evidence chain

Every violation produces a hash-linked record for ledger+audit.
"""

import hashlib
import json
import time
from typing import Any, Dict, List


class ViolationReporter:
    """
    Produces tamper-evident violation records.

    Each record:
      - timestamp
      - observable data
      - violated constraints
      - SHA256 hash over sorted JSON
    """

    def report(self, obs, violations: List[str]) -> Dict[str, Any]:
        record = {
            "timestamp": time.time(),
            "observable": getattr(obs, 'data', str(obs)),
            "violations": violations,
        }

        record["hash"] = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

        return record

    def report_from_result(self, obs, result) -> Dict[str, Any]:
        """Convenience: extract violations from a ConstraintResult."""
        return self.report(obs, result.violated_constraints)
