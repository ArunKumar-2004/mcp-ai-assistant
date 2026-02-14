from models import Severity

class ScoringPolicy:
    def get_penalty_for_severity(self, severity: str) -> int:
        mapping = {
            "HIGH": 40,
            "MEDIUM": 20,
            "LOW": 5
        }
        return mapping.get(severity.upper(), 0)

    def get_penalty_for_drift(self) -> int:
        return 15

    def get_penalty_for_service_down(self) -> int:
        return 25

    def get_penalty_for_db_failure(self) -> int:
        return 50
