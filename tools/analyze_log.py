from services.llm_client import LLMClient
from models import LogCategory, Severity
import json

class AnalyzeBuildLogTool:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    async def execute(self, log_text: str) -> dict:
        prompt = (
            "As an AI Build Engineer, analyze this build log to identify the root cause of failure.\n"
            "Raw Log Content:\n"
            f"{log_text[:5000]}\n\n" # Truncate if too long for prompt
            "Return a JSON object with these keys:\n"
            "1. 'category': (INFRA|CODE|CONFIG|DEPENDENCY|FLAKY)\n"
            "2. 'severity': (LOW|MEDIUM|HIGH)\n"
            "3. 'confidence': (float 0-1)\n"
            "4. 'explanation': A professional, technical explanation of the root cause.\n"
            "5. 'suggested_fix': Concrete, actionable steps to resolve the issue.\n"
            "The tone should be 'respective', direct, and highly professional."
        )
        
        try:
            analysis = self.llm_client.generate_with_tools(prompt)
            validated = self._validate_llm_response(analysis)
            return {
                "success": True,
                "data": validated
            }
        except Exception as e:
            # Even if the analysis fails, use AI to narrate the system failure
            error_narration = self._generate_error_narration(str(e))
            return {
                "success": False,
                "error": {
                    "code": "ANALYSIS_ERROR",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "The log analysis engine encountered an internal error."),
                    "suggested_fix": error_narration.get("suggested_fix", "Review logs manually or retry.")
                }
            }

    def _validate_llm_response(self, response: dict) -> dict:
        if not isinstance(response, dict):
             raise ValueError("LLM response is not a dict")
             
        return {
            "category": str(response.get("category", LogCategory.INFRA)).upper(),
            "severity": str(response.get("severity", Severity.MEDIUM)).upper(),
            "confidence": float(response.get("confidence", 0.5)),
            "explanation": response.get("explanation", "Unknown cause."),
            "suggested_fix": response.get("suggested_fix", "Manual review required.")
        }

    def _generate_error_narration(self, error_msg: str) -> dict:
        """Narrates a log analysis failure using AI."""
        prompt = (
            f"The build log analysis engine encountered an internal error: {error_msg}\n"
            "Explain in professional terms why the AI analysis failed and what the user should do. "
            "Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            # Use a very short timeout/simple call for error narration
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {
                "explanation": "Diagnostic engine timeout during log analysis.",
                "suggested_fix": "Please check the build logs manually for high-priority errors."
            }
