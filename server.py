from mcp.server.fastmcp import FastMCP
from agent.agent_controller import DeploymentAgent
from services.config_loader import ConfigLoader, ConfigError
import logging
import sys
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

def run_server():
    # 1. Handle Initialization CLI Command
    if "--init-config" in sys.argv:
        ConfigLoader.generate_default_config()
        sys.exit(0)

    # 2. Production Config Loading (Fail-Fast)
    try:
        config = ConfigLoader().load()
    except ConfigError as e:
        logger.error(f"❌ STARTUP FAILED: {e}")
        sys.exit(1)

    # 3. Initialize Agent and Server
    mcp = FastMCP(config.get("project_name", "AI Deployment Readiness Assistant"))
    agent = DeploymentAgent(config=config)

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
