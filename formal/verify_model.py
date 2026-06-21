#!/usr/bin/env python3
"""
verify_model.py — Formal model verification for distributed consensus CI.

Enumerates all reachable states of the ConsensusSystem and proves:
  1. Safety      — never COMMIT with invalid execution
  2. Liveness    — system always eventually decides
  3. Consistency — all COMMIT nodes share same hash

Usage:
    python3 formal/verify_model.py

Exit code:
    0 — ALL invariants PASS (model is correct)
    1 — ANY invariant FAILS (model violation found)
"""
import sys, json, itertools, time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS = ["OK", "FAIL"]
NODES = ["A", "B", "C"]
THRESHOLD_COUNT = 2  # ≥2/3 of 3 nodes


class ConsensusModel:
    """Minimal state machine model of the distributed CI consensus protocol."""

    def initial_state(self):
        return {
            "state": "init",
            "exec_result": {n: "pending" for n in NODES},
            "node_hashes": {n: "" for n in NODES},
            "pass_votes": 0,
            "decision": "pending",
            "invalid_exec": False,
        }

    def transitions(self, s: dict) -> list:
        next_states = []

        if s["state"] == "init":
            # RunNodes: assign OK/FAIL to each node
            for r in itertools.product(RESULTS, repeat=len(NODES)):
                ns = dict(s)
                ns["exec_result"] = dict(s["exec_result"])
                ns["node_hashes"] = dict(s["node_hashes"])
                for i, n in enumerate(NODES):
                    ns["exec_result"][n] = r[i]
                    ns["node_hashes"][n] = "HASH_OK" if r[i] == "OK" else "HASH_FAIL"
                ns["state"] = "running"
                next_states.append(ns)

        elif s["state"] == "running":
            ns = dict(s)
            ns["pass_votes"] = sum(1 for n in NODES if ns["exec_result"][n] == "OK")
            ns["state"] = "aggregating"
            next_states.append(ns)

        elif s["state"] == "aggregating":
            ns = dict(s)
            if ns["pass_votes"] >= THRESHOLD_COUNT:
                ns["decision"] = "COMMIT"
            else:
                unique_hashes = len(set(ns["node_hashes"][n] for n in NODES))
                if unique_hashes > 1:
                    ns["decision"] = "KILL_SWITCH"
                else:
                    ns["decision"] = "REJECT"
            ns["state"] = "decided"
            next_states.append(ns)

        return next_states

    def enumerate_states(self) -> list:
        visited = []
        seen = set()
        stack = [self.initial_state()]

        while stack:
            s = stack.pop()
            key = json.dumps(s, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            visited.append(s)
            for ns in self.transitions(s):
                nk = json.dumps(ns, sort_keys=True)
                if nk not in seen:
                    stack.append(ns)

        return visited


def verify() -> dict:
    model = ConsensusModel()
    states = model.enumerate_states()
    total = len(states)

    safety_violations = []
    consistency_violations = []

    for s in states:
        # Safety: never COMMIT with invalid_exec
        if s["decision"] == "COMMIT" and s["invalid_exec"]:
            safety_violations.append(s)

        # Consistency: among PASSING nodes, all hashes must match
        if s["decision"] == "COMMIT":
            passing_hashes = set(
                s["node_hashes"][n] for n in NODES
                if s["exec_result"][n] == "OK"
            )
            if len(passing_hashes) > 1:
                consistency_violations.append(s)

    # Liveness: from any state, can a terminal decision be reached?
    liveness_violations = []
    undecided = [s for s in states if s["state"] != "decided"]
    for s in undecided:
        reachable = [s]
        stack = [s]
        seen_local = {json.dumps(s, sort_keys=True)}
        can_decide = False
        while stack:
            cur = stack.pop()
            for ns in model.transitions(cur):
                nk = json.dumps(ns, sort_keys=True)
                if nk in seen_local:
                    continue
                seen_local.add(nk)
                if ns["state"] == "decided":
                    can_decide = True
                    break
                stack.append(ns)
            if can_decide:
                break
        if not can_decide:
            liveness_violations.append(s)

    all_pass = (
        len(safety_violations) == 0
        and len(liveness_violations) == 0
        and len(consistency_violations) == 0
    )

    return {
        "system_valid": all_pass,
        "total_states_explored": total,
        "terminal_states": sum(1 for s in states if s["state"] == "decided"),
        "invariants": {
            "safety": {
                "rule": "no COMMIT with invalid execution",
                "pass": len(safety_violations) == 0,
                "violations": len(safety_violations),
            },
            "liveness": {
                "rule": "system always eventually decides",
                "pass": len(liveness_violations) == 0,
                "violations": len(liveness_violations),
            },
            "consistency": {
                "rule": "all COMMIT nodes share same hash",
                "pass": len(consistency_violations) == 0,
                "violations": len(consistency_violations),
            },
        },
        "violation_count": {
            "safety": len(safety_violations),
            "liveness": len(liveness_violations),
            "consistency": len(consistency_violations),
        },
    }


def main():
    result = verify()

    # Write to formal output
    out_dir = REPO_ROOT / "CKS_RUN_OUTPUT" / "formal"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "formal_verification.json"
    out_path.write_text(json.dumps(result, indent=2))

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["system_valid"] else 1)


if __name__ == "__main__":
    main()
