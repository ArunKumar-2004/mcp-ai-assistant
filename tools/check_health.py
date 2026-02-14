from services.drivers.health_driver import DeepHealthDriver
import asyncio
import time

class CheckServiceHealthTool:
    def __init__(self, driver: DeepHealthDriver = None):
        self.driver = driver or DeepHealthDriver()

    async def execute(self, service_name: str, health_url: str) -> dict:
        try:
            result = await self.driver.check_service(health_url)
            
            suggested_fix = None
            if result["status"] != "UP": # Match UP/DOWN status from driver
                suggested_fix = result.get("suggested_fix") or f"Check logs for {service_name} at {health_url}. Possible service crash or dependency failure."

            return {
                "success": True, 
                "data": {
                    "service_name": service_name,
                    "status": result["status"],
                    "latency_ms": result["latency_ms"],
                    "explanation": result["explanation"],
                    "suggested_fix": suggested_fix,
                    "details": result
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "HEALTH_CHECK_ERROR", 
                    "message": str(e),
                    "explanation": f"The health check tool encountered a system error: {str(e)}",
                    "suggested_fix": "Verify the health_url configuration and network connectivity."
                }
            }
