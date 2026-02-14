from services.drivers.health_driver import DatabaseDriver

class CheckDatabaseConnectionTool:
    def __init__(self, driver: DatabaseDriver = None):
        self.driver = driver or DatabaseDriver()

    async def execute(self, environment: str) -> dict:
        try:
            ping_res = self.driver.check_connectivity()
            migration_res = self.driver.check_migrations()
            
            return {
                "success": True,
                "data": {
                    "environment": environment,
                    "db_status": ping_res["status"], # CONNECTED | FAILED
                    "response_time_ms": ping_res["latency_ms"],
                    "migrations_ok": migration_res["match"]
                }
            }
        except Exception as e:
            return {
                "success": True,
                "data": {
                    "environment": environment,
                    "db_status": "FAILED",
                    "response_time_ms": 0,
                    "error": str(e)
                }
            }
