from services.drivers.ci_driver import GitHubActionsDriver
from services.llm_client import LLMClient
from datetime import datetime
import os
import logging

logger = logging.getLogger("fetch_log_tool")

class FetchBuildLogTool:
    def __init__(self, driver: GitHubActionsDriver = None, llm_client: LLMClient = None):
        self.driver = driver or GitHubActionsDriver()
        self.llm_client = llm_client or LLMClient()
        self.default_repo = os.getenv("GITHUB_REPOSITORY") 

    async def execute(self, build_id: str, repo: str = None) -> dict:
        target_repo = repo or self.default_repo
        if not target_repo:
            error_narration = self._generate_error_narration("No repository specified.", build_id)
            return {
                "success": False,
                "error": {
                    "code": "CONFIG_ERROR", 
                    "message": "No repository specified.",
                    "explanation": error_narration.get("explanation", "Target repository is undefined."),
                    "suggested_fix": error_narration.get("suggested_fix", "Set GITHUB_REPOSITORY environment variable.")
                }
            }

        try:
            log_text = self.driver.fetch_log(target_repo, build_id)
            
            # AI Narration of the fetch event
            ai_narration = self._generate_ai_status(target_repo, build_id, True)

            return {
                "success": True,
                "data": {
                    "build_id": build_id,
                    "repo": target_repo,
                    "log_text": log_text,
                    "timestamp": datetime.now().isoformat(),
                    "explanation": ai_narration.get("explanation", "Log retrieved successfully.")
                }
            }
        except Exception as e:
            error_narration = self._generate_error_narration(str(e), build_id, target_repo)
            return {
                "success": False,
                "error": {
                    "code": "FETCH_LOG_ERROR",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Failed to retrieve logs."),
                    "suggested_fix": error_narration.get("suggested_fix", "Verify build ID and permissions.")
                }
            }

    def _generate_ai_status(self, repo: str, build_id: str, success: bool) -> dict:
        """Briefly narrates the status of the log retrieval."""
        prompt = (
            f"As a DevOps Assistant, provide a brief, professional confirmation of log retrieval.\n"
            f"Repo: {repo}\n"
            f"Build ID: {build_id}\n"
            f"Status: SUCCESS\n\n"
            "Return a JSON object with 'explanation'. The tone should be helpful and 'respective'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"Successfully retrieved logs for build {build_id}."}

    def _generate_error_narration(self, error_msg: str, build_id: str, repo: str = "Unknown") -> dict:
        """Narrates a log fetch failure using AI."""
        prompt = (
            f"The DevOps log fetcher encountered a failure.\n"
            f"Error: {error_msg}\n"
            f"Repo: {repo}\n"
            f"Build ID: {build_id}\n\n"
            "Explain in professional terms why this happened. Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"System error fetching log: {error_msg}", "suggested_fix": "Verify GitHub credentials."}
