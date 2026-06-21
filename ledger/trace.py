"""
trace_viewer.py — CSCO Telemetry / Trace Layer v0.2

Minimal observability layer for the full pipeline:
  O → COCS → TAL → CSCO → Ledger → Audit

Drop-in. No external deps. Buffered window of last 20 events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime, timezone


@dataclass
class TraceEvent:
    """A single trace event with type + payload + timestamp."""
    type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: _now_iso())


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TraceViewer:
    """
    Minimal observability layer for CSCO flow.

    Records each pipeline stage as a trace event.
    dump() returns the last 20 events — enough to debug without infinite memory.
    """

    def __init__(self):
        self.buffer: List[TraceEvent] = []

    def record(self, event_type: str, data: Dict[str, Any]):
        """Record a trace event."""
        self.buffer.append(TraceEvent(type=event_type, data=data))

    def dump(self) -> Dict[str, Any]:
        """Return last 20 events as serializable dict."""
        recent = self.buffer[-20:]
        return {
            "trace_length": len(self.buffer),
            "events": [
                {
                    "type": e.type,
                    "timestamp": e.timestamp,
                    "data": e.data,
                }
                for e in recent
            ],
        }

    def last(self, n: int = 1) -> List[Dict[str, Any]]:
        """Return the last n events."""
        recent = self.buffer[-n:]
        return [
            {"type": e.type, "timestamp": e.timestamp, "data": e.data}
            for e in recent
        ]

    def clear(self):
        """Clear trace buffer."""
        self.buffer.clear()
