"""
gsai_verifier/types.py — Core types for M_valid Runtime Verifier

Verdict: ALLOW | DENY | DEFER
Observable: grounded data + provenance + uncertainty
ConstraintResult: verdict + violations + explanation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    DEFER = "DEFER"


@dataclass
class Observable:
    """A runtime observable produced by the Observation Operator."""
    data: Dict[str, Any]
    provenance: str
    uncertainty: float


@dataclass
class ConstraintResult:
    """Result from a full M_valid evaluation."""
    verdict: Verdict
    violated_constraints: List[str]
    explanation: Optional[str] = None
