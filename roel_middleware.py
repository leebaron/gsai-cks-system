#!/usr/bin/env python3
"""
ROEL Middleware v1.0 — Hard enforcement output gate.
Not a validator. A middleware that blocks output from escaping.

Flow:
  1. Generate candidate output
  2. ROEL validate (L1 syntax, L2 semantic, L3 determinism)
  3. PASS → send output
  4. HARD_REJECT → regenerate (max 3 retries)
  5. 3 failures → SYSTEM_FAILURE

Usage (wrapping generate step):
    python3 roel_middleware.py < candidate_output.txt
    exit 0 = output (stdout) — safe to send
    exit 1 = all retries exhausted — SYSTEM HALT
"""
import sys, re, hashlib, json, os
from pathlib import Path


ROOT = Path(__file__).parent
VIEW_STATE_TAGS = {"COMPLETE", "PARTIAL", "INFERRED"}
MAX_RETRIES = 3

# --- L1 Syntax Gate ---
TABLE_RE = re.compile(r"(?:^\|.*\|$|^[\s\|:\-]+\|[\s\|:\-]+$)", re.MULTILINE)
FORMAT_PATTERNS = [
    (r"```", "code_block"),
    (r"^[*-]\s", "bullet_list"),
    (r"^\d+\.\s", "numbered_list"),
    (r"^\|", "table_syntax"),
    (r"^>\s", "blockquote"),
]


class HARD_REJECT(Exception):
    """Raised when ROEL blocks output. Triggers retry or system halt."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


class ROELMiddleware:
    def __init__(self):
        self.retry_count = 0
        self.failures = []

    def _syntax_gate(self, text: str):
        # Table = immediate hard reject
        if TABLE_RE.search(text):
            raise HARD_REJECT("TABLE_FORBIDDEN")
        # Mixed format detection
        active = set()
        for pat, fmt in FORMAT_PATTERNS:
            if re.search(pat, text, re.MULTILINE):
                active.add(fmt)
        if len(active) > 1:
            raise HARD_REJECT(f"MIXED_FORMAT ({', '.join(sorted(active))})")

    def _semantic_gate(self, text: str):
        # VIEW_STATE tag mandatory
        has_tag = any(
            re.search(rf"VIEW_STATE\s*:\s*{tag}", text, re.IGNORECASE)
            for tag in VIEW_STATE_TAGS
        )
        if not has_tag:
            raise HARD_REJECT("MISSING_VIEW_STATE")
        # Silent inference
        if "VIEW_STATE: INFERRED" not in text:
            inferential = re.findall(
                r"\b(?:probably|likely|might|may|suggests|indicates|appears|seems|"
                r"presumably|guess|estimate|roughly|approximately|"
                r"I think|I believe|I assume|I suspect)\b",
                text, re.IGNORECASE,
            )
            if inferential:
                raise HARD_REJECT(f"SILENT_INFERENCE ({', '.join(set(inferential))})")

    def _determinism_gate(self, text: str, input_tag: str):
        cache_path = ROOT / ".roel_mid_cache.json"
        cache = {}
        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text())
            except:
                pass
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        if input_tag in cache:
            expected = cache[input_tag]
            if h != expected:
                raise HARD_REJECT(f"NON_DETERMINISTIC (expected {expected}, got {h})")
        cache[input_tag] = h
        cache_path.write_text(json.dumps(cache, indent=2))

    def enforce(self, text: str, input_tag: str = "default"):
        """Run all three gates. Raises HARD_REJECT on any violation."""
        self._syntax_gate(text)
        self._semantic_gate(text)
        self._determinism_gate(text, input_tag)

    def run(self, generate_fn, input_tag: str = "default"):
        """
        Middleware entry point. Loops up to MAX_RETRIES.
        generate_fn should return a string candidate.
        """
        self.retry_count = 0
        self.failures = []

        for attempt in range(1, MAX_RETRIES + 1):
            candidate = generate_fn(attempt)
            try:
                self.enforce(candidate, input_tag)
                # PASS — output is safe
                return {"passed": True, "output": candidate, "attempts": attempt}
            except HARD_REJECT as e:
                self.failures.append({"attempt": attempt, "reason": e.reason})
                self.retry_count += 1
                continue

        # All retries exhausted — SYSTEM FAILURE
        return {
            "passed": False,
            "output": None,
            "attempts": MAX_RETRIES,
            "failures": self.failures,
            "system_halt": True,
        }


def main():
    """Read candidate from stdin, run middleware loop (simulated)."""
    raw = sys.stdin.read()
    if not raw.strip():
        print("ROEL Middleware: empty input", file=sys.stderr)
        sys.exit(1)

    input_tag = os.environ.get("ROEL_INPUT_TAG", hashlib.sha256(raw.encode()).hexdigest()[:8])

    # Simulate middleware: first attempt passes through if valid
    middleware = ROELMiddleware()
    result = middleware.run(lambda attempt: raw, input_tag)

    if result["passed"]:
        sys.stdout.write(result["output"])
        sys.exit(0)
    else:
        print("ROEL SYSTEM HALT —", "; ".join(f.get("reason", "?") for f in result.get("failures", [])), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
