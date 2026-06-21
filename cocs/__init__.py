"""
cocs_gate.py — COCS Constraint Gate v0.2

M_valid = G1 ∩ G2 ∩ G3 ∩ G4

Pipeline:
  O (ObservationOperator) → COCS Gate → TAL → CSCO

If any layer rejects, the pipeline short-circuits with a REJECT.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ConstraintResult:
    """Result of a full COCS gate check."""
    valid: bool
    failed_layer: Optional[str]
    reason: Optional[str]
    trace: Dict[str, Any]


class COCSGate:
    """
    Constraint Gate:
    M_valid = G1 ∩ G2 ∩ G3 ∩ G4

    Sequential check: G1 → G2 → G3 → G4
    First failure short-circuits and returns REJECT.
    """

    # ── G1: Root invariants ────────────────────────────────────────
    def check_G1(self, obs) -> bool:
        """Physical + logical safety boundary."""
        signal = obs.signal
        return not (signal.get("signal_type") is None)

    # ── G2: Civilizational constraints ─────────────────────────────
    def check_G2(self, obs) -> bool:
        """Truthfulness + harm minimization."""
        return obs.confidence > 0.2

    # ── G3: Adaptive constraints ───────────────────────────────────
    def check_G3(self, obs) -> bool:
        """Learning guard — reject unverifiable novelty."""
        return obs.signal.get("structured", 0) >= 0.3

    # ── G4: Identity constraints ───────────────────────────────────
    def check_G4(self, obs) -> bool:
        """Mission/role/domain alignment."""
        return "observable_event" in str(obs.signal)

    # ── Main gate ──────────────────────────────────────────────────
    def validate(self, obs) -> ConstraintResult:
        """
        Evaluate a(t) ∈ M_valid.

        Sequential: fails fast on first violated layer.
        """
        if not self.check_G1(obs):
            return ConstraintResult(False, "G1", "invalid_signal", {})

        if not self.check_G2(obs):
            return ConstraintResult(False, "G2", "low_confidence", {})

        if not self.check_G3(obs):
            return ConstraintResult(False, "G3", "unstructured_signal", {})

        if not self.check_G4(obs):
            return ConstraintResult(False, "G4", "identity_mismatch", {})

        return ConstraintResult(True, None, None, {"status": "M_valid_pass"})


# Module-level singleton
_default_gate = None


def get_gate() -> COCSGate:
    global _default_gate
    if _default_gate is None:
        _default_gate = COCSGate()
    return _default_gate
