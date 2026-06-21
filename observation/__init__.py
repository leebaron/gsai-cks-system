"""
observation_operator.py — O Layer v0.1

GSAI × COCS × CSCO 統一架構 insertion (2026-06-21)

Pipeline:
  Input → O.ground() → WorldState → O.normalize() → FeatureVector → O.extract() → ObservableSignal → TAL

Design constraints:
  - Zero dependency on kernel.py / TAL / CSCO internals
  - Single dataclass output (ObservableSignal) that TAL already accepts
  - No constraint logic (that's COCS Gate, separate module)
  - Pure function semantics: same input → same output
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class WorldState:
    """Grounded representation of raw input."""
    raw: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeatureVector:
    """Normalized feature space representation."""
    features: Dict[str, float]
    structure: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservableSignal:
    """TAL/CSCO-consumable signal with provenance trace."""
    signal: Dict[str, Any]
    confidence: float
    trace: Dict[str, Any] = field(default_factory=dict)


class ObservationOperator:
    """
    O-layer: Raw Input → Grounded State → Normalized Features → Observable Signal

    Three responsibilities:
      1. ground()    — extract structured WorldState from raw input
      2. normalize() — map WorldState to normalized FeatureVector
      3. extract()   — produce TAL-ready ObservableSignal with confidence + trace
    """

    # ── 1. Grounding layer ──────────────────────────────────────────
    def ground(self, raw_input: Any) -> WorldState:
        """
        Transform raw input into a grounded, traceable world state.

        No feature extraction here — only structural capture + metadata.
        """
        metadata = {
            "type": type(raw_input).__name__,
            "length": len(raw_input) if hasattr(raw_input, "__len__") else 1,
        }
        return WorldState(raw=raw_input, metadata=metadata)

    # ── 2. Normalization layer ──────────────────────────────────────
    def normalize(self, state: WorldState) -> FeatureVector:
        """
        Map grounded WorldState into a normalized feature space.

        Features are floats [0.0, 1.0] for consistency.
        Extensible: additional extractors can be added without changing interface.
        """
        raw = state.raw

        features = {
            "complexity": min(float(len(str(raw))) / 1000.0, 1.0),
            "structuredness": 1.0 if isinstance(raw, dict) else 0.3,
            "ambiguity": 1.0 if isinstance(raw, str) and "?" in raw else 0.2,
        }

        structure = {
            "metadata": state.metadata,
            "has_dict_structure": isinstance(raw, dict),
        }

        return FeatureVector(features=features, structure=structure)

    # ── 3. Extraction layer (TAL-ready) ─────────────────────────────
    def extract(self, fv: FeatureVector) -> ObservableSignal:
        """
        Produce a TAL/CSCO-consumable ObservableSignal.

        The signal dict is flat and schema-free:
          - TAL uses it for truth provenance labeling
          - CSCO uses it for execution routing
        """
        confidence = max(0.0, 1.0 - fv.features.get("ambiguity", 0.5))

        signal = {
            "signal_type": "observable_event",
            "complexity": fv.features.get("complexity", 0.5),
            "structured": fv.features.get("structuredness", 0.5),
        }

        trace = {
            "source": "ObservationOperator",
            "normalized": fv.features,
            "structure": fv.structure,
        }

        return ObservableSignal(signal=signal, confidence=confidence, trace=trace)

    # ── 4. Full pipeline convenience ────────────────────────────────
    def process(self, raw_input: Any) -> ObservableSignal:
        """Run full grounding → normalization → extraction in one call."""
        state = self.ground(raw_input)
        fv = self.normalize(state)
        return self.extract(fv)


# Module-level singleton (optional, kernel.py can also instantiate per-event)
_default_operator = None


def get_operator() -> ObservationOperator:
    """Get or create the default ObservationOperator singleton."""
    global _default_operator
    if _default_operator is None:
        _default_operator = ObservationOperator()
    return _default_operator
