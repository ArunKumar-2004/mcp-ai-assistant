from services.drivers.health_driver import DeepHealthDriver
from services.llm_client import LLMClient
import logging

logger = logging.getLogger("health_tool")

class CheckServiceHealthTool:
    def __init__(self, driver: DeepHealthDriver = None, llm_client: LLMClient = None):
        self.driver = driver or DeepHealthDriver()
        self.llm_client = llm_client or LLMClient()

    async def execute(self, service_name: str, health_url: str) -> dict:
        try:
            # Deterministic Fact Gathering
            facts = await self.driver.check_service(health_url)
            
            # AI Narrative Generation
            ai_narration = self._generate_ai_analysis(facts, service_name, health_url)
            
            return {
                "success": True,
                "data": {
                    "service_name": service_name,
                    "health_url": health_url,
                    "status": facts["status"],
                    "latency_ms": facts["latency_ms"],
                    "http_code": facts["http_code"],
                    "explanation": ai_narration.get("explanation", f"{service_name} status: {facts['status']}"),
                    "suggested_fix": ai_narration.get("suggested_fix", "No action required.")
                }
            }
        except Exception as e:
            # Even failures get AI-narrated responses
            error_narration = self._generate_error_narration(str(e), service_name, health_url)
            return {
                "success": False,
                "error": {
                    "code": "HEALTH_CHECK_ERROR", 
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Health check execution failed."),
                    "suggested_fix": error_narration.get("suggested_fix", "Check network and URL.")
                }
            }

    def _generate_ai_analysis(self, facts: dict, service_name: str, url: str) -> dict:
        """Synthesizes technical facts into a project-aware narrative."""
        prompt = (
            f"As a Site Reliability Engineer, analyze this health check result for '{service_name}'.\n"
            f"Endpoint: {url}\n"
            f"Technical Status: {facts['status']}\n"
            f"HTTP Response: {facts['http_code']}\n"
            f"Latency: {facts['latency_ms']}ms\n\n"
            "Return JSON with 'explanation' and 'suggested_fix'. The 'explanation' should "
            "be a professional summary of the service health. The 'suggested_fix' should "
            "provide optimization or recovery steps if the service is underperforming or down."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except Exception as e:
            logger.error(f"AI Narration failed: {e}")
            return {"explanation": f"Health check for {service_name} completed.", "suggested_fix": "Review results manually."}

    def _generate_error_narration(self, error_msg: str, service_name: str, url: str) -> dict:
        """Narrates a tool failure using AI to provide helpful context."""
        prompt = (
            f"The health auditor encountered an error checking {service_name}.\n"
            f"Error Message: {error_msg}\n"
            f"Target URL: {url}\n"
            "Explain in professional terms why this check failed and how to resolve it. Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"System error: {error_msg}", "suggested_fix": "Verify the health endpoint URL."}
