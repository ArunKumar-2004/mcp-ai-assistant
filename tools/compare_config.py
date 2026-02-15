from services.drivers.config_driver import DriftAnalyst
from services.llm_client import LLMClient
from services.config_service import ConfigService
import os
import logging

logger = logging.getLogger("config_tool")

class CompareEnvironmentConfigsTool:
    def __init__(self, analyst: DriftAnalyst = None, llm_client: LLMClient = None, config_service: ConfigService = None):
        self.analyst = analyst or DriftAnalyst()
        self.llm_client = llm_client or LLMClient()
        self.config_service = config_service or ConfigService()

    async def execute(self, env_1: str, env_2: str, integrity_mode: bool = False) -> dict:
        template_file = env_2
        if not os.path.exists(template_file):
            template_file = f"config/templates/{env_2}.yaml"
        
        try:
            # Real Configuration Fetching
            logger.info(f"Fetching actual configuration for environment: {env_1}")
            actual_data = self.config_service.fetch_environment_config(env_1)
            logger.info(f"Retrieved {len(actual_data)} configuration values from {env_1}")
        except RuntimeError as e:
            # Configuration not found - return proper error
            error_narration = self._generate_error_narration(str(e), template_file)
            return {
                "success": False,
                "error": {
                    "code": "CONFIG_FETCH_ERROR",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", f"Failed to fetch configuration for {env_1}."),
                    "suggested_fix": error_narration.get("suggested_fix", "Ensure environment configuration is available.")
                }
            }

        try:
            facts = self.analyst.compare_configs(template_file, actual_data, integrity_mode=integrity_mode)
            
            # AI Narrative Generation
            ai_narration = self._generate_ai_analysis(facts, env_1, env_2)
            
            return {
                "success": True,
                "data": {
                    "env_1": env_1,
                    "env_2": env_2,
                    "drift_detected": facts["drift_detected"],
                    "drift_keys": facts["drift_keys"],
                    "explanation": ai_narration.get("explanation", "Audit complete."),
                    "suggested_fix": ai_narration.get("suggested_fix", "No action required."),
                    "analysis_type": facts["analysis_type"],
                    "resolved_path": facts["resolved_path"]
                }
            }
        except Exception as e:
            # Even failures get AI-narrated responses
            error_narration = self._generate_error_narration(str(e), template_file)
            return {
                "success": False,
                "error": {
                    "code": "CONFIG_COMPARE_ERROR", 
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Internal audit failure."),
                    "suggested_fix": error_narration.get("suggested_fix", "Check system logs.")
                }
            }

    def _generate_ai_analysis(self, facts: dict, env_1: str, env_2: str) -> dict:
        """Synthesizes technical facts into a project-aware narrative."""
        mode = facts["analysis_type"]
        issues = facts["drift_keys"]
        
        prompt = (
            f"As an AI DevOps Specialist, interpret these configuration audit results.\n"
            f"Project Environment: {env_1}\n"
            f"Baseline Reference: {env_2}\n"
            f"Resolved Path: {facts['resolved_path']}\n"
            f"Operation Mode: {mode}\n"
            f"Technical Findings: {', '.join(issues) if issues else 'NONE'}\n\n"
            "Return JSON with 'explanation' and 'suggested_fix'. Ensure the tone is 'respective' "
            "and professional. Explain the technical significance of any gaps."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except Exception as e:
            logger.error(f"AI Narration failed: {e}")
            return {"explanation": "Audit complete based on raw findings.", "suggested_fix": "Review results manually."}

    def _generate_error_narration(self, error_msg: str, path: str) -> dict:
        """Narrates a tool failure using AI to provide helpful context."""
        prompt = (
            f"The configuration auditor encountered a failure.\n"
            f"Error Message: {error_msg}\n"
            f"Attempted Path: {path}\n"
            "Explain in plain, professional terms why this happened and how to fix it. Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"System error: {error_msg}", "suggested_fix": "Verify file paths and permissions."}
