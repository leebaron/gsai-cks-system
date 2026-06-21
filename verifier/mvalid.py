"""
gsai_verifier/m_valid.py — M_valid Engine (G1 ∩ G2 ∩ G3 ∩ G4)

Core evaluation logic. Not a gate — just the constraint check.
RuntimeGate (runtime_gate.py) provides the non-bypassable wrapper.
"""

from typing import List
from .types import Observable, ConstraintResult, Verdict
from .constraint_engine import ConstraintEngine


class MValidEngine:
    """
    M_valid = G1 ∩ G2 ∩ G3 ∩ G4

    evaluate(obs) → ConstraintResult:
      - ALLOW if all G layers pass
      - DEFER if G3 (epistemic) fails but others pass
      - DENY otherwise
    """

    def __init__(self, constraints: ConstraintEngine = None):
        self.constraints = constraints or ConstraintEngine()

    def evaluate(self, obs: Observable) -> ConstraintResult:
        violations: List[str] = []

        results = self.constraints.evaluate_all(obs)

        if not results["G1"]:
            violations.append("G1_PHYSICAL")
        if not results["G2"]:
            violations.append("G2_CIVILIZATION")
        if not results["G3"]:
            violations.append("G3_EPISTEMIC")
        if not results["G4"]:
            violations.append("G4_IDENTITY")

        if len(violations) == 0:
            return ConstraintResult(Verdict.ALLOW, [])

        # Epistemic uncertainty is deferrable, not denial
        if violations == ["G3_EPISTEMIC"]:
            return ConstraintResult(
                Verdict.DEFER,
                violations,
                "Epistemic uncertainty requires human/CCP routing",
            )

        return ConstraintResult(Verdict.DENY, violations)
