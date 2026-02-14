from services.drivers.ci_driver import GitHubActionsDriver
from datetime import datetime
import os

class FetchBuildLogTool:
    def __init__(self, driver: GitHubActionsDriver = None):
        # We allow passing a repo name or using default from env
        self.driver = driver or GitHubActionsDriver()
        self.default_repo = os.getenv("GITHUB_REPOSITORY") 

    async def execute(self, build_id: str, repo: str = None) -> dict:
        """
        build_id here refers to the GitHub Actions Run ID.
        """
        target_repo = repo or self.default_repo
        if not target_repo:
             return {
                "success": False,
                "error": {"code": "CONFIG_ERROR", "message": "No repository specified and GITHUB_REPOSITORY env not set."}
            }

        try:
            log_text = self.driver.fetch_log(target_repo, build_id)
            return {
                "success": True,
                "data": {
                    "build_id": build_id,
                    "repo": target_repo,
                    "log_text": log_text,
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return self._handle_error(e)

    def _handle_error(self, e):
        return {
            "success": False,
            "error": {
                "code": "FETCH_LOG_ERROR",
                "message": str(e)
            }
        }
