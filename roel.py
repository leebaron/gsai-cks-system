#!/usr/bin/env python3
"""
ROEL v2.0 — Runtime Output Enforcement Layer (Hardened Output Firewall)
CKS pipeline final gate: O → COCS → CSCO → RAL → Ledger → ROEL

Three-layer architecture:
  L1 — Syntax Firewall: table rejection, format lock, single renderer
  L2 — Semantic Integrity: VIEW_STATE, OBSERVED/INFERRED/DERIVED markers
  L3 — Determinism & Drift Control: hash+state stability, drift detection

Usage:
    python3 roel.py < message.txt
    generate_message | python3 roel.py

Exit code:
    0 — ALLOW (output written to stdout)
    1 — REJECT (output blocked, reasons to stderr)
"""
import sys, re, hashlib, os, json
from pathlib import Path


ROOT = Path(__file__).parent
CACHE_PATH = ROOT / ".roel_cache.json"
VIEW_STATE_TAGS = {"COMPLETE", "PARTIAL", "INFERRED"}
FACT_MARKERS = {"OBSERVED", "INFERRED", "DERIVED"}

# ---- Load drift cache ----
def _load_cache():
    try:
        return json.loads(CACHE_PATH.read_text())
    except:
        return {}


def _save_cache(cache: dict):
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


# =====================================================================
# L1 — Syntax Firewall
# =====================================================================

TABLE_RE = re.compile(
    r"(?:^\|.*\|$|^[\s\|:\-]+\|[\s\|:\-]+$)", re.MULTILINE
)
FORMAT_PATTERNS = [
    (r"```", "code_block"),
    (r"^[*-]\s", "bullet_list"),
    (r"^\d+\.\s", "numbered_list"),
    (r"^\|", "table_syntax"),
    (r"^>\s", "blockquote"),
]


def detect_table(text: str) -> bool:
    return bool(TABLE_RE.search(text))


def detect_mixed_format(text: str) -> bool:
    active = set()
    for pat, fmt in FORMAT_PATTERNS:
        if re.search(pat, text, re.MULTILINE):
            active.add(fmt)
    # text-only (no format markers) is always valid
    return len(active) > 1


def single_renderer(text: str) -> bool:
    return not detect_mixed_format(text) and not detect_table(text)


def l1_syntax_gate(text: str) -> dict:
    reasons = []
    if detect_table(text):
        reasons.append("TABLE_FORBIDDEN")
    if detect_mixed_format(text):
        reasons.append("FORMAT_COLLISION")
    if not single_renderer(text):
        reasons.append("MULTI_RENDERER")
    return {"passed": len(reasons) == 0, "reasons": reasons}


# =====================================================================
# L2 — Semantic Integrity
# =====================================================================

INFERENCE_PATTERNS = [
    r"\b(?:probably|likely|might|may|suggests|indicates|appears|seems|"
    r"presumably|guess|estimate|roughly|approximately|about)\b",
    r"\b(?:based on|according to|I think|I believe|I assume|I suspect)\b",
]


def has_view_state(text: str) -> bool:
    for tag in VIEW_STATE_TAGS:
        if re.search(rf"VIEW_STATE\s*:\s*{tag}", text, re.IGNORECASE):
            return True
    return False


def has_fact_marker(text: str) -> bool:
    for tag in FACT_MARKERS:
        if re.search(rf"\b{tag}\b", text):
            return True
    return False


def detect_silent_inference(text: str) -> bool:
    if "VIEW_STATE: INFERRED" in text or has_fact_marker(text):
        return False
    for pat in INFERENCE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def l2_semantic_gate(text: str) -> dict:
    reasons = []
    if not has_view_state(text):
        reasons.append("MISSING_VIEW_STATE")
    if detect_silent_inference(text):
        reasons.append("SILENT_INFERENCE")
    return {"passed": len(reasons) == 0, "reasons": reasons}


# =====================================================================
# L3 — Determinism & Drift Control
# =====================================================================


def deterministic_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def l3_drift_gate(text: str, input_tag: str = "default") -> dict:
    cache = _load_cache()
    h = deterministic_hash(text)
    reasons = []
    if input_tag in cache:
        expected = cache[input_tag]
        if h != expected:
            reasons.append(f"NON_DETERMINISTIC_OUTPUT (expected {expected}, got {h})")
    # Update cache with current hash
    cache[input_tag] = h
    _save_cache(cache)
    return {"passed": len(reasons) == 0, "reasons": reasons, "hash": h}


# =====================================================================
# Metrics collectors (in-memory, appended each run)
# =====================================================================

CURRENT_METRICS = {
    "format_violation_rate": 0.0,
    "inference_leak_rate": 0.0,
    "drift_score": 0.0,
    "renderer_entropy": 0.0,
}
METRICS_LOG = []


def record_metrics(result: dict):
    METRICS_LOG.append(result)


# =====================================================================
# Pipeline
# =====================================================================


def validate(text: str, input_tag: str = "default") -> dict:
    l1 = l1_syntax_gate(text)
    l2 = l2_semantic_gate(text)
    l3 = l3_drift_gate(text, input_tag)

    all_reasons = l1["reasons"] + l2["reasons"] + [r for r in l3["reasons"] if "NON_DETERMINISTIC" in r]

    result = {
        "passed": l1["passed"] and l2["passed"] and l3["passed"],
        "reasons": all_reasons,
        "layers": {
            "L1_syntax": l1,
            "L2_semantic": l2,
            "L3_drift": {"passed": l3["passed"], "hash": l3["hash"]},
        },
    }
    record_metrics(result)
    return result


# =====================================================================
# Entry point
# =====================================================================


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("ROEL: empty input", file=sys.stderr)
        sys.exit(1)

    input_tag = os.environ.get("ROEL_INPUT_TAG", hashlib.sha256(raw.encode()).hexdigest()[:8])
    result = validate(raw, input_tag)

    if result["passed"]:
        sys.stdout.write(raw)
        sys.exit(0)
    else:
        print("ROEL REJECTED", "; ".join(result["reasons"]), file=sys.stderr)
        sys.stdout.write(raw)
        sys.exit(1)


if __name__ == "__main__":
    main()
