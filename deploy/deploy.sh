#!/usr/bin/env bash
# deploy/deploy.sh — CKS production deployment
set -euo pipefail

NAMESPACE="cks-system"
echo "🚀 CKS Deployment — namespace: $NAMESPACE"

kubectl apply -f deploy/docker/governance-deployment.yaml
kubectl apply -f deploy/docker/ledger-statefulset.yaml
kubectl apply -f deploy/docker/cocs-service.yaml
kubectl apply -f deploy/docker/runtime-deployment.yaml

echo "⏳ Waiting for pods..."
kubectl -n "$NAMESPACE" rollout status deployment/gsai-runtime --timeout=120s
kubectl -n "$NAMESPACE" rollout status deployment/cocs-gate --timeout=60s
kubectl -n "$NAMESPACE" rollout status deployment/governance-controller --timeout=60s

echo "✅ CKS deployment complete"
echo "  Runtime:   gsai-runtime.cks-system:8080"
echo "  COCS gate: cocs-gate.cks-system:9000"
echo "  Ledger:    ledger-0.ledger.cks-system:7000"
