#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
from agent.agent_controller import DeploymentAgent
from services.config_loader import ConfigLoader, ConfigError
from models import ToolResponse, ServerHealth, DiscoveryResult
import logging
import sys
import os
from dotenv import load_dotenv

# Configure Logging early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Load environment variables early - look in script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path=env_path, override=False)  # Don't override existing env vars
logger.info(f"Loading .env from: {env_path} (exists: {os.path.exists(env_path)})")

def run_server():
    # 1. Handle Initialization CLI Command
    if "--init-config" in sys.argv:
        ConfigLoader.generate_default_config()
        sys.exit(0)

    # 2. Production Config Loading (Graceful)
    # We load with fail_fast=False to allow the server to start even if files are missing.
    loader = ConfigLoader()
    config = loader.load(fail_fast=False)

    # 3. Initialize Agent and Server
    mcp = FastMCP("Readiness Assistant")
    agent = DeploymentAgent(config=config)

    @mcp.tool()
    async def initialize_config() -> DiscoveryResult:
        """
        Creates/updates readiness_schema.json by scanning the workspace for projects.
        Use this if the server reports that configuration is missing or to register new projects.
        """
        discovered = ConfigLoader.discover_workspace_projects()
        
        ConfigLoader.generate_default_config(discovered_projects=discovered)
        # Reload agent with new config
        new_config = loader.load(fail_fast=True)
        agent.config = new_config
        
        return DiscoveryResult(
            success=True,
            message="Workspace scanned and readiness_schema.json registered.",
            discovered_projects=list(discovered.keys())
        )

    @mcp.tool()
    async def server_health() -> ServerHealth:
        """
        Returns the health status and telemetry of the Readiness Assistant server.
        """
        try:
            return ServerHealth(
                status="UP",
                tools_registered=10, # Static count of registered tools
                environment=os.getenv("APP_ENV", "production"),
                config_loaded=loader.exists()
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    @mcp.tool()
    async def evaluate_build(project: str, build_id: str, environment: str) -> dict:
        """
        Orchestrates the full deployment readiness assessment for a specific project, build, and environment.
        Calls CI logs, AI analysis, config drift detection, and health checks.
        """
        logger.info(f"MCP Tool call: evaluate_build({project}, {build_id}, {environment})")
        result = await agent.evaluate_build(project, build_id, environment)
        return result

    # Register individual tools as well if direct access is desired
    @mcp.tool()
    async def fetch_build_log(build_id: str, repo: str = None) -> dict:
        """Fetch build logs from the CI system."""
        return await agent._execute_tool_call("fetch_build_log", {"build_id": build_id, "repo": repo})

    @mcp.tool()
    async def get_latest_build(repo: str = None, workflow_name: str = None, 
                              branch: str = None, include_log: bool = True) -> dict:
        """
        Automatically fetch and analyze the latest GitHub Actions build.
        No manual run_id required - intelligently discovers the most recent workflow run.
        
        Args:
            repo: Repository (owner/repo format). Defaults to GITHUB_REPOSITORY env var.
            workflow_name: Optional workflow filter (e.g., "nextjs-build" or "Next.js Build")
            branch: Optional branch filter (e.g., "main")
            include_log: Whether to fetch full log text (default: True)
        
        Returns:
            Latest build status with AI-powered analysis of failures.
        """
        return await agent._execute_tool_call("get_latest_build", {
            "repo": repo,
            "workflow_name": workflow_name,
            "branch": branch,
            "include_log": include_log
        })

    @mcp.tool()
    async def analyze_build_log(log_text: str) -> dict:
        """Use AI to classify the build log and determine the root cause of failures."""
        return await agent._execute_tool_call("analyze_build_log", {"log_text": log_text})

    @mcp.tool()
    async def analyze_log_with_llm(log: str) -> dict:
        """Alias for analyze_build_log to support existing tests."""
        return await analyze_build_log(log)

    @mcp.tool()
    async def check_service_health(service_name: str, health_url: str) -> dict:
        """Check the health status and latency of a specific service."""
        return await agent._execute_tool_call("check_service_health", {"service_name": service_name, "health_url": health_url})

    @mcp.tool()
    async def verify_build(project: str, build_id: str) -> dict:
        """Just verify the build logs and root cause using AI."""
        return await agent.verify_build(project, build_id)

    @mcp.tool()
    async def verify_config(project: str, environment: str) -> dict:
        """Just verify configuration drift for a project and environment."""
        return await agent.verify_config(project, environment)

    @mcp.tool()
    async def verify_health(project: str, environment: str) -> dict:
        """Just verify health and connectivity for a project and environment."""
        return await agent.verify_health(project, environment)

    @mcp.tool()
    async def calculate_readiness_score(log_analysis: dict, drift_analysis: dict, health_checks: list, db_status: str) -> dict:
        """Calculate the final readiness score based on all analysis results."""
        return await agent._execute_tool_call("calculate_readiness_score", {
            "log_analysis": log_analysis,
            "drift_analysis": drift_analysis,
            "health_checks": health_checks,
            "db_status": db_status
        })

    mcp.run()

if __name__ == "__main__":
    run_server()
