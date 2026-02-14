from .tool_registry import ToolRegistry
from .context_manager import AgentContext
from tools.fetch_build_log import FetchBuildLogTool
from tools.analyze_log import AnalyzeBuildLogTool
from tools.fetch_config import FetchEnvironmentConfigTool
from tools.compare_config import CompareEnvironmentConfigsTool
from tools.check_health import CheckServiceHealthTool
from tools.check_db import CheckDatabaseConnectionTool
from tools.calculate_score import CalculateReadinessScoreTool
from services.drivers.notification_driver import WebhookDriver
import logging
import os
import json

class DeploymentAgent:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.registry = ToolRegistry()
        self.context = AgentContext()
        self.notifier = WebhookDriver()
        self._register_all_tools()
        self.logger = logging.getLogger("agent")

    def _register_all_tools(self):
        self.registry.register_tool("fetch_build_log", FetchBuildLogTool())
        self.registry.register_tool("analyze_build_log", AnalyzeBuildLogTool())
        self.registry.register_tool("fetch_environment_config", FetchEnvironmentConfigTool())
        self.registry.register_tool("compare_environment_configs", CompareEnvironmentConfigsTool())
        self.registry.register_tool("check_service_health", CheckServiceHealthTool())
        self.registry.register_tool("check_database_connection", CheckDatabaseConnectionTool())
        self.registry.register_tool("calculate_readiness_score", CalculateReadinessScoreTool())

    async def evaluate_build(self, project: str, build_id: str, environment: str) -> dict:
        self.context.clear()
        project_config = self.config.get("projects", {}).get(project, {})
        env_config = project_config.get("environments", {}).get(environment, {})
        
        if not env_config:
             return {"success": False, "error": {"code": "CONFIG_ERROR", "message": f"Project '{project}' or environment '{environment}' not found in schema."}}

        repo = project_config.get("repo", "unknown/repo")
        self.logger.info(f"Starting evaluation for {project} (repo: {repo}) build {build_id} in {environment}")

        try:
            # 1. Fetch Log (Pass repo to driver)
            log_res = await self._execute_tool_call("fetch_build_log", {"build_id": build_id, "repo": repo})
            if not log_res["success"]: return self._finalize_error("Failed to fetch log", log_res)
            log_text = log_res["data"]["log_text"]

            # 2. Analyze Log
            analysis_res = await self._execute_tool_call("analyze_build_log", {"log_text": log_text})
            if not analysis_res["success"]: return self._finalize_error("Failed to analyze log", analysis_res)
            
            # 3. Fetch Config
            config_res = await self._execute_tool_call("fetch_environment_config", {"environment": environment})
            
            # 4. Compare Config
            template_file = env_config.get("config_template")
            drift_res = await self._execute_tool_call("compare_environment_configs", {
                "env_1": environment, 
                "env_2": template_file
            })

            # 5. Check Service Health
            health_url = env_config.get("health_url")
            health_res = await self._execute_tool_call("check_service_health", {
                "service_name": f"{project.capitalize()} ({environment})", 
                "health_url": health_url
            })

            # 6. Check DB
            db_url = env_config.get("db_url", "none")
            db_res = await self._execute_tool_call("check_database_connection", {"environment": environment})

            # 7. Final Scoring
            score_res = await self._execute_tool_call("calculate_readiness_score", {
                "log_analysis": analysis_res["data"],
                "drift_analysis": drift_res["data"] if drift_res["success"] else {},
                "health_checks": [health_res["data"]] if health_res["success"] else [],
                "db_status": db_res["data"]["db_status"] if (db_res["success"] and db_url != "none") else "SAFE"
            })

            # 8. Enrich with Audit Report
            if score_res["success"]:
                score_res["data"]["audit_report"] = {
                    "build_analysis": analysis_res["data"],
                    "config_audit": drift_res.get("data", {}),
                    "health_status": health_res.get("data", {}),
                    "db_connectivity": db_res.get("data", {})
                }

                # 9. Human-in-the-loop Notification
                data = score_res["data"]
                self.notifier.send_deployment_alert(
                    score=data["readiness_score"],
                    status=data["status"],
                    summary=analysis_res["data"]["root_cause_summary"],
                    recommendations=data["penalties"]
                )

            return score_res

        except Exception as e:
            self.logger.exception("Agent execution failed")
            return {"success": False, "error": {"code": "AGENT_ERROR", "message": str(e)}}

    async def verify_build(self, project: str, build_id: str) -> dict:
        project_config = self.config.get("projects", {}).get(project, {})
        repo = project_config.get("repo", "unknown/repo")
        log_res = await self._execute_tool_call("fetch_build_log", {"build_id": build_id, "repo": repo})
        if not log_res["success"]: return log_res
        analysis_res = await self._execute_tool_call("analyze_build_log", {"log_text": log_res["data"]["log_text"]})
        return analysis_res

    async def verify_config(self, project: str, environment: str) -> dict:
        project_config = self.config.get("projects", {}).get(project, {})
        env_config = project_config.get("environments", {}).get(environment, {})
        if not env_config: return {"success": False, "error": {"message": "Env not found"}}
        template_file = env_config.get("config_template")
        drift_res = await self._execute_tool_call("compare_environment_configs", {
            "env_1": environment, 
            "env_2": template_file
        })
        return drift_res

    async def verify_health(self, project: str, environment: str) -> dict:
        project_config = self.config.get("projects", {}).get(project, {})
        env_config = project_config.get("environments", {}).get(environment, {})
        if not env_config: return {"success": False, "error": {"message": "Env not found"}}
        health_url = env_config.get("health_url")
        health_res = await self._execute_tool_call("check_service_health", {
            "service_name": f"{project.capitalize()} ({environment})", 
            "health_url": health_url
        })
        return health_res

    async def _execute_tool_call(self, tool_name: str, arguments: dict) -> dict:
        self.logger.info(f"Invoking tool: {tool_name}")
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return {"success": False, "error": {"code": "TOOL_NOT_FOUND", "message": f"Tool {tool_name} not found"}}
        
        result = await tool.execute(**arguments)
        self.context.add_tool_result(tool_name, result)
        return result

    def _finalize_error(self, message: str, tool_result: dict):
        return {
            "success": False, 
            "error": {
                "code": "EVALUATION_ABORTED", 
                "message": f"{message}: {tool_result.get('error', {}).get('message', 'Unknown error')}"
            }
        }
