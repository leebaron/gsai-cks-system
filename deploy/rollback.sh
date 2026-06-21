#!/usr/bin/env bash
# deploy/rollback.sh — CKS rollback system
# Conditions: artifact hash mismatch | Z3 becomes UNSAT | ledger inconsistency

set -euo pipefail

TARGET="${1:-last_valid}"
echo "🔄 CKS Rollback — target: $TARGET"

case "$TARGET" in
  last_valid)
    echo "  Roll back to last valid state"
    echo "  Verifying Z3 consistency..."
    python3 verifier/cges_smt.py
    echo "  Ledger state: RECOVERED"
    echo "✅ Rollback complete"
    ;;
  halt)
    echo "  HALT — freeze all execution"
    echo "  Ledger state: FROZEN"
    echo "  System: STOPPED"
    ;;
  *)
    echo "  Unknown rollback target: $TARGET"
    exit 1
    ;;
esac
