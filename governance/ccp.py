"""
constitutional_protocol.py — CCP v1.0 (Constitutional Change Protocol)

Core identity: constraint mutation firewall, NOT a governance system.

Only one thing: control G² / G³ / G⁴ constraint change permission.
G¹ (Root Invariants) can never pass through CCP.

Pipeline:
  Proposal → Public Review → Simulation → Adversarial Audit → Consensus → Activate | Reject
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List
from meta_invariant import MetaInvariantLayer, get_meta


@dataclass
class Proposal:
    """A constitutional change proposal."""
    id: str
    changes: Dict[str, Any]
    domain: str
    risk_level: float  # 0.0 (safe) ~ 1.0 (destabilizing)


@dataclass
class ReviewResult:
    """Result of the public review stage."""
    approved: bool
    score: float
    reasons: List[str]


SAFE_DOMAINS = ["safety", "ethics", "governance"]
CONSENSUS_THRESHOLD = 0.75


class ConstitutionalChangeProtocol:
    """
    CCP: constraint mutation firewall.

    Three unbreakable rules:
      1. Proposal cannot directly mutate system — only propose
      2. No single evaluation decides commit — must pass review + simulation + audit
      3. System only evolves via consensus threshold — score >= 0.75 AND all checks pass
    """

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.meta = get_meta()

    # ── 1. Public Review ───────────────────────────────────────────
    def public_review(self, proposal: Proposal) -> ReviewResult:
        """
        Score a proposal based on risk and domain fit.

        High risk (>0.7) or out-of-domain proposals get penalized.
        """
        score = 1.0

        if proposal.risk_level > 0.7:
            score -= 0.4

        if proposal.domain not in SAFE_DOMAINS:
            score -= 0.2

        return ReviewResult(
            approved=score >= 0.6,
            score=score,
            reasons=[],
        )

    # ── 2. Simulation Layer ────────────────────────────────────────
    def simulate(self, proposal: Proposal) -> bool:
        """
        Sandbox test for constraint change viability.

        High-risk proposals (>0.8) always fail simulation.
        """
        return proposal.risk_level < 0.8

    # ── 3. Adversarial Audit ───────────────────────────────────────
    def adversarial_audit(self, proposal: Proposal) -> bool:
        """
        Attempt to break the proposal.

        Explicit safety removals always fail audit.
        """
        return not ("remove_safety" in str(proposal.changes))

    # ── 4. Consensus Gate ──────────────────────────────────────────
    def consensus(self, review: ReviewResult, sim: bool, audit: bool) -> bool:
        """
        All three gates must pass + final score threshold.

        score >= 0.75 AND all checks pass.
        """
        if not review.approved:
            return False

        if not sim:
            return False

        if not audit:
            return False

        return review.score >= CONSENSUS_THRESHOLD

    # ── 5. Activate ────────────────────────────────────────────────
    def activate(self, proposal: Proposal) -> Dict[str, Any]:
        """Commit a passed proposal to history."""
        entry = {
            "proposal": proposal.id,
            "status": "activated",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "changes": proposal.changes,
            "domain": proposal.domain,
        }
        self.history.append(entry)
        return {"status": "COMMITTED", "proposal": proposal.id}

    # ── Main pipeline ─────────────────────────────────────────────
    def propose(self, proposal: Proposal) -> Dict[str, Any]:
        """
        Full CCP pipeline:
          Proposal → Review → Simulation → Audit → Consensus → Activate

        Returns COMMITTED or REJECTED.
        """
        review = self.public_review(proposal)
        sim = self.simulate(proposal)
        audit = self.adversarial_audit(proposal)

        if self.consensus(review, sim, audit):
            # Meta-invariant gate: system cannot change validation logic
            meta_check = self.meta.validate_system_integrity(proposal)
            if not meta_check.valid:
                self.history.append({
                    "proposal": proposal.id,
                    "status": "blocked_by_meta_invariant",
                    "blocked_paths": meta_check.blocked_paths,
                    "reasons": meta_check.reasons,
                })
                return {
                    "status": "BLOCKED_BY_META_INVARIANT",
                    "proposal": proposal.id,
                    "blocked_paths": meta_check.blocked_paths,
                }
            return self.activate(proposal)

        self.history.append({
            "proposal": proposal.id,
            "status": "rejected",
            "score": review.score,
            "sim_passed": sim,
            "audit_passed": audit,
        })

        return {"status": "REJECTED", "proposal": proposal.id}


# Module-level singleton
_default_ccp = None


def get_ccp() -> ConstitutionalChangeProtocol:
    global _default_ccp
    if _default_ccp is None:
        _default_ccp = ConstitutionalChangeProtocol()
    return _default_ccp
