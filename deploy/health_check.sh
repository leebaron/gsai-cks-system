#!/usr/bin/env bash
# deploy/health_check.sh — CKS production health check
set -euo pipefail

NAMESPACE="cks-system"
PASS=0
FAIL=0

echo "🩺 CKS Health Check"
echo ""

check() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd" 2>/dev/null; then
    echo "  ✅ $name"
    PASS=$((PASS+1))
  else
    echo "  ❌ $name"
    FAIL=$((FAIL+1))
  fi
}

check "Kernel alive" "kubectl -n $NAMESPACE exec deploy/gsai-runtime -- curl -sf http://localhost:8080/health"
check "COCS pass rate" "kubectl -n $NAMESPACE exec deploy/cocs-gate -- curl -sf http://localhost:9000/health"
check "Ledger consistent" "kubectl -n $NAMESPACE exec ledger-0 -- curl -sf http://localhost:7000/health"
check "Governance active" "kubectl -n $NAMESPACE exec deploy/governance-controller -- curl -sf http://localhost:8081/health"

echo ""
echo "  Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -eq 0 ]; then
  echo "  Status: HEALTHY"
else
  echo "  Status: DEGRADED"
  exit 1
fi
