import os
import requests
import zipfile
import io
import logging

logger = logging.getLogger("ci_driver")

class GitHubActionsDriver:
    """
    Driver for fetching build logs from GitHub Actions.
    Requires GITHUB_TOKEN in environment.
    """
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = os.getenv("GITHUB_API_URL", "https://api.github.com")

    def fetch_log(self, repo: str, run_id: str) -> str:
        """
        Fetches the log for a specific workflow run.
        Note: GitHub returns logs as a zip file containing multiple job logs.
        """
        if not self.token:
            logger.warning("GITHUB_TOKEN not found, returning mock log.")
            return "ERROR: GITHUB_TOKEN missing. This is a mock log.\nINFO: Build failed at step 'tests'"

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Download logs zip
        url = f"{self.base_url}/repos/{repo}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch GitHub logs: {response.status_code} {response.text}")

        # Debug: check if it's actually a zip
        if not response.content.startswith(b'PK'):
            logger.error(f"Response is not a zip! Content starts with: {response.content[:100]}")
            raise RuntimeError("File is not a zip file")

        # Unzip in memory and extract logs
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Join all log files into one text block for the LLM
            log_contents = []
            for filename in z.namelist():
                if filename.endswith(".txt") or ".log" in filename:
                    with z.open(filename) as f:
                        log_contents.append(f"--- File: {filename} ---\n{f.read().decode('utf-8')}")
            
            return "\n\n".join(log_contents) if log_contents else "No log files found in bundle."

    def list_workflow_runs(self, repo: str, workflow_name: str = None, 
                           status: str = None, branch: str = None, limit: int = 10) -> list:
        """
        List recent workflow runs for a repository.
        
        Args:
            repo: Repository in format "owner/repo"
            workflow_name: Optional workflow file name (e.g., "nextjs-build.yml")
            status: Optional filter (completed, in_progress, queued, failure, success)
            branch: Optional branch filter
            limit: Maximum number of runs to return (max 100)
        
        Returns:
            List of workflow runs with id, name, status, conclusion, created_at
        """
        if not self.token:
            logger.warning("GITHUB_TOKEN not found, returning empty list.")
            return []

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # Build query parameters
        params = {"per_page": min(limit, 100)}
        if status:
            params["status"] = status
        if branch:
            params["branch"] = branch
        
        # If workflow_name is provided, we need to get workflow_id first
        url = f"{self.base_url}/repos/{repo}/actions/runs"
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"Failed to list workflow runs: {response.status_code} {response.text}")
            raise RuntimeError(f"Failed to list workflow runs: {response.status_code}")
        
        data = response.json()
        runs = data.get("workflow_runs", [])
        
        # Filter by workflow name if specified
        if workflow_name:
            runs = [r for r in runs if workflow_name.lower() in r.get("name", "").lower() or 
                    workflow_name in r.get("path", "")]
        
        # Format the response
        return [{
            "id": run["id"],
            "name": run.get("name", "Unknown"),
            "status": run.get("status", "unknown"),
            "conclusion": run.get("conclusion"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "head_branch": run.get("head_branch"),
            "head_commit": {
                "message": run.get("head_commit", {}).get("message", ""),
                "author": run.get("head_commit", {}).get("author", {}).get("name", "")
            },
            "html_url": run.get("html_url")
        } for run in runs[:limit]]

    def get_latest_run(self, repo: str, workflow_name: str = None, 
                       branch: str = None, status: str = "completed") -> dict:
        """
        Get the most recent workflow run.
        
        Args:
            repo: Repository in format "owner/repo"
            workflow_name: Optional workflow filter
            branch: Optional branch filter (default: None, gets all branches)
            status: Filter by status (default: "completed")
        
        Returns:
            Single workflow run dict or None if no runs found
        """
        runs = self.list_workflow_runs(
            repo=repo,
            workflow_name=workflow_name,
            status=status,
            branch=branch,
            limit=1
        )
        
        return runs[0] if runs else None

class JenkinsDriver:
    """
    Driver for fetching build logs from Jenkins.
    """
    def fetch_log(self, build_url: str) -> str:
        # Appending /consoleText is the standard way to get raw logs from Jenkins
        url = f"{build_url.rstrip('/')}/consoleText"
        response = requests.get(url)
        if response.status_code != 200:
             raise RuntimeError(f"Failed to fetch Jenkins logs: {response.status_code}")
        return response.text
