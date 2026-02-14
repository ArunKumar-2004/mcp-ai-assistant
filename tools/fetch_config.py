from services.llm_client import LLMClient
import logging

logger = logging.getLogger("fetch_config_tool")

class FetchEnvironmentConfigTool:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    async def execute(self, environment: str) -> dict:
        try:
            # Deterministic Fact Gathering
            # In a real system, this would fetch from Vault, S3, or a DB
            facts = {
                "DB_URL": "postgres://localhost:5432/db",
                "REDIS_TTL": 3600,
                "API_VERSION": "v1.2.0"
            }
            
            # AI Narration of the fetch event
            ai_narration = self._generate_ai_status(environment, True)

            return {
                "success": True,
                "data": {
                    "environment": environment,
                    "config": facts,
                    "explanation": ai_narration.get("explanation", f"Configurations for {environment} retrieved."),
                    "suggested_fix": ai_narration.get("suggested_fix", "No action required.")
                }
            }
        except Exception as e:
            error_narration = self._generate_error_narration(str(e), environment)
            return {
                "success": False,
                "error": {
                    "code": "FETCH_CONFIG_ERROR",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Failed to retrieve configuration snapshots."),
                    "suggested_fix": error_narration.get("suggested_fix", "Check environment availability.")
                }
            }

    def _generate_ai_status(self, env: str, success: bool) -> dict:
        """Briefly narrates the status of the configuration retrieval."""
        prompt = (
            f"As a Cloud Architect, provide a brief, professional confirmation of configuration retrieval.\n"
            f"Environment: {env}\n"
            f"Status: SUCCESS\n\n"
            "Return a JSON object with 'explanation' and 'suggested_fix'. The tone should be authoritative and helpful."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"Environment configurations for {env} successfully synchronized.", "suggested_fix": "No action required."}

    def _generate_error_narration(self, error_msg: str, env: str) -> dict:
        """Narrates a config fetch failure using AI."""
        prompt = (
            f"The configuration loader encountered a failure for environment '{env}'.\n"
            f"Error: {error_msg}\n\n"
            "Explain in professional terms why this happened. Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"Failed to load context for {env}: {error_msg}", "suggested_fix": "Verify access to the configuration store."}
