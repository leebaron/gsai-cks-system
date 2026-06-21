# CKS v1.0 Helm Chart — Production Deployment

**One-command deploy:**
```
helm install gsai ./deploy/helm/cks-system --namespace cks-system --create-namespace
```

**Upgrade:**
```
helm upgrade gsai ./deploy/helm/cks-system
```

**Rollback:**
```
helm rollback gsai 1
```

## Components

| Component | Type | Port | Description |
|-----------|------|------|-------------|
| Runtime | Deployment (x3) | 8080 | Core pipeline: O → C → E |
| COCS Gate | Deployment (x2) | 9000 | M_valid constraint enforcement |
| Ledger | StatefulSet (x1) | 7000 | Append-only immutable audit |
| Governance | Deployment (x1) | 8081 | CCP + MG + RAL controller |
| Observation | Deployment (x1) | 8082 | Grounding/normalize/extract |
| ConfigMap | — | — | System-wide configuration |

## Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| replicaCount | 3 | Runtime pod count |
| cocs.mode | enforce | enforce / audit / shadow |
| governance.mode | strict | strict / shadow / audit |
| ral.threshold | 0.95 | Reality alignment minimum |
| rolloutPhase | 3 | 1=shadow, 2=soft, 3=enforce, 4=autonomy |
| ledger.storage | 10Gi | Persistent volume size |
| ingress.host | gsai.local | External access hostname |

## Architecture

```
Ingress (gsai.local:80)
  ↓
Runtime Pod (port 8080)
  ↓
Observation Operator (O)
  ↓
COCS Constraint Gate (M_valid)
  ↓
Governance Policy (CCP + MG)
  ↓
Execution Engine
  ↓
Ledger (append-only, StatefulSet)
  ↓
RAL Reality Check
```

## Rollout Phases

1. **Shadow** — run parallel, observe, no enforcement
2. **Soft** — COCS warnings only, no blocking
3. **Enforce** — COCS is blocking gate (default)
4. **Autonomy** — self-governed under constraints
