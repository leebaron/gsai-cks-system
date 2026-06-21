#!/usr/bin/env python3
"""
ROEL Kill Switch — System protection layer.

Acts when:
  drift_score > threshold (0.30)
  deterministic failure rate spike
  RAL mismatch sustained
  Mesh disagreement > 1/3 nodes

Behavior:
  HALT output, freeze ledger, open recovery mode
"""
import sys, json, os, time


KILL_THRESHOLDS = {
    "drift_score": 0.30,
    "deterministic_failure_pct": 50.0,
    "ral_mismatch_count": 3,
    "mesh_disagreement_pct": 33.0,
}


class KillSwitch:
    def __init__(self, thresholds: dict = None):
        self.thresholds = thresholds or KILL_THRESHOLDS
        self.state = "RUNNING"  # RUNNING | HALTED | RECOVERY
        self.triggers = []
        self.metrics_history = []

    def evaluate(self, metrics: dict) -> dict:
        """Check all kill conditions. Return PASS or HALT."""
        triggers = []

        drift = metrics.get("drift_score", 0.0)
        if drift > self.thresholds["drift_score"]:
            triggers.append(f"DRIFT_EXCEEDED ({drift} > {self.thresholds['drift_score']})")

        det_fail = metrics.get("deterministic_failure_pct", 0.0)
        if det_fail > self.thresholds["deterministic_failure_pct"]:
            triggers.append(f"DETERMINISTIC_SPIKE ({det_fail}% > {self.thresholds['deterministic_failure_pct']}%)")

        ral_mismatch = metrics.get("ral_mismatch_count", 0)
        if ral_mismatch >= self.thresholds["ral_mismatch_count"]:
            triggers.append(f"RAL_MISMATCH_SUSTAINED ({ral_mismatch} >= {self.thresholds['ral_mismatch_count']})")

        mesh_disagreement = metrics.get("mesh_disagreement_pct", 0.0)
        if mesh_disagreement > self.thresholds["mesh_disagreement_pct"]:
            triggers.append(f"MESH_DISAGREEMENT ({mesh_disagreement}% > {self.thresholds['mesh_disagreement_pct']}%)")

        self.metrics_history.append({"timestamp": time.time(), "metrics": metrics, "triggers": triggers})

        if triggers:
            self.state = "HALTED"
            self.triggers = triggers
            return {"passed": False, "state": self.state, "triggers": triggers, "reasons": triggers}
        else:
            self.state = "RUNNING"
            return {"passed": True, "state": self.state, "triggers": [], "reasons": []}

    def reset(self):
        self.state = "RUNNING"
        self.triggers = []

    def status(self):
        return {
            "state": self.state,
            "triggers": self.triggers,
            "thresholds": self.thresholds,
            "history_count": len(self.metrics_history),
        }


if __name__ == "__main__":
    ks = KillSwitch()

    # If metrics JSON provided via stdin, evaluate
    raw = sys.stdin.read().strip()
    if raw:
        try:
            metrics = json.loads(raw)
        except:
            print("ROEL Kill Switch: invalid metrics JSON", file=sys.stderr)
            sys.exit(1)
        result = ks.evaluate(metrics)
        if result["passed"]:
            print(f"[ROEL-KILL] {result['state']} — no triggers")
            sys.exit(0)
        else:
            print(f"[ROEL-KILL] {result['state']} — ", "; ".join(result["triggers"]), file=sys.stderr)
            sys.exit(1)
    else:
        print(ks.status())
