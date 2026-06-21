#!/usr/bin/env python3
"""
decision_engine.py — Self-healing CI decision engine.

Reads anomaly detection result and decides:
  OK         → PASS (deploy)
  ANOMALY    → ROLLBACK (revert commit)
  CRITICAL   → KILL_SWITCH (freeze pipeline)

Usage:
    python3 tools/decision_engine.py [anomaly_result.json]
    
Exit code:
    0 — PASS (deploy)
    2 — ROLLBACK
    3 — KILL_SWITCH
"""
import sys, json, time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_anomaly(path: str = None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    # Try default locations
    for p in [
        REPO_ROOT / "CKS_RUN_OUTPUT" / "artifact" / "anomaly_result.json",
        Path("anomaly_result.json"),
    ]:
        if p.exists():
            return json.loads(p.read_text())
    return {"status": "MISSING", "detail": "no anomaly result found"}


def decide(anomaly: dict) -> dict:
    status = anomaly.get("status", "UNKNOWN")
    checks = anomaly.get("checks", {})

    # Critical triggers
    severities = [c.get("severity", "none") for c in checks.values()]

    if "critical" in severities:
        decision = "KILL_SWITCH"
        exit_code = 3
        detail = "critical anomaly: " + ", ".join(
            k for k, v in checks.items() if v.get("severity") == "critical"
        )
    elif status in ("ANOMALY", "FAIL_RUNTIME", "FAIL_DETERMINISM", "FAIL_ROEL"):
        decision = "ROLLBACK"
        exit_code = 2
        detail = "anomaly detected: " + ", ".join(
            k for k, v in checks.items() if v.get("status") != "OK"
        )
    else:
        decision = "PASS"
        exit_code = 0
        detail = "all checks OK, ready for deploy"

    return {
        "decision": decision,
        "exit_code": exit_code,
        "detail": detail,
        "timestamp": time.time(),
    }


def main():
    anomaly = load_anomaly(sys.argv[1] if len(sys.argv) > 1 else None)
    result = decide(anomaly)
    print(json.dumps(result, indent=2))
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
