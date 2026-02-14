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
