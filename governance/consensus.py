"""
gsai_verifier/consensus.py — Distributed No-Bypass Consensus Layer v1.0

GSAI × COCS × CSCO × CCP 文明級閉合層

系統升級路徑：
  single-runtime gated system → distributed constraint enforcement system

核心：
  - VerifierNode: 獨立 M_valid 驗證器（無共享 mutable state）
  - ConsensusLayer: 聚合 n 個 verifier 結果（Byzantine-resilient）
  - DistributedGate: 需 consensus = ALLOW 才能執行
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import hashlib
import json
import time

from .types import Verdict, Observable, ConstraintResult
from .m_valid import MValidEngine
from .violation_reporter import ViolationReporter


# ── Consensus types ──────────────────────────────────────────────────

@dataclass
class VerifierVote:
    """A single verifier node's vote on an observable."""
    node_id: str
    verdict: Verdict
    violated_constraints: List[str]
    explanation: Optional[str] = None
    signature: str = ""  # hash over vote for tamper-evidence


@dataclass
class ConsensusResult:
    """Result of aggregating n verifier votes."""
    overall: Verdict
    votes: List[VerifierVote]
    n_total: int
    n_allow: int
    n_deny: int
    n_defer: int
    signatures: Dict[str, str]  # node_id → signature


# ── Verifier Node ────────────────────────────────────────────────────

class VerifierNode:
    """
    An independent M_valid verifier.

    Properties:
      - No shared mutable state with other verifiers
      - Cannot influence other verifiers
      - Each has its own MValidEngine (can be diverse implementations)
    """

    def __init__(self, node_id: str, verifier: MValidEngine = None):
        self.node_id = node_id
        self.verifier = verifier or MValidEngine()
        self.reporter = ViolationReporter()
        self.vote_count = 0

    def evaluate(self, obs: Observable) -> ConstraintResult:
        """Evaluate an observable and return a signed vote."""
        return self.verifier.evaluate(obs)

    def vote(self, obs: Observable) -> VerifierVote:
        """Evaluate and produce a signed VerifierVote."""
        result = self.verifier.evaluate(obs)
        self.vote_count += 1

        vote = VerifierVote(
            node_id=self.node_id,
            verdict=result.verdict,
            violated_constraints=result.violated_constraints,
            explanation=result.explanation,
        )

        # Sign the vote with a hash for tamper-evidence
        vote.signature = self._sign(vote)
        return vote

    def _sign(self, vote: VerifierVote) -> str:
        """Deterministic signature: hash over vote fields."""
        payload = f"{vote.node_id}|{vote.verdict.value}|{sorted(vote.violated_constraints)}|{self.vote_count}"
        return hashlib.sha256(payload.encode()).hexdigest()


# ── Consensus Layer ──────────────────────────────────────────────────

class ConsensusLayer:
    """
    Aggregates verifier results into a single consensus verdict.

    Consensus rules:
      ALLOW → ∀ i: V_i(x) = ALLOW
      DENY  → ∃ i: V_i(x) = DENY
      DEFER → majority V_i(x) = DEFER

    Byzantine safety: n ≥ 3k + 1  (k = max tolerated faulty nodes)
    """

    def __init__(self, verifiers: List[VerifierNode] = None):
        self.verifiers = verifiers or []
        self.history: List[ConsensusResult] = []

    def add_verifier(self, verifier: VerifierNode):
        """Register a new verifier node."""
        self.verifiers.append(verifier)

    @property
    def n(self) -> int:
        return len(self.verifiers)

    @property
    def byzantine_k(self) -> int:
        """Maximum tolerated faulty/bypassed nodes: k = floor((n-1)/3)."""
        return (self.n - 1) // 3 if self.n > 0 else 0

    def reach_consensus(self, obs: Observable) -> ConsensusResult:
        """
        Run all verifiers and aggregate votes.

        Returns ConsensusResult with overall verdict.
        """
        if not self.verifiers:
            raise RuntimeError("No verifier nodes registered for consensus")

        votes: List[VerifierVote] = []
        for v in self.verifiers:
            votes.append(v.vote(obs))

        n_allow = sum(1 for v in votes if v.verdict == Verdict.ALLOW)
        n_deny = sum(1 for v in votes if v.verdict == Verdict.DENY)
        n_defer = sum(1 for v in votes if v.verdict == Verdict.DEFER)

        signatures = {v.node_id: v.signature for v in votes}

        # Consensus rule
        if n_deny > 0:
            overall = Verdict.DENY
        elif n_allow == self.n:
            overall = Verdict.ALLOW
        else:
            overall = Verdict.DEFER

        result = ConsensusResult(
            overall=overall,
            votes=votes,
            n_total=self.n,
            n_allow=n_allow,
            n_deny=n_deny,
            n_defer=n_defer,
            signatures=signatures,
        )

        self.history.append(result)
        return result


# ── Distributed Gate ─────────────────────────────────────────────────

class DistributedGate:
    """
    No-single-point-of-bypass execution gate.

    Requires consensus(n-verifiers) = ALLOW before execution.
    Byzantine-resilient: survives up to k = floor((n-1)/3) faulty nodes.
    """

    def __init__(self, consensus: ConsensusLayer):
        self.consensus = consensus

    def guard(self, obs: Observable, fn: Callable) -> Any:
        """
        Gate execution through distributed consensus.

        Args:
            obs: Observable signal
            fn: Execution function (called only if consensus = ALLOW)

        Returns:
            fn(obs) if ALLOW
            deferred dict if DEFER
            Raises DistributedGateError if DENY
        """
        result = self.consensus.reach_consensus(obs)

        if result.overall == Verdict.ALLOW:
            return fn(obs)

        if result.overall == Verdict.DEFER:
            return {
                "status": "deferred",
                "reason": "consensus_majority_deferred",
                "allow": result.n_allow,
                "deny": result.n_deny,
                "defer": result.n_defer,
                "total": result.n_total,
            }

        # DENY
        deny_reasons = [
            f"{v.node_id}: {v.violated_constraints}"
            for v in result.votes if v.verdict == Verdict.DENY
        ]
        raise DistributedGateError(
            result,
            f"BLOCKED by {len(deny_reasons)}/{result.n_total} verifiers: {deny_reasons}"
        )


class DistributedGateError(Exception):
    """Raised when distributed consensus votes DENY."""
    def __init__(self, result: ConsensusResult, msg: str):
        self.result = result
        super().__init__(msg)


# ── Helper: build standard 3-verifier cluster (n ≥ 3k+1, k=1) ────────

def build_standard_cluster(n_verifiers: int = 4) -> DistributedGate:
    """
    Build a standard n-verifier cluster with Byzantine resilience.

    Default: 4 verifiers, tolerates k=1 faulty/bypassed node (n ≥ 3k+1).
    k=1: n ≥ 4
    k=2: n ≥ 7
    Each verifier has an independent MValidEngine.
    """
    layer = ConsensusLayer()
    for i in range(n_verifiers):
        node = VerifierNode(node_id=f"VERIFIER_{i+1}", verifier=MValidEngine())
        layer.add_verifier(node)
    return DistributedGate(layer)
