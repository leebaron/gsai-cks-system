"""
gsai_verifier/meta_governance.py — Meta-Governance Layer v1.4 (MG)

GSAI × COCS × CSCO × CGL 文明治理封頂層

MG = (S, D, Q, T, F)

S = Stakeholders — 治理參與者集合
D = Decision protocol — 決策機制
Q = Qualification rules — 參與資格
T = Threshold system — 通過門檻
F = Finalization function — 最終生效

三層治理:
  L1: Local Governance — single domain (controls G²)
  L2: Cross-Domain Governance — multi-domain consistency
  L3: Civilizational Governance — G¹/G⁴/GCT modification (hardest)

Governance Invariants:
  GIV-1: No Single Authority Rule
  GIV-2: Auditability Requirement
  GIV-3: Reversibility Window
  GIV-4: Anti-Capture Principle
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone


# ── Stakeholders ─────────────────────────────────────────────────────

STAKEHOLDER_TYPES = ["HUMAN", "AI", "INDEPENDENT_AUDITOR", "INSTITUTION"]


@dataclass
class Stakeholder:
    """A governance participant with verified qualifications."""
    id: str
    stakeholder_type: str   # HUMAN | AI | INDEPENDENT_AUDITOR | INSTITUTION
    weight: float           # voting weight (0.0 - 1.0)
    qualified: bool = False
    integrity_hash: str = ""


# ── Governance levels ────────────────────────────────────────────────

class GovernanceLevel:
    LOCAL = "local"           # G²: single domain
    CROSS_DOMAIN = "cross"    # G²/G³: multi-domain
    CIVILIZATIONAL = "civil"  # G¹/G⁴/GCT


# ── Decision types ───────────────────────────────────────────────────

@dataclass
class GovernanceProposal:
    """A proposal at the meta-governance level."""
    description: str
    governance_level: str      # local | cross | civil
    affected_domains: List[str]
    proposed_by: str
    content: Dict[str, Any]


@dataclass
class GovernanceVote:
    stakeholder_id: str
    approve: bool
    weight: float
    reason: str = ""


@dataclass
class GovernanceDecision:
    """The result of a meta-governance decision process."""
    accepted: bool
    governance_level: str
    total_weight: float
    approval_weight: float
    votes: List[GovernanceVote]
    reason: str


# ── Meta-Governance Engine ──────────────────────────────────────────

class MetaGovernance:
    """
    MG: the gate above all gates.

    Defines who can change the rules of changing rules.
    Prevents single-actor dominance, opaque authority, and capture.
    """

    # Threshold per governance level
    THRESHOLDS = {
        "local": 0.60,
        "cross": 0.75,
        "civil": 0.90,  # G¹/G⁴/GCT changes need near-unanimity
    }

    # Maximum weight any single stakeholder type can hold
    MAX_TYPE_WEIGHT = {
        "local": 0.5,
        "cross": 0.4,
        "civil": 0.3,  # no single type > 30% in civilizational decisions
    }

    # Governance invariants
    INVARIANTS = {
        "GIV-1: No Single Authority Rule": "no single stakeholder can force a decision",
        "GIV-2: Auditability Requirement": "every decision must have a trace in L",
        "GIV-3: Reversibility Window": "decisions reversible within window",
        "GIV-4: Anti-Capture Principle": "system cannot be controlled by single entity/nation/model/culture",
    }

    def __init__(self):
        self.stakeholders: Dict[str, Stakeholder] = {}
        self.history: List[Dict[str, Any]] = []

    # ── Stakeholder management ─────────────────────────────────────

    def register_stakeholder(self, s: Stakeholder) -> bool:
        """Register a stakeholder after qualification check."""
        if s.stakeholder_type not in STAKEHOLDER_TYPES:
            return False
        if s.weight <= 0.0 or s.weight > 1.0:
            return False
        s.qualified = True
        self.stakeholders[s.id] = s
        return True

    # ── Qualification ──────────────────────────────────────────────

    def check_qualifications(self, stakeholder: Stakeholder) -> bool:
        """
        Q: Qualification check.
        
        Q1 — Integrity: traceable, non-forgeable
        Q2 — Independence: no conflict of interest  
        Q3 — Stability: consistent behavior over time
        """
        # Q1: must have an integrity hash
        if not stakeholder.integrity_hash:
            return False

        # Q2: structural independence check
        if stakeholder.stakeholder_type in ("HUMAN", "AI") and stakeholder.weight > 0.8:
            return False  # high weight = potential domination risk

        return True

    # ── Decision protocol ──────────────────────────────────────────

    def decide(self, proposal: GovernanceProposal, votes: List[GovernanceVote]) -> GovernanceDecision:
        """
        D: Decision protocol.

        Computes weighted vote against level-specific threshold.
        Enforces no-single-type-dominance per governance level.
        """
        level = proposal.governance_level
        threshold = self.THRESHOLDS.get(level, 0.75)

        total_weight = sum(v.weight for v in votes)
        approval_weight = sum(v.weight for v in votes if v.approve)

        # Enforce type weight caps
        type_weights: Dict[str, float] = {}
        for v in votes:
            s = self.stakeholders.get(v.stakeholder_id)
            if s:
                wt = type_weights.get(s.stakeholder_type, 0.0)
                type_weights[s.stakeholder_type] = wt + v.weight

        max_type = self.MAX_TYPE_WEIGHT.get(level, 0.5)
        for stype, w in type_weights.items():
            if w > max_type:
                # Type dominance detected — decision blocked
                decision = GovernanceDecision(
                    accepted=False,
                    governance_level=level,
                    total_weight=total_weight,
                    approval_weight=approval_weight,
                    votes=votes,
                    reason=f"BLOCKED: {stype} weight {w:.2f} exceeds max {max_type:.2f} for level {level}",
                )
                self._log(decision)
                return decision

        accepted = (approval_weight / total_weight >= threshold) if total_weight > 0 else False

        decision = GovernanceDecision(
            accepted=accepted,
            governance_level=level,
            total_weight=total_weight,
            approval_weight=approval_weight,
            votes=votes,
            reason=f"{'APPROVED' if accepted else 'REJECTED'} at {level} level ({approval_weight:.2f}/{total_weight:.2f} ≥ {threshold})",
        )

        self._log(decision)
        return decision

    # ── Internal ──────────────────────────────────────────────────

    def _log(self, decision: GovernanceDecision):
        self.history.append({
            "level": decision.governance_level,
            "accepted": decision.accepted,
            "approval_ratio": f"{decision.approval_weight:.2f}/{decision.total_weight:.2f}",
            "reason": decision.reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def status(self) -> Dict[str, Any]:
        """Full governance system status."""
        return {
            "stakeholders": len(self.stakeholders),
            "stakeholder_types": {
                t: sum(1 for s in self.stakeholders.values() if s.stakeholder_type == t)
                for t in STAKEHOLDER_TYPES
            },
            "thresholds": self.THRESHOLDS,
            "max_type_weights": self.MAX_TYPE_WEIGHT,
            "invariants": list(self.INVARIANTS.keys()),
            "decision_history": len(self.history),
            "last_decision": self.history[-1] if self.history else None,
        }


# Module-level singleton
_default_mg = None

def get_mg() -> MetaGovernance:
    global _default_mg
    if _default_mg is None:
        _default_mg = MetaGovernance()
    return _default_mg
