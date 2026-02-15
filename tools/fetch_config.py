from services.llm_client import LLMClient
from services.config_service import ConfigService
import logging

logger = logging.getLogger("fetch_config_tool")

class FetchEnvironmentConfigTool:
    def __init__(self, config_service: ConfigService = None, llm_client: LLMClient = None):
        self.config_service = config_service or ConfigService()
        self.llm_client = llm_client or LLMClient()

    async def execute(self, environment: str) -> dict:
        try:
            # Real Configuration Fetching
            logger.info(f"Fetching configuration for environment: {environment}")
            config = self.config_service.fetch_environment_config(environment)
            
            # AI Narration of the fetch event
            ai_narration = self._generate_ai_status(environment, config, True)

            return {
                "success": True,
                "data": {
                    "environment": environment,
                    "config": config,
                    "config_keys": list(config.keys()),
                    "config_count": len(config),
                    "explanation": ai_narration.get("explanation", f"Configurations for {environment} retrieved."),
                    "suggested_fix": ai_narration.get("suggested_fix", "No action required.")
                }
            }
        except RuntimeError as e:
            # Configuration not found - proper error handling
            error_narration = self._generate_error_narration(str(e), environment)
            return {
                "success": False,
                "error": {
                    "code": "CONFIG_NOT_FOUND",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Failed to retrieve configuration."),
                    "suggested_fix": error_narration.get("suggested_fix", "Check environment configuration sources.")
                }
            }
        except Exception as e:
            # Unexpected error
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

    def _generate_ai_status(self, env: str, config: dict, success: bool) -> dict:
        """Briefly narrates the status of the configuration retrieval."""
        prompt = (
            f"As a Cloud Architect, provide a brief, professional confirmation of configuration retrieval.\n"
            f"Environment: {env}\n"
            f"Status: SUCCESS\n"
            f"Configuration Keys Retrieved: {', '.join(list(config.keys())[:10])}\n"
            f"Total Keys: {len(config)}\n\n"
            "Return a JSON object with 'explanation' and 'suggested_fix'. The tone should be authoritative and helpful."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {
                "explanation": f"Environment configurations for {env} successfully synchronized. Retrieved {len(config)} configuration values.",
                "suggested_fix": "No action required."
            }

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
            return {
                "explanation": f"Failed to load context for {env}: {error_msg}",
                "suggested_fix": "Verify access to the configuration store or set environment variables."
            }
