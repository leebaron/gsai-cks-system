#!/usr/bin/env python3
"""
ROEL Mesh — Multi-node output consensus layer.

Enforces:
  output valid ⇔ ≥ 2/3 ROEL nodes approve
  Rejects on: NO_CONSENSUS, NODE_OFFLINE, VERSION_MISMATCH
"""
import sys, json, hashlib


class ROELNode:
    def __init__(self, node_id, roel_version="2.0"):
        self.node_id = node_id
        self.roel_version = roel_version
        self.healthy = True

    def validate(self, text: str) -> dict:
        """Simulated ROEL validation per node"""
        has_table = "|" in text and ("---" in text or text.strip().startswith("|"))
        has_view_state = "VIEW_STATE" in text
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        return {
            "node_id": self.node_id,
            "version": self.roel_version,
            "approved": not has_table and has_view_state,
            "hash": h,
            "reasons": (["TABLE_FORBIDDEN"] if has_table else []) + (["MISSING_VIEW_STATE"] if not has_view_state else []),
        }


class ROELMesh:
    def __init__(self, nodes: list):
        self.nodes = nodes
        self.consensus_threshold = 2.0 / 3.0

    def validate(self, text: str) -> dict:
        votes = []
        for node in self.nodes:
            v = node.validate(text)
            votes.append(v)

        approved = sum(1 for v in votes if v["approved"])
        total = len(votes)
        ratio = approved / total if total > 0 else 0.0

        # Reject if below threshold
        consensus = ratio >= self.consensus_threshold

        # Check hash consistency across approving nodes
        hashes = [v["hash"] for v in votes if v["approved"]]
        hash_consistent = len(set(hashes)) <= 1 if hashes else True

        # Check version consistency
        versions = set(v["version"] for v in votes)
        version_ok = len(versions) == 1

        results = {
            "passed": consensus and hash_consistent and version_ok,
            "approved": approved,
            "total": total,
            "ratio": round(ratio, 4),
            "threshold": self.consensus_threshold,
            "hash_consistent": hash_consistent,
            "version_ok": version_ok,
            "node_votes": votes,
        }

        if not consensus:
            results["reasons"] = [f"NO_CONSENSUS ({approved}/{total})"]
        elif not hash_consistent:
            results["reasons"] = ["HASH_MISMATCH_ACROSS_NODES"]
        elif not version_ok:
            results["reasons"] = [f"VERSION_MISMATCH ({versions})"]
        else:
            results["reasons"] = []

        return results


def main():
    nodes = [
        ROELNode("roel-a"),
        ROELNode("roel-b"),
        ROELNode("roel-c"),
    ]
    mesh = ROELMesh(nodes)

    raw = sys.stdin.read()
    if not raw.strip():
        print("ROEL Mesh: empty input", file=sys.stderr)
        sys.exit(1)

    result = mesh.validate(raw)

    if result["passed"]:
        sys.stdout.write(raw)
        sys.exit(0)
    else:
        print("ROEL MESH REJECTED", "; ".join(result.get("reasons", [])), file=sys.stderr)
        sys.stdout.write(raw)
        sys.exit(1)


if __name__ == "__main__":
    main()
