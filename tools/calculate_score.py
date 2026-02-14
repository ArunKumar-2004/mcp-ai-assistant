from .policy_engine import ScoringPolicy
from models import ReadinessStatus, Recommendation

class CalculateReadinessScoreTool:
    def __init__(self, policy: ScoringPolicy = None):
        self.policy = policy or ScoringPolicy()

    async def execute(self, log_analysis: dict, drift_analysis: dict, health_checks: list, db_status: str) -> dict:
        penalties = []
        score = 100
        
        # 1. Log Severity Penalty
        severity = log_analysis.get("severity", "LOW")
        penalty = self.policy.get_penalty_for_severity(severity)
        if penalty > 0:
            score -= penalty
            penalties.append(f"Build log severity {severity}: -{penalty}")
            
        # 2. Drift Penalty
        if drift_analysis.get("drift_detected"):
            penalty = self.policy.get_penalty_for_drift()
            score -= penalty
            penalties.append(f"Config drift detected: -{penalty}")
            
        # 3. Health Checks Penalty
        for hc in health_checks:
            if hc.get("status") == "DOWN":
                penalty = self.policy.get_penalty_for_service_down()
                score -= penalty
                penalties.append(f"Service {hc.get('service_name')} is DOWN: -{penalty}")
                
        # 4. DB Status Penalty
        if db_status == "FAILED":
            penalty = self.policy.get_penalty_for_db_failure()
            score -= penalty
            penalties.append(f"Database connection failed: -{penalty}")
            
        # Final status and recommendation
        score = max(0, score)
        if score >= 80:
            status = ReadinessStatus.SAFE
            recommendation = Recommendation.ALLOW_AUTOMATION
        elif score >= 50:
            status = ReadinessStatus.CAUTION
            recommendation = Recommendation.BLOCK_AUTOMATION
        else:
            status = ReadinessStatus.NOT_SAFE
            recommendation = Recommendation.BLOCK_AUTOMATION
            
        return {
            "success": True,
            "data": {
                "readiness_score": score,
                "status": status,
                "penalties": penalties,
                "recommendation": recommendation,
                "explanation": f"Readiness Score: {score}/100. Status: {status.value.upper()}. {len(penalties)} risks identified.",
                "suggested_fix": "Address the highest severity penalties in the audit report to improve the score." if penalties else "No immediate action required."
            }
        }
