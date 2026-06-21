---
name: Violation / Drift Report
about: Report a constraint violation or reality drift
title: '[VIOLATION] '
labels: violation
assignees: ''

---

## Detection

- **Type:** constraint_violation / reality_drift / ledger_inconsistency
- **Detected at:** [timestamp]
- **Confidence:** [0.0–1.0]

## Details

**What was observed:**
[Description of the violation or drift]

**Expected vs actual:**

| Property | Expected | Actual |
|----------|----------|--------|
| [G1/G2/G3/G4] | [PASS] | [FAIL] |

## Response

- [ ] RAL audit triggered
- [ ] Drift analysis initiated
- [ ] Rollback evaluated
- [ ] Kill switch assessed

---

_Violation reports automatically trigger reality_check.yml._
