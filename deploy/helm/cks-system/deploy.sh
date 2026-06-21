#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:-cks-system}"
MODE="${2:-enforce}"

echo "🚀 CKS Helm Deploy"
echo "  Namespace: $NAMESPACE"
echo "  Mode: $MODE"

helm upgrade --install cks-system deploy/helm/cks-system \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --set mode="$MODE"

echo ""
echo "⏳ Waiting for rollout..."
kubectl -n "$NAMESPACE" rollout status deployment/gsai-runtime --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/cocs-gate --timeout=60s
kubectl -n "$NAMESPACE" rollout status deployment/governance-controller --timeout=60s

echo ""
echo "✅ CKS production deployment complete"
echo "  Runtime:   gsai-runtime.$NAMESPACE:8080"
echo "  COCS gate: cocs-gate.$NAMESPACE:9000"
echo "  Ledger:    ledger-0.ledger.$NAMESPACE:7000"
echo ""
echo "  Mode: $MODE"
echo "  Rollout phase:"
echo "    1=shadow       (observe only)"
echo "    2=soft          (warnings only)"
echo "    3=enforce       (blocking gate) ← default"
echo "    4=autonomy      (self-governed)"
