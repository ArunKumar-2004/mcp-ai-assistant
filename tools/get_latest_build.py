from services.drivers.ci_driver import GitHubActionsDriver
from services.llm_client import LLMClient
from datetime import datetime
import os
import logging

logger = logging.getLogger("get_latest_build_tool")

class GetLatestBuildTool:
    """
    Automatically discovers and fetches the latest build log from GitHub Actions.
    No manual run_id required - intelligently finds the most recent workflow run.
    """
    def __init__(self, driver: GitHubActionsDriver = None, llm_client: LLMClient = None):
        self.driver = driver or GitHubActionsDriver()
        self.llm_client = llm_client or LLMClient()
        self.default_repo = os.getenv("GITHUB_REPOSITORY")

    async def execute(self, repo: str = None, workflow_name: str = None, 
                     branch: str = None, include_log: bool = True) -> dict:
        """
        Automatically fetch and analyze the latest GitHub Actions build.
        
        Args:
            repo: Repository (owner/repo format). Defaults to GITHUB_REPOSITORY env var.
            workflow_name: Optional workflow filter (e.g., "nextjs-build" or "Next.js Build")
            branch: Optional branch filter (e.g., "main")
            include_log: Whether to fetch and include full log text (default: True)
        
        Returns:
            Latest build status with AI-powered analysis
        """
        target_repo = repo or self.default_repo
        if not target_repo:
            error_narration = self._generate_error_narration("No repository specified.", None)
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
            # Discover the latest workflow run
            logger.info(f"Discovering latest workflow run for {target_repo}...")
            latest_run = self.driver.get_latest_run(
                repo=target_repo,
                workflow_name=workflow_name,
                branch=branch,
                status="completed"  # Only get completed runs
            )

            if not latest_run:
                error_narration = self._generate_error_narration(
                    "No workflow runs found.",
                    target_repo,
                    workflow_name,
                    branch
                )
                return {
                    "success": False,
                    "error": {
                        "code": "NO_RUNS_FOUND",
                        "message": "No workflow runs found matching the criteria.",
                        "explanation": error_narration.get("explanation", "No builds found."),
                        "suggested_fix": error_narration.get("suggested_fix", "Check repository and workflow name.")
                    }
                }

            run_id = latest_run["id"]
            logger.info(f"Found latest run: {run_id} - {latest_run['name']} ({latest_run['conclusion']})")

            # Fetch the log if requested
            log_text = None
            if include_log:
                try:
                    logger.info(f"Fetching logs for run {run_id}...")
                    log_text = self.driver.fetch_log(target_repo, str(run_id))
                except Exception as e:
                    logger.warning(f"Failed to fetch logs: {e}")
                    log_text = f"[Log fetch failed: {str(e)}]"

            # Generate AI analysis
            ai_analysis = self._generate_ai_analysis(latest_run, log_text)

            return {
                "success": True,
                "data": {
                    "run_id": run_id,
                    "workflow_name": latest_run["name"],
                    "status": latest_run["status"],
                    "conclusion": latest_run["conclusion"],
                    "created_at": latest_run["created_at"],
                    "updated_at": latest_run["updated_at"],
                    "branch": latest_run["head_branch"],
                    "commit": latest_run["head_commit"],
                    "html_url": latest_run["html_url"],
                    "log_text": log_text if include_log else "[Log not fetched - set include_log=True]",
                    "explanation": ai_analysis.get("explanation", f"Build {latest_run['conclusion']}."),
                    "root_cause": ai_analysis.get("root_cause", "N/A"),
                    "suggested_fix": ai_analysis.get("suggested_fix", "No action required.")
                }
            }

        except Exception as e:
            logger.error(f"Error in get_latest_build: {e}")
            error_narration = self._generate_error_narration(str(e), target_repo, workflow_name, branch)
            return {
                "success": False,
                "error": {
                    "code": "FETCH_ERROR",
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Failed to retrieve build information."),
                    "suggested_fix": error_narration.get("suggested_fix", "Verify GitHub credentials and repository access.")
                }
            }

    def _generate_ai_analysis(self, run_info: dict, log_text: str = None) -> dict:
        """
        Generate AI-powered analysis of the build result.
        """
        conclusion = run_info.get("conclusion", "unknown")
        workflow_name = run_info.get("name", "Unknown")
        commit_msg = run_info["head_commit"]["message"]
        
        # Build the prompt
        prompt = (
            f"As a DevOps Engineer, analyze this GitHub Actions build result.\\n\\n"
            f"Workflow: {workflow_name}\\n"
            f"Status: {run_info['status']}\\n"
            f"Conclusion: {conclusion}\\n"
            f"Branch: {run_info['head_branch']}\\n"
            f"Commit: {commit_msg}\\n"
        )

        if log_text and conclusion == "failure":
            # Truncate log if too long (keep last 5000 chars which usually has the error)
            log_snippet = log_text[-5000:] if len(log_text) > 5000 else log_text
            prompt += f"\\nBuild Log (last 5000 chars):\\n{log_snippet}\\n"

        prompt += (
            "\\nReturn JSON with:\\n"
            "- 'explanation': Professional summary of the build result\\n"
            "- 'root_cause': If failed, identify the root cause from logs\\n"
            "- 'suggested_fix': Actionable steps to resolve the issue\\n"
        )

        try:
            logger.info("Generating AI analysis of build result...")
            return self.llm_client.generate_with_tools(prompt)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback response
            if conclusion == "success":
                return {
                    "explanation": f"Build completed successfully for {workflow_name}.",
                    "root_cause": "N/A",
                    "suggested_fix": "No action required."
                }
            else:
                return {
                    "explanation": f"Build {conclusion} for {workflow_name}. Check logs for details.",
                    "root_cause": "Unable to analyze - AI narration failed.",
                    "suggested_fix": "Review build logs manually."
                }

    def _generate_error_narration(self, error_msg: str, repo: str = None, 
                                  workflow_name: str = None, branch: str = None) -> dict:
        """
        Generate AI-powered error explanation.
        """
        prompt = (
            f"The GitHub Actions build fetcher encountered an error.\\n"
            f"Error: {error_msg}\\n"
            f"Repository: {repo or 'Not specified'}\\n"
            f"Workflow: {workflow_name or 'Any'}\\n"
            f"Branch: {branch or 'Any'}\\n\\n"
            "Explain why this happened and how to fix it. Return JSON with 'explanation' and 'suggested_fix'."
        )
        
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {
                "explanation": f"Error: {error_msg}",
                "suggested_fix": "Verify GitHub configuration and credentials."
            }
