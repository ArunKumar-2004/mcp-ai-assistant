from services.drivers.config_driver import DriftAnalyst
import os

class CompareEnvironmentConfigsTool:
    def __init__(self, analyst: DriftAnalyst = None):
        self.analyst = analyst or DriftAnalyst()

    async def execute(self, env_1: str, env_2: str, integrity_mode: bool = False) -> dict:
        """
        env_1: The current target environment (e.g. staging)
        env_2: The baseline environment or repo template
        """
        # Use the provided template path directly if it exists, 
        # otherwise fall back to the legacy template folder logic.
        template_file = env_2
        if not os.path.exists(template_file):
            template_file = f"config/templates/{env_2}.yaml"
        
        # Simulated 'actual' data fetching (in real world, this calls a Cloud API/K8s)
        actual_data = {
            "DB_URL": "postgres://localhost:5432/db",
            "REDIS_TTL": 3600
        }

        try:
            result = self.analyst.compare_configs(template_file, actual_data, integrity_mode=integrity_mode)
            suggested_fix = result.get("suggested_fix", "No action required.")

            return {
                "success": True,
                "data": {
                    "env_1": env_1,
                    "env_2": env_2,
                    "drift_detected": result["drift_detected"],
                    "drift_keys": result["drift_keys"],
                    "explanation": result["explanation"],
                    "version_mismatch": False,
                    "suggested_fix": suggested_fix
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "CONFIG_COMPARE_ERROR", 
                    "message": str(e),
                    "explanation": f"The tool failed to compare the configurations: {str(e)}",
                    "suggested_fix": "Check if the baseline file path is correct and accessible by the server."
                }
            }
