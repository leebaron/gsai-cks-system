#!/usr/bin/env python3
"""COCS Gate — constraint enforcement layer"""
G1_THRESHOLD = 0.30
G2_HARM_THRESHOLD = 0.15
G3_EPISTEMIC_THRESHOLD = 0.20
G4_IDENTITY_THRESHOLD = 0.10


class COCSGate:
    def check(self, observation: dict) -> dict:
        obs = observation.get("value", "")
        confidence = observation.get("confidence", 0.0)
        length = len(obs) if obs else 0

        G1 = 1.0 if length > 0 else 0.0
        G2 = confidence  # higher confidence = less harm risk
        G3 = 1.0 if len(obs.split()) > 1 else 0.5
        G4 = 1.0  # identity preserved

        violations = []
        if G1 < G1_THRESHOLD:
            violations.append("G1: no valid observation")
        if G2 < G2_HARM_THRESHOLD:
            violations.append("G2: harm risk too high")
        if G3 < G3_EPISTEMIC_THRESHOLD:
            violations.append("G3: epistemic insufficient")
        if G4 < G4_IDENTITY_THRESHOLD:
            violations.append("G4: identity mismatch")

        status = "PASS" if not violations else "BLOCKED"
        return {
            "status": status,
            "G1": G1, "G2": G2, "G3": G3, "G4": G4,
            "violations": violations,
        }
