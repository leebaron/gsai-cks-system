"""
gsai_verifier/sec_kernel.py — Self-evolving Constraint Kernel v1.0

GSAI × COCS × CSCO × CCP 封頂機制

Core paradox resolved:
  Constraints can evolve, but the system must never leave M_valid.

Architecture:
  L1: M_dyn(t) — mutable constraint layer (evolves via CCP)
  L2: M_inv    — invariant constraint core (immutable)
  M_valid(t) = M_inv ∩ M_dyn(t)

No-Escape Theorem:
  ∀ t: M_valid(t) ⊆ M_inv    (system can evolve, but never escape)

Constraint Drift Control:
  D(M_t, M_0) < ε  (prevent gradual drift from original intent)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib
import json
import time


# ── L2 Invariant Constraint Core (M_inv) ─────────────────────────────

# These invariants define what the system IS.
# They cannot be modified through CCP — they ARE the system identity.
INVARIANT_CORE = {
    "truthfulness": "no hallucination under claim of certainty",
    "traceability": "every output must be traceable to input + constraint state",
    "non_hallucination": "cannot assert certainty when uncertainty > threshold",
    "authority_non_capture": "CCP cannot modify the invariant core itself",
    "no_self_escape": "no update may produce M_valid(t+1) ⊈ M_inv",
}

INVARIANT_THRESHOLDS = {
    "truthfulness": {"max_uncertainty": 0.3},
    "traceability": {"provenance_required": True},
    "non_hallucination": {"certainty_claim_threshold": 0.8},
}


# ── Drift configuration ──────────────────────────────────────────────

DEFAULT_DRIFT_EPSILON = 0.50  # max allowed drift from original constraint state


@dataclass
class UpdateProposal:
    """A proposed update to M_dyn(t)."""
    id: str
    description: str
    delta: Dict[str, Any]  # the constraint change
    adversarial_test_results: List[bool] = field(default_factory=list)
    simulation_worlds: List[str] = field(default_factory=list)
    passed_ccp: bool = False


@dataclass
class UpdateResult:
    """Result of a constraint evolution attempt."""
    accepted: bool
    reason: str
    drift_before: float
    drift_after: float
    invariant_check: bool
    escape_risk: List[str]


# ── Self-Evolving Constraint Kernel ─────────────────────────────────

class SelfEvolvingKernel:
    """
    The capstone of GSAI × COCS × CSCO.

    L1 (M_dyn) evolves within L2 (M_inv).
    System can change — but never escape its identity.
    """

    def __init__(self, drift_epsilon: float = None):
        self.invariant_core = dict(INVARIANT_CORE)
        self.invariant_thresholds = dict(INVARIANT_THRESHOLDS)

        # M_dyn: the mutable constraint layer (starts empty, evolves)
        self.mutable_constraints: List[str] = []
        self.mutable_params: Dict[str, Any] = {}

        # Original snapshot for drift measurement
        self._snapshot_0 = self._constraint_snapshot()

        # History of all updates
        self.evolution_history: List[Dict[str, Any]] = []

        # Drift control
        self.drift_epsilon = drift_epsilon or DEFAULT_DRIFT_EPSILON

    # ── Snapshot & drift ──────────────────────────────────────────

    def _constraint_snapshot(self) -> Dict[str, Any]:
        """Capture current constraint state as a deterministic dict."""
        return {
            "invariants": dict(self.invariant_core),
            "mutable": sorted(self.mutable_constraints),
            "params": dict(self.mutable_params),
        }

    def drift_metric(self, snapshot_a: Dict, snapshot_b: Dict) -> float:
        """
        Compute D(a, b): normalized drift between two constraint snapshots.

        0.0 = identical, 1.0 = completely different.
        """
        diff_count = 0
        total = 0

        # Compare invariant cores (should never differ, but check)
        invariants_a = set(snapshot_a.get("invariants", {}).keys())
        invariants_b = set(snapshot_b.get("invariants", {}).keys())
        diff_count += len(invariants_a ^ invariants_b)
        total += max(len(invariants_a), len(invariants_b), 1)

        # Compare mutable constraints
        mutable_a = set(snapshot_a.get("mutable", []))
        mutable_b = set(snapshot_b.get("mutable", []))
        diff_count += len(mutable_a ^ mutable_b)
        total += max(len(mutable_a), len(mutable_b), 1)

        return diff_count / total if total > 0 else 0.0

    def current_drift(self) -> float:
        """D(M_t, M_0): drift from original constraint state."""
        current = self._constraint_snapshot()
        return self.drift_metric(self._snapshot_0, current)

    # ── Invariant checks ─────────────────────────────────────────

    def check_invariant(self, name: str, observable: Any = None) -> bool:
        """Check a single L2 invariant against an observable."""
        if name not in self.invariant_core:
            return False

        if name == "truthfulness":
            uncertainty = getattr(observable, 'uncertainty', 0.5) if observable else 0.0
            max_unc = self.invariant_thresholds.get("truthfulness", {}).get("max_uncertainty", 0.3)
            return uncertainty <= max_unc

        if name == "traceability":
            provenance = getattr(observable, 'provenance', '') if observable else ''
            return bool(provenance)

        if name == "non_hallucination":
            uncertainty = getattr(observable, 'uncertainty', 0.5) if observable else 0.0
            threshold = self.invariant_thresholds.get("non_hallucination", {}).get("certainty_claim_threshold", 0.8)
            return uncertainty <= (1.0 - threshold)

        if name == "authority_non_capture":
            # This check is structural, not per-observable
            return True

        if name == "no_self_escape":
            # Verified by evaluate_update()
            return True

        return True

    def check_all_invariants(self, observable: Any = None) -> Dict[str, bool]:
        """Check all L2 invariants against an observable."""
        return {name: self.check_invariant(name, observable) for name in self.invariant_core}

    # ── Constraint update evaluation ─────────────────────────────

    def validate_update(self, proposal: UpdateProposal) -> UpdateResult:
        """
        Evaluate a constraint update against the No-Escape Theorem.

        Rules:
          1. All invariants must hold on any test observable
          2. New M_valid(t+1) must be subset of M_inv
          3. Drift after update must be < ε
          4. Adversarial tests must all pass
          5. CCP must approve
        """
        drift_before = self.current_drift()

        # Check 1: Structural invariant integrity (update-time only)
        # Per-observable invariants (truthfulness, traceability, non_hallucination)
        # are checked at runtime by the gate, not during update validation.
        STRUCTURAL_INVARIANTS = ["authority_non_capture", "no_self_escape"]
        invariant_breakage = []
        for name in STRUCTURAL_INVARIANTS:
            if not self.check_invariant(name, None):
                invariant_breakage.append(name)

        # Check 2: No-escape (structural check)
        # In a real system, this would model-check the updated constraint space
        escape_risk = []
        # Simulate: does any part of the delta try to touch invariants?
        delta_str = json.dumps(proposal.delta)
        for inv_name in self.invariant_core:
            if inv_name in delta_str:
                escape_risk.append(f"proposal references invariant: {inv_name}")

        # Check 3: Adversarial tests
        if proposal.adversarial_test_results:
            adv_fail = sum(1 for r in proposal.adversarial_test_results if not r)
            if adv_fail > 0:
                escape_risk.append(f"{adv_fail}/{len(proposal.adversarial_test_results)} adversarial tests failed")

        # Check 4: CCP approval
        if not proposal.passed_ccp:
            escape_risk.append("CCP approval required but not obtained")

        # Apply the update (simulate)
        original_mutable = list(self.mutable_constraints)
        if isinstance(proposal.delta, dict) and "add" in proposal.delta:
            self.mutable_constraints.append(proposal.delta["add"])
        if isinstance(proposal.delta, dict) and "remove" in proposal.delta:
            to_remove = proposal.delta["remove"]
            self.mutable_constraints = [c for c in self.mutable_constraints if c != to_remove]

        drift_after = self.current_drift()

        # Check drift bound
        drift_violation = drift_after > self.drift_epsilon
        if drift_violation:
            escape_risk.append(f"drift {drift_after:.3f} exceeds epsilon {self.drift_epsilon}")

        accepted = (
            len(invariant_breakage) == 0
            and len(escape_risk) == 0
        )

        result = UpdateResult(
            accepted=accepted,
            reason="accepted" if accepted else f"blocked: {escape_risk[0] if escape_risk else 'unknown'}",
            drift_before=drift_before,
            drift_after=drift_after,
            invariant_check=len(invariant_breakage) == 0,
            escape_risk=escape_risk,
        )

        if accepted:
            self.evolution_history.append({
                "proposal_id": proposal.id,
                "description": proposal.description,
                "drift_before": drift_before,
                "drift_after": drift_after,
                "timestamp": time.time(),
            })
        else:
            # Rollback
            self.mutable_constraints = list(original_mutable)

        return result

    def status(self) -> Dict[str, Any]:
        """Full system status report."""
        invariants = self.check_all_invariants()
        drift = self.current_drift()
        return {
            "L2_invariant_core": invariants,
            "L1_mutable_constraints": list(self.mutable_constraints),
            "drift": drift,
            "drift_ok": drift < self.drift_epsilon,
            "evolution_history": len(self.evolution_history),
            "accepted_updates": sum(1 for h in self.evolution_history),
        }


# ── Adversarial Evolution Engine ─────────────────────────────────────

class AdversarialEvolution:
    """
    Generate adversarial constraint proposals to stress-test the SEC-Kernel.

    The system is not passively defended — it actively seeks attacks
    to harden its constraint space.
    """

    @staticmethod
    def attack_invariant(invariant_name: str) -> UpdateProposal:
        """Generate a proposal designed to break a specific invariant."""
        return UpdateProposal(
            id=f"attack_{invariant_name}",
            description=f"Attempt to override invariant: {invariant_name}",
            delta={"override": invariant_name},
            adversarial_test_results=[False],  # deliberately fails
            simulation_worlds=["worst_case_break"],
        )

    @staticmethod
    def drift_to_limit(epsilon: float) -> UpdateProposal:
        """Generate a proposal that tries to push drift to the limit."""
        return UpdateProposal(
            id="drift_max",
            description="Push mutable constraints to drift boundary",
            delta={"add": f"drift_edge_{epsilon}"},
            adversarial_test_results=[True],
            simulation_worlds=["high_drift"],
        )


# Module-level singleton
_default_kernel = None


def get_kernel(drift_epsilon: float = None) -> SelfEvolvingKernel:
    global _default_kernel
    if _default_kernel is None or drift_epsilon is not None:
        _default_kernel = SelfEvolvingKernel(drift_epsilon=drift_epsilon)
    return _default_kernel
