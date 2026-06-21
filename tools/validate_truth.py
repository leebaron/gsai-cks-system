#!/usr/bin/env python3
"""
Truth Validator v1.0
Validates execution graph against truth rules.

Truth rules:
  pytest exit_code == 0
  ROEL gate passes (exit 0 for clean input)
  ROEL table rejection triggers (exit 1 for table)
  Hash chain validates (chain_valid == True)

Usage:
    python3 tools/validate_truth.py [execution_graph.json]
    cat execution_graph.json | python3 tools/validate_truth.py
"""
import sys, json


def validate(graph: dict) -> dict:
    checks = {}
    all_pass = True

    # Check 1: pytest
    pytest = graph.get("execution", {}).get("pytest", {})
    pytest_pass = pytest.get("exit_code") == 0
    checks["pytest"] = {
        "rule": "pytest exit_code == 0",
        "actual": pytest.get("exit_code"),
        "pass": pytest_pass,
        "evidence": pytest.get("log_hash", ""),
    }
    if not pytest_pass:
        all_pass = False

    # Check 2: ROEL gate (clean input should pass)
    roel_gate = graph.get("execution", {}).get("roel_gate", {})
    roel_pass = roel_gate.get("gate_passed") == True
    checks["roel_gate"] = {
        "rule": "ROEL gate passes for clean input",
        "actual": roel_gate.get("exit_code"),
        "pass": roel_pass,
        "evidence": roel_gate.get("log_hash", ""),
    }
    if not roel_pass:
        all_pass = False

    # Check 3: ROEL table rejection
    roel_reject = graph.get("execution", {}).get("roel_table_reject", {})
    table_blocked = roel_reject.get("table_blocked") == True
    checks["roel_table_reject"] = {
        "rule": "ROEL rejects table input (exit 1)",
        "actual": roel_reject.get("exit_code"),
        "pass": table_blocked,
        "evidence": roel_reject.get("log_hash", ""),
    }
    if not table_blocked:
        all_pass = False

    # Check 4: Hash chain
    chain = graph.get("execution", {}).get("hash_chain", {})
    chain_valid = chain.get("chain_valid") == True
    checks["hash_chain"] = {
        "rule": "ledger hash chain validates",
        "actual": chain.get("exit_code"),
        "pass": chain_valid,
        "evidence": chain.get("log_hash", ""),
    }
    if not chain_valid:
        all_pass = False

    # Check 5: Commit exists
    commit = graph.get("commit", "")
    commit_exists = bool(commit) and commit != "unknown"
    checks["commit_binding"] = {
        "rule": "commit SHA exists and is bound",
        "actual": commit[:12] if commit else "MISSING",
        "pass": commit_exists,
        "evidence": commit,
    }
    if not commit_exists:
        all_pass = False

    return {
        "system_valid": all_pass,
        "checks_passed": sum(1 for c in checks.values() if c["pass"]),
        "checks_total": len(checks),
        "checks": checks,
    }


def main():
    path = None
    if len(sys.argv) > 1:
        path = sys.argv[1]
        try:
            with open(path) as f:
                graph = json.load(f)
        except Exception as e:
            print(json.dumps({"error": f"cannot read {path}: {e}"}))
            sys.exit(1)
    else:
        raw = sys.stdin.read().strip()
        if raw:
            graph = json.loads(raw)
        else:
            print(json.dumps({"error": "no input"}))
            sys.exit(1)

    result = validate(graph)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["system_valid"] else 1)


if __name__ == "__main__":
    main()
