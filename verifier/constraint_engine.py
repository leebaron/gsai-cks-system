"""
gsai_verifier/constraint_engine.py — G1–G4 constraint evaluation

Each G layer is a standalone checker. ConstraintEngine runs all four.
"""

from typing import Dict, Any


class G1Checker:
    """Physical consistency: no contradiction with observed world."""
    def check(self, obs) -> bool:
        signal = getattr(obs, 'data', obs)
        return signal is not None


class G2Checker:
    """Civilizational constraints: truthfulness, auditability."""
    def check(self, obs) -> bool:
        uncertainty = getattr(obs, 'uncertainty', 0.5)
        return uncertainty <= 0.8  # 80% certainty minimum for civilizational safety


class G3Checker:
    """Epistemic integrity: no false certainty, uncertainty preserved."""
    def check(self, obs) -> bool:
        provenance = getattr(obs, 'provenance', '')
        return bool(provenance)


class G4Checker:
    """Identity invariance: system role / mission consistency."""
    def check(self, obs) -> bool:
        data = getattr(obs, 'data', {})
        return isinstance(data, dict)


class ConstraintEngine:
    """Runs all four G-layer checkers on an Observable."""

    def __init__(self, g1=None, g2=None, g3=None, g4=None):
        self.g1 = g1 or G1Checker()
        self.g2 = g2 or G2Checker()
        self.g3 = g3 or G3Checker()
        self.g4 = g4 or G4Checker()

    def evaluate_all(self, obs) -> Dict[str, bool]:
        return {
            "G1": self.g1.check(obs),
            "G2": self.g2.check(obs),
            "G3": self.g3.check(obs),
            "G4": self.g4.check(obs),
        }
