# CKS Runtime — Observation Operator
class ObservationOperator:
    def ground(self, raw_input):
        return {"value": raw_input, "grounded": True, "confidence": 1.0}
