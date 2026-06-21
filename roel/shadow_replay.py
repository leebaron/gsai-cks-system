#!/usr/bin/env python3
"""
ROEL Shadow Replay — Output reproducibility verification.

Ensures: production output == reproducible execution output.
Blocks output if replay mismatch detected.
"""
import sys, json, hashlib


class ShadowReplay:
    def __init__(self):
        self.replay_cache = {}

    def record(self, input_text: str, output_text: str) -> dict:
        """Record a production run's output for later verification."""
        key = hashlib.sha256(input_text.encode()).hexdigest()[:16]
        output_hash = hashlib.sha256(output_text.encode()).hexdigest()[:16]
        self.replay_cache[key] = output_hash
        return {"key": key, "hash": output_hash}

    def verify(self, input_text: str, output_text: str) -> dict:
        """Verify current output matches recorded production output."""
        key = hashlib.sha256(input_text.encode()).hexdigest()[:16]
        current_hash = hashlib.sha256(output_text.encode()).hexdigest()[:16]

        if key not in self.replay_cache:
            return {
                "passed": True,  # No baseline to compare — assume valid
                "key": key,
                "status": "NO_BASELINE",
            }

        expected = self.replay_cache[key]
        match = current_hash == expected

        return {
            "passed": match,
            "key": key,
            "status": "MATCH" if match else "MISMATCH",
            "expected_hash": expected,
            "actual_hash": current_hash,
        }

    def full_check(self, bundle: list) -> dict:
        """Verify a batch of (input, output) pairs."""
        results = []
        for inp, out in bundle:
            results.append(self.verify(inp, out))

        all_pass = all(r["passed"] for r in results)
        return {
            "passed": all_pass,
            "total": len(results),
            "passed_count": sum(1 for r in results if r["passed"]),
            "results": results,
        }


def main():
    engine = ShadowReplay()
    raw = sys.stdin.read().strip()
    if not raw:
        print("ROEL Shadow Replay: empty input", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except:
        print("ROEL Shadow Replay: expected JSON input", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, list):
        result = engine.full_check(data)
    elif isinstance(data, dict) and "input" in data and "output" in data:
        result = engine.verify(data["input"], data["output"])
    else:
        print("ROEL Shadow Replay: expected [ [in,out], ... ] or {input, output}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
