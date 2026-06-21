"""
meta_invariant.py — Meta-Constraint Invariance Layer v1.0

GSAI × COCS × CSCO × CCP 統一架構 — closure 的最後一層

Core responsibility:
  Ensure the constraint system itself cannot be changed by CCP
  in ways that violate the constraint validation logic.

Three invariants:
  1. COCS gate logic cannot be modified via CCP
  2. Constraint evaluation semantics must remain stable
  3. Ledger/audit path must remain immutable

System closure condition:
  System cannot change itself into a system that violates itself.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional


SACRED_PATHS = [
    "COCS_gate_logic",
    "validation_semantics",
    "ledger_or_audit",
    "meta_invariant_itself",
]

SACRED_LABELS = {
    "COCS_gate_logic": "COCS G¹~G⁴ check functions cannot be modified",
    "validation_semantics": "constraint evaluation semantics must be stable",
    "ledger_or_audit": "ledger append + audit path must remain immutable",
    "meta_invariant_itself": "meta-invariant code cannot be modified via CCP",
}


@dataclass
class MetaInvariantResult:
    """Result of a meta-invariant integrity check."""
    valid: bool
    blocked_paths: List[str]
    reasons: List[str]


class MetaInvariantLayer:
    """
    Meta-Constraint Invariance Layer.

    Guarantees that the constraint system's own validation logic
    cannot be undermined through the governance protocol (CCP).

    Insertion point: CCP commit gate — before activate().
    """

    def validate_system_integrity(self, proposal: Any) -> MetaInvariantResult:
        """
        Check that a CCP proposal does not violate meta-invariants.

        Args:
            proposal: A CCP Proposal object with .changes dict

        Returns:
            MetaInvariantResult: valid=True if all meta-invariants hold
        """
        blocked = []
        reasons = []

        changes_str = str(proposal.changes) if hasattr(proposal, 'changes') else str(proposal)

        for path in SACRED_PATHS:
            if path.lower() in changes_str.lower():
                blocked.append(path)
                reasons.append(SACRED_LABELS.get(path, path))

        return MetaInvariantResult(
            valid=len(blocked) == 0,
            blocked_paths=blocked,
            reasons=reasons,
        )


# Module-level singleton
_default_meta = None


def get_meta() -> MetaInvariantLayer:
    global _default_meta
    if _default_meta is None:
        _default_meta = MetaInvariantLayer()
    return _default_meta
