"""
gsai_verifier/runtime_gate.py — Non-bypassable M_valid Runtime Gate

Enforces: ∀ x, output(x) ∈ M_valid

guard(observable, fn):
  - ALLOW → calls fn(observable)
  - DENY  → raises RuntimeGateError
  - DEFER → routes to human/CCP review
"""

from typing import Any, Callable
from .types import Observable, ConstraintResult, Verdict
from .m_valid import MValidEngine
from .violation_reporter import ViolationReporter


class RuntimeGateError(Exception):
    """Raised when the RuntimeGate denies execution."""
    def __init__(self, result: ConstraintResult, report: dict):
        self.result = result
        self.report = report
        super().__init__(f"BLOCKED: {result.violated_constraints}")


class RuntimeGate:
    """
    Non-bypassable execution gate.

    All pipeline execution flows through guard():
      1. MValidEngine.evaluate(observable)
      2. ALLOW → execute fn
      3. DENY  → raise, logged with violation reporter
      4. DEFER → route to human/CCP
    """

    def __init__(self, verifier: MValidEngine = None):
        self.verifier = verifier or MValidEngine()
        self.reporter = ViolationReporter()
        self._deferred: list = []

    def guard(self, observable: Observable, fn: Callable) -> Any:
        """
        Gate execution through M_valid.

        Args:
            observable: Observable from O layer
            fn: execution function (e.g., TAL.process)

        Returns:
            fn(observable) if ALLOW
            deferred dict if DEFER
            Raises RuntimeGateError if DENY
        """
        result = self.verifier.evaluate(observable)

        if result.verdict == Verdict.ALLOW:
            return fn(observable)

        if result.verdict == Verdict.DEFER:
            return self._route_to_review(observable, result)

        # DENY — raise with evidence
        report = self.reporter.report_from_result(observable, result)
        raise RuntimeGateError(result, report)

    def _route_to_review(self, obs: Observable, result: ConstraintResult) -> dict:
        """Route deferrals to human/CCP review."""
        entry = {
            "status": "deferred",
            "reason": result.explanation,
            "violations": result.violated_constraints,
            "observable": obs.data,
        }
        self._deferred.append(entry)
        return entry

    @property
    def deferred_count(self) -> int:
        return len(self._deferred)
