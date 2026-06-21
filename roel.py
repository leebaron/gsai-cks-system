#!/usr/bin/env python3
"""
ROEL — Runtime Output Enforcement Layer v1.0
A hard gate on all CKS Telegram output.

Enforces (in order):
1. No markdown table syntax (| --- |)
2. State visibility tag (COMPLETE / PARTIAL / INFERRED) mandatory
3. No raw system code paths in user-facing output
4. Single format contract (bullet/paragraph, never mixed table)

Usage:
    python3 roel.py < intended_message.txt
    # or: pargs | python3 roel.py

Returns:
    exit 0 — output is clean, written to stdout
    exit 1 — output was rejected (message printed to stderr)
"""
import sys, re


STATE_TAGS = {"COMPLETE", "PARTIAL", "INFERRED"}
# These lines telegraph internal system structure
SYS_LEAK_PATTERNS = [
    r"~/gsai/",
    r"/gsai_kernel/",
    r"/gsai-cks-system/",
    r"cron job",
    r"isolated session",
    r"gateway config",
    r"openclaw\.sqlite",
    r"auth_profile",
]


def has_table_syntax(text: str) -> bool:
    """Detect markdown table: lines starting/ending with | and containing |"""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
            return True
        if re.match(r"^[\s\|:\-]+\|[\s\|:\-]+", stripped) and "---" in stripped:
            return True
    return False


def has_state_tag(text: str) -> bool:
    """Check if any STATE_TAG prefix exists as first non-whitespace token"""
    for line in text.split("\n"):
        stripped = line.strip().upper()
        for tag in STATE_TAGS:
            if stripped.startswith(tag) or stripped.startswith(f"[{tag}]"):
                return True
    return False


def has_system_leak(text: str) -> bool:
    """Check for internal system paths in user-facing message"""
    for pat in SYS_LEAK_PATTERNS:
        if re.search(pat, text):
            return True
    return False


def add_state_tag(text: str, tag: str = "COMPLETE") -> str:
    """Prepend state tag if missing"""
    if has_state_tag(text):
        return text
    return f"[{tag}] {text}"


def strip_tables(text: str) -> str:
    """Remove any line containing table syntax"""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2:
            continue
        if re.match(r"^[\s\|:\-]+\|[\s\|:\-]+", stripped) and "---" in stripped:
            continue
        lines.append(line)
    return "\n".join(lines)


def validate(text: str) -> dict:
    """Return pass/fail + cleaned text + reasons"""
    reasons = []
    original = text

    # Gate 1: Table syntax
    if has_table_syntax(text):
        text = strip_tables(text)
        if has_table_syntax(text):
            reasons.append("TABLE_SYNTAX_PERSISTS")
        else:
            reasons.append("TABLE_STRIPPED")

    # Gate 2: State visibility tag
    if not has_state_tag(text):
        text = add_state_tag(text)
        reasons.append("STATE_TAG_ADDED")

    # Gate 3: System leak
    if has_system_leak(text):
        reasons.append("SYSTEM_LEAK_DETECTED")
        return {"pass": False, "text": original, "reasons": reasons}

    passed = len([r for r in reasons if "PERSISTS" in r or "DETECTED" in r]) == 0

    return {"pass": passed, "text": text, "reasons": reasons}


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("[ERROR] ROEL: empty input", file=sys.stderr)
        sys.exit(1)

    result = validate(raw)
    if result["pass"]:
        sys.stdout.write(result["text"])
        sys.exit(0)
    else:
        print("[ROEL-REJECTED]", "; ".join(result["reasons"]), file=sys.stderr)
        print(result["text"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
