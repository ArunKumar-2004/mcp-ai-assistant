from .policy_engine import ScoringPolicy
from models import ReadinessStatus, Recommendation
from services.llm_client import LLMClient

class CalculateReadinessScoreTool:
    def __init__(self, policy: ScoringPolicy = None, llm_client: LLMClient = None):
        self.policy = policy or ScoringPolicy()
        self.llm_client = llm_client or LLMClient()

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
            
        # Final AI-First Executive Summary
        ai_res = self._generate_ai_executive_summary(score, status, penalties)

        return {
            "success": True,
            "data": {
                "readiness_score": score,
                "status": status,
                "penalties": penalties,
                "recommendation": recommendation,
                "explanation": ai_res.get("explanation", f"Score: {score}. Status: {status.value}."),
                "suggested_fix": ai_res.get("suggested_fix", "Address identified risks.")
            }
        }

    def _generate_ai_executive_summary(self, score: int, status: ReadinessStatus, penalties: list) -> dict:
        """Uses AI to synthesize a 'respective' executive summary of the entire deployment readiness."""
        prompt = (
            f"As an AI Deployment Auditor, provide an executive summary of the readiness for this release.\n"
            f"Numerical Score: {score}/100\n"
            f"Status Level: {status.value}\n"
            f"Identified Risks/Penalties:\n" + "\n".join([f"- {p}" for p in penalties]) + "\n\n"
            "Return a JSON object with two fields:\n"
            "1. 'explanation': A professional, informative summary of the readiness state.\n"
            "2. 'suggested_fix': A long-term remediation strategy to reach 100/100 readiness.\n"
            "The tone should be authoritative yet helpful and provide 'respective' feedback."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except Exception as e:
            return {
                "explanation": f"Readiness Score: {score}/100. Status: {status.value.upper()}.",
                "suggested_fix": "Review technical diagnostics manually."
            }
