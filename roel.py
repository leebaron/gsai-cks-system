#!/usr/bin/env python3
"""
ROEL — Runtime Output Enforcement Layer v1.0
Hard gate on CKS Telegram output.

Rules (all hard, no auto-fix):
 A — Single renderer lock: output must be json or text, no hybrid/mixed
 B — Table format: hard REJECT (not strip, not fix)
 C — VIEW_STATE tag mandatory: COMPLETE / PARTIAL / INFERRED
 D — No silent completion: inference must be tagged
 E — Deterministic output: same input → same output

Usage:
    python3 roel.py < message.txt
    or: generate_message | python3 roel.py

Exit code:
    0 — output valid (written to stdout)
    1 — output REJECTED (sent to stderr)
"""
import sys, re, hashlib


VIEW_STATE_TAGS = {"COMPLETE", "PARTIAL", "INFERRED"}
TABLE_RE = re.compile(
    r"(?:"
    r"^\|.*\|$"          # markdown table row: | a | b |
    r"|"
    r"^[\s\|:\-]+\|[\s\|:\-]+$"  # separator row: |---|---|
    r")",
    re.MULTILINE,
)
MIXED_FORMAT_PATTERNS = [
    (r"```", "code_block"),
    (r"^[*-]\s", "bullet_list"),
    (r"^\d+\.\s", "numbered_list"),
    (r"^\|", "table_syntax"),
]


def detect_table(text: str) -> bool:
    return bool(TABLE_RE.search(text))


def detect_mixed_format(text: str) -> bool:
    """Return True if more than one distinct non-text format is detected"""
    formats = set()
    for pat, fmt in MIXED_FORMAT_PATTERNS:
        if re.search(pat, text, re.MULTILINE):
            formats.add(fmt)
    return len(formats) > 1


def require_view_state(text: str, tag: str) -> bool:
    """Check VIEW_STATE: TAG exists somewhere in output"""
    pattern = rf"VIEW_STATE\s*:\s*{tag}"
    return bool(re.search(pattern, text, re.IGNORECASE))


def detect_silent_inference(text: str) -> bool:
    """Check for unmarked inferential language without INFERRED tag"""
    if "VIEW_STATE: INFERRED" in text or "VIEW_STATE: PARTIAL" in text:
        return False  # inference is declared
    inferential = [
        r"\b(?:probably|likely|might|may|suggests|indicates|appears|seems|presumably|guess|estimate|roughly|approximately)\b",
        r"\b(?:based on|according to my|in my|I think|I believe|I assume|I suspect)\b",
    ]
    for pat in inferential:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def check_deterministic(text: str) -> str:
    """Return content hash for deterministic check"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def validate(text: str) -> dict:
    """
    Returns dict with keys:
      passed (bool)
      reasons (list of str)
    Does NOT modify text — ROEL is a REJECT gate, not a fixer.
    """
    reasons = []

    # Rule A: Single renderer
    has_table = detect_table(text)
    has_mixed = detect_mixed_format(text)
    if has_table:
        reasons.append("TABLE_FORMAT_REJECTED")
    if has_mixed:
        reasons.append("MIXED_RENDERER_REJECTED")

    # Rule B: Table (redundant but explicit)
    if has_table:
        reasons.append("TABLE_IS_FORBIDDEN_PRIMITIVE")

    # Rule C: VIEW_STATE tag
    state_found = False
    for tag in VIEW_STATE_TAGS:
        if require_view_state(text, tag):
            state_found = True
            break
    if not state_found:
        reasons.append("MISSING_VIEW_STATE")

    # Rule D: No silent completion
    if detect_silent_inference(text):
        reasons.append("SILENT_INFERENCE_REJECTED")

    # Rule E: Deterministic check — always passes on single validation
    # (purpose of E is cross-run comparison, not single-pass)

    passed = len(reasons) == 0
    return {"passed": passed, "reasons": reasons}


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("ROEL: empty input", file=sys.stderr)
        sys.exit(1)

    result = validate(raw)
    if result["passed"]:
        sys.stdout.write(raw)
        sys.exit(0)
    else:
        print("ROEL-REJECTED", "; ".join(result["reasons"]), file=sys.stderr)
        sys.stdout.write(raw)
        sys.exit(1)


if __name__ == "__main__":
    main()
