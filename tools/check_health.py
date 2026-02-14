from services.drivers.health_driver import DeepHealthDriver
import asyncio
import time

class CheckServiceHealthTool:
    def __init__(self, driver: DeepHealthDriver = None):
        self.driver = driver or DeepHealthDriver()

    async def execute(self, service_name: str, health_url: str) -> dict:
        result = await self.driver.check_service(health_url)
        
        suggested_fix = None
        if result["status"] != "PASS":
            suggested_fix = f"Check logs for {service_name} at {health_url}. Possible service crash or dependency failure."

        return {
            "success": True, 
            "data": {
                "service_name": service_name,
                "status": result["status"],
                "latency_ms": result["latency_ms"],
                "suggested_fix": suggested_fix,
                "details": result
            }
        }
