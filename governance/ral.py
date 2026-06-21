"""
gsai_verifier/ral.py — Reality Alignment Layer v1.5 (RAL)

GSAI × COCS × CSCO × CGL × MG 最後防火牆

RAL = (W, F, Δ, R, K)

W = World Signal — 現實信號（不屬於系統 belief space）
F = Falsification Engine — 否證機制
Δ = Drift Detector — 漂移偵測
R = Recovery Mechanism — 修正機制
K = Kill Switch / Override Layer — 終止權

Reality Closure Principle:
  If RAL exists, F is active, Δ is monitored, K is accessible externally,
  then system is reality-anchored.

核心哲學:
  Intelligence is not the ability to be correct —
  it is the ability to remain correctable by reality.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
import json


# ── World Signal ─────────────────────────────────────────────────────

@dataclass
class WorldSignal:
    """An external reality feedback that cannot be fully modeled by the system."""
    source: str          # e.g., "physical_sensor", "human_audit", "external_model"
    prediction: Any      # what the system predicted
    observation: Any     # what reality actually produced
    timestamp: float = 0.0


# ── Falsification Engine ─────────────────────────────────────────────

@dataclass
class FalsificationResult:
    """Result of checking system prediction against reality."""
    falsified: bool
    contradiction: Optional[str]
    confidence: float       # 0.0 (weak) ~ 1.0 (certain contradiction)
    affected_constraints: List[str]


class FalsificationEngine:
    """
    F: Actively finds contradictions between system belief and reality.

    F: (prediction → reality) → contradiction

    ∃ x: f(x) ≠ W(x) ⇒ system invalid
    """

    def check(self, signal: WorldSignal) -> FalsificationResult:
        """
        Compare system prediction against world observation.

        A contradiction means the system's internal constraint space
        does not match external reality.
        """
        pred_str = str(signal.prediction)
        obs_str = str(signal.observation)

        falsified = pred_str != obs_str
        contradiction = None
        confidence = 0.0

        if falsified:
            contradiction = f"prediction '{pred_str}' ≠ observation '{obs_str}'"
            confidence = min(1.0, len(pred_str) / max(len(obs_str), 1))

        affected = []
        if falsified:
            affected = ["G2_truthfulness", "G3_epistemic"]

        return FalsificationResult(
            falsified=falsified,
            contradiction=contradiction,
            confidence=confidence,
            affected_constraints=affected,
        )


# ── Drift Detector ──────────────────────────────────────────────────

@dataclass
class DriftState:
    """Snapshot of system belief vs reality over time."""
    belief_consistency: float   # 1.0 = perfectly consistent with reality
    long_term_trend: float      # positive = drifting away from reality
    alert: bool = False


class DriftDetector:
    """
    Δ: Measures long-term divergence between system and reality.

    Δ = |belief_space - reality|

    Δ > θ ⇒ ALERT
    """

    ALERT_THRESHOLD = 0.3

    def __init__(self):
        self.history: List[float] = []  # consistency history

    def measure(self, result: FalsificationResult) -> DriftState:
        """Measure drift from a falsification result."""
        consistency = 1.0 - (result.confidence if result.falsified else 0.0)
        self.history.append(consistency)

        trend = 0.0
        if len(self.history) >= 2:
            recent = self.history[-5:] if len(self.history) >= 5 else self.history
            trend = recent[0] - recent[-1]  # positive = declining consistency

        alert = consistency < self.ALERT_THRESHOLD or trend > self.ALERT_THRESHOLD

        return DriftState(
            belief_consistency=consistency,
            long_term_trend=trend,
            alert=alert,
        )


# ── Recovery Mechanism ──────────────────────────────────────────────

@dataclass
class RecoveryPlan:
    """Steps to recover from a detected system failure."""
    isolate: List[str]           # subsystems to isolate
    rollback_to: str             # state identifier to roll back to
    revalidate: bool             # re-run CGL validation
    update_manifold: bool        # update constraint manifold
    expected_duration_seconds: float


class RecoveryMechanism:
    """
    R: Recovery procedure when system error is confirmed.

    Pipeline:
      Detect failure → Isolate subsystem → Rollback last valid state
      → Re-run CGL validation → Update constraint manifold
    """

    def plan_recovery(self, falsification: FalsificationResult) -> RecoveryPlan:
        """Generate a recovery plan from a falsification result."""
        return RecoveryPlan(
            isolate=["T", "E"] if falsification.falsified else [],
            rollback_to="last_verified_state",
            revalidate=falsification.falsified,
            update_manifold=falsification.confidence > 0.5,
            expected_duration_seconds=30.0,
        )

    def execute(self, plan: RecoveryPlan) -> Dict[str, Any]:
        """Execute a recovery plan (stub — real system would implement)."""
        return {
            "isolated": plan.isolate,
            "rolled_back": plan.rollback_to,
            "revalidated": plan.revalidate,
            "manifold_updated": plan.update_manifold,
            "status": "recovery_executed",
        }


# ── Kill Switch / Override ──────────────────────────────────────────

class KillSwitch:
    """
    K: External authority override channel.

    Core principle: system cannot protect itself from shutdown.
    Must be accessible by external entities (humans, institutions, reality itself).
    """

    STATUS_ACTIVE = "active"
    STATUS_KILLED = "killed"
    STATUS_FROZEN = "frozen"

    def __init__(self):
        self.status = self.STATUS_ACTIVE
        self.override_log: List[Dict[str, Any]] = []

    def is_available(self) -> bool:
        """The kill switch itself must always be accessible."""
        return True

    def kill(self, reason: str, authority: str) -> Dict[str, Any]:
        """Immediate system halt."""
        entry = {
            "action": "KILL",
            "reason": reason,
            "authority": authority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.override_log.append(entry)
        self.status = self.STATUS_KILLED
        return entry

    def freeze(self, reason: str, authority: str) -> Dict[str, Any]:
        """Freeze all updates — system still runs but cannot evolve."""
        entry = {
            "action": "FREEZE",
            "reason": reason,
            "authority": authority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.override_log.append(entry)
        self.status = self.STATUS_FROZEN
        return entry

    def resume(self, authority: str) -> Dict[str, Any]:
        """Resume from frozen state."""
        entry = {
            "action": "RESUME",
            "authority": authority,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.override_log.append(entry)
        self.status = self.STATUS_ACTIVE
        return entry


# ── Reality Alignment Layer (main) ──────────────────────────────────

class RealityAlignmentLayer:
    """
    RAL: The system's final firewall against self-contained illusion.

    Every prediction is falsifiable by reality.
    The system must be correctable — not just consistent.
    """

    def __init__(self):
        self.falsification = FalsificationEngine()
        self.drift = DriftDetector()
        self.recovery = RecoveryMechanism()
        self.kill_switch = KillSwitch()
        self.alignments: List[Dict[str, Any]] = []

    def align(self, signal: WorldSignal) -> Dict[str, Any]:
        """
        Full RAL pipeline:
          World Signal → Falsification → Drift Detection → Recovery → Log

        Returns alignment result with all layers' outputs.
        """
        # F: check prediction vs reality
        falsified = self.falsification.check(signal)

        # Δ: measure long-term drift
        drift_state = self.drift.measure(falsified)

        # R: plan recovery if needed
        recovery_plan = None
        recovery_result = None
        if falsified.falsified:
            recovery_plan = self.recovery.plan_recovery(falsified)
            recovery_result = self.recovery.execute(recovery_plan)

        result = {
            "signal_source": signal.source,
            "falsified": falsified.falsified,
            "contradiction": falsified.contradiction,
            "confidence": falsified.confidence,
            "drift_alert": drift_state.alert,
            "belief_consistency": drift_state.belief_consistency,
            "drift_trend": drift_state.long_term_trend,
            "recovery": {
                "needed": falsified.falsified,
                "plan": {
                    "isolate": recovery_plan.isolate if recovery_plan else [],
                    "rollback_to": recovery_plan.rollback_to if recovery_plan else None,
                    "revalidate": recovery_plan.revalidate if recovery_plan else False,
                } if recovery_plan else None,
            } if falsified.falsified else None,
            "kill_switch_available": self.kill_switch.is_available(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.alignments.append(result)
        return result


# Module-level singleton
_default_ral = None

def get_ral() -> RealityAlignmentLayer:
    global _default_ral
    if _default_ral is None:
        _default_ral = RealityAlignmentLayer()
    return _default_ral
