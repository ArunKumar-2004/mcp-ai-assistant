from services.drivers.health_driver import DatabaseDriver
from services.llm_client import LLMClient
import logging

logger = logging.getLogger("db_tool")

class CheckDatabaseConnectionTool:
    def __init__(self, driver: DatabaseDriver = None, llm_client: LLMClient = None):
        self.driver = driver or DatabaseDriver()
        self.llm_client = llm_client or LLMClient()

    async def execute(self, environment: str) -> dict:
        try:
            # Deterministic Fact Gathering
            ping_res = self.driver.check_connectivity()
            migration_res = self.driver.check_migrations()
            
            facts = {
                "environment": environment,
                "db_status": ping_res["status"], # CONNECTED | FAILED
                "response_time_ms": ping_res["latency_ms"],
                "migrations_ok": migration_res["match"]
            }

            # AI Narrative Generation
            ai_narration = self._generate_ai_analysis(facts)

            return {
                "success": True,
                "data": {
                    **facts,
                    "explanation": ai_narration.get("explanation", f"Database {facts['db_status']}."),
                    "suggested_fix": ai_narration.get("suggested_fix", "No action required.")
                }
            }
        except Exception as e:
            # Even failures get AI-narrated responses
            error_narration = self._generate_error_narration(str(e), environment)
            return {
                "success": False,
                "error": {
                    "code": "DB_CHECK_ERROR", 
                    "message": str(e),
                    "explanation": error_narration.get("explanation", "Database check failed."),
                    "suggested_fix": error_narration.get("suggested_fix", "Check connection string.")
                }
            }

    def _generate_ai_analysis(self, facts: dict) -> dict:
        """Synthesizes technical facts into a project-aware narrative."""
        prompt = (
            f"As a Database Administrator, analyze this connectivity result for the '{facts['environment']}' environment.\n"
            f"Connection Status: {facts['db_status']}\n"
            f"Latency: {facts['response_time_ms']}ms\n"
            f"Migrations Match: {facts['migrations_ok']}\n\n"
            "Return JSON with 'explanation' and 'suggested_fix'. The 'explanation' should "
            "be a professional summary of the database health. The 'suggested_fix' should "
            "provide steps to optimize the connection or resolve migration mismatches."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except Exception as e:
            logger.error(f"AI Narration failed: {e}")
            return {"explanation": "Database audit completed.", "suggested_fix": "No action required."}

    def _generate_error_narration(self, error_msg: str, env: str) -> dict:
        """Narrates a tool failure using AI to provide helpful context."""
        prompt = (
            f"The database auditor encountered an error checking the '{env}' environment.\n"
            f"Error Message: {error_msg}\n"
            "Explain in professional terms why this check failed and how to resolve it. Return JSON with 'explanation' and 'suggested_fix'."
        )
        try:
            return self.llm_client.generate_with_tools(prompt)
        except:
            return {"explanation": f"System error: {error_msg}", "suggested_fix": "Verify the database URL."}
