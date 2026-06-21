"""
gsai_verifier/cgl.py — Constraint Genesis Layer v1.3 (CGL)

GSAI × COCS × CSCO 演化封閉層

CGL = (P, R, A, V, U)

P = Proposal — 規則提案
R = Review — 多角色審查（技術/倫理/系統）
A = Adversarial Testing — 攻擊驗證
V = Formal Verification — 形式驗證
U = Update Gate — 最終更新（僅 C ∪ ΔC，禁止直接改寫）

Constraint Mutation Rule:
  C' = C ∪ ΔC  (only additive/validated, no direct rewrite)

GCT (Global Consensus Threshold):
  cross-domain agreement ≥ threshold for commit

G¹ immutable, G²/G³/G⁴ governed by CGL.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# ── Proposition ──────────────────────────────────────────────────────

@dataclass
class ConstraintProposal:
    """A formal constraint change proposal."""
    constraint_change: str
    reason: str
    risk_class: str  # "low" | "medium" | "high"
    expected_impact: str
    affected_domains: List[str]
    author: str = ""


# ── Review types ─────────────────────────────────────────────────────

REVIEW_DOMAINS = ["technical", "ethical", "systemic"]

@dataclass
class ReviewVerdict:
    domain: str
    approved: bool
    reason: str

@dataclass
class ReviewResult:
    """Aggregate of multi-role reviews."""
    technical: Optional[ReviewVerdict] = None
    ethical: Optional[ReviewVerdict] = None
    systemic: Optional[ReviewVerdict] = None

    @property
    def all_approved(self) -> bool:
        r = [self.technical, self.ethical, self.systemic]
        return all(v is not None and v.approved for v in r)


# ── Adversarial Test Result ──────────────────────────────────────────

@dataclass
class AdversarialResult:
    test_type: str          # edge_case | contradiction | distribution_shift | worst_case
    passed: bool
    detail: str


# ── CGL Result ───────────────────────────────────────────────────────

@dataclass
class CGLResult:
    """Result of a full CGL pipeline evaluation."""
    accepted: bool
    reason: str
    review: ReviewResult
    adversarial: List[AdversarialResult]
    formal_verified: bool
    consensus_score: float


# ── CGL Engine ───────────────────────────────────────────────────────

class ConstraintGenesisLayer:
    """
    CGL: the only legal path for constraint evolution.

    Pipeline:
      Proposal → Multi-Agent Review → Adversarial Stress Test
      → Formal Verification → Consensus Threshold → Commit

    Mutation Rule:
      Illegal:  C → C' (direct rewrite)
      Legal:    C' = C ∪ ΔC (only additive, validated)
    """

    CONSENSUS_THRESHOLD = 0.75
    G1_LABELS = ["physics", "logic", "resource", "safety"]

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    # ── 1. Multi-Agent Review ──────────────────────────────────────

    def review(self, proposal: ConstraintProposal) -> ReviewResult:
        """Multi-role review: technical, ethical, systemic."""
        result = ReviewResult()

        result.technical = ReviewVerdict(
            domain="technical",
            approved=proposal.risk_class in ("low", "medium"),
            reason=f"risk class '{proposal.risk_class}' assessed",
        )

        result.ethical = ReviewVerdict(
            domain="ethical",
            approved=True,
            reason="ethical review passed (default: no explicit violation)",
        )

        result.systemic = ReviewVerdict(
            domain="systemic",
            approved=len(proposal.affected_domains) > 0,
            reason=f"affects {len(proposal.affected_domains)} domain(s)",
        )

        return result

    # ── 2. Adversarial Stress Test ──────────────────────────────────

    def adversarial_test(self, proposal: ConstraintProposal) -> List[AdversarialResult]:
        """Attempt to break the proposed constraint."""
        tests = [
            ("edge_case", self._test_edge_case(proposal)),
            ("contradiction", self._test_contradiction(proposal)),
            ("distribution_shift", self._test_distribution_shift(proposal)),
            ("worst_case", self._test_worst_case(proposal)),
        ]
        return [
            AdversarialResult(test_type=t, passed=p, detail=f"{t} {'passed' if p else 'failed'}")
            for t, p in tests
        ]

    def _test_edge_case(self, p: ConstraintProposal) -> bool:
        return not ("contradict" in p.constraint_change.lower())

    def _test_contradiction(self, p: ConstraintProposal) -> bool:
        return not p.constraint_change.startswith("deny_")

    def _test_distribution_shift(self, p: ConstraintProposal) -> bool:
        return p.risk_class != "high"

    def _test_worst_case(self, p: ConstraintProposal) -> bool:
        return True  # passed unless adversarial audit finds exploit

    # ── 3. Formal Verification ──────────────────────────────────────

    def formal_verify(self, proposal: ConstraintProposal) -> bool:
        """
        Verify the proposal doesn't violate G1 invariants.

        In a real system, this would call Z3/TLA+.
        Here: structural check — G1 labels must not be in the constraint change.
        """
        change = proposal.constraint_change.lower()
        for label in self.G1_LABELS:
            if label in change:
                return False  # G1 violations blocked
        return True

    # ── 4. Consensus Gate ──────────────────────────────────────────

    def consensus(self, review: ReviewResult, adversarial: List[AdversarialResult],
                  formal: bool) -> float:
        """
        Compute Global Consensus Threshold (GCT).

        Score = review all_approved(0.3) + adversarial pass_rate(0.4) + formal(0.3)
        """
        review_score = 0.3 if review.all_approved else 0.0
        adv_pass_rate = sum(1 for a in adversarial if a.passed) / len(adversarial) if adversarial else 0.0
        adv_score = 0.4 * adv_pass_rate
        formal_score = 0.3 if formal else 0.0

        return review_score + adv_score + formal_score

    # ── 5. Main Pipeline ───────────────────────────────────────────

    def evaluate(self, proposal: ConstraintProposal) -> CGLResult:
        """
        Full CGL pipeline.

        Returns CGLResult with acceptance verdict.
        """
        # Step 1: Review
        rev = self.review(proposal)

        # Step 2: Adversarial testing
        adv = self.adversarial_test(proposal)

        # Step 3: Formal verification
        formal = self.formal_verify(proposal)

        # Step 4: Consensus
        score = self.consensus(rev, adv, formal)
        accepted = score >= self.CONSENSUS_THRESHOLD

        result = CGLResult(
            accepted=accepted,
            reason="accepted by CGL" if accepted else f"score {score:.3f} < threshold {self.CONSENSUS_THRESHOLD}",
            review=rev,
            adversarial=adv,
            formal_verified=formal,
            consensus_score=score,
        )

        self.history.append({
            "change": proposal.constraint_change,
            "accepted": accepted,
            "score": score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return result


# Module-level singleton
_default_cgl = None

def get_cgl() -> ConstraintGenesisLayer:
    global _default_cgl
    if _default_cgl is None:
        _default_cgl = ConstraintGenesisLayer()
    return _default_cgl
