"""
Direct test of AI-powered tools to verify Cohere integration.
This bypasses the MCP server to test the tools directly.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from tools.check_health import CheckServiceHealthTool
from tools.compare_config import CompareEnvironmentConfigsTool

async def test_ai_tools():
    print("=" * 60)
    print("TESTING AI-POWERED DIAGNOSTIC TOOLS")
    print("=" * 60)
    
    # Check if API key is loaded
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        print("❌ COHERE_API_KEY not found in environment!")
        return
    print(f"✅ COHERE_API_KEY loaded (length: {len(api_key)})\n")
    
    # Test 1: Health Check
    print("\n" + "=" * 60)
    print("TEST 1: Health Check Tool")
    print("=" * 60)
    health_tool = CheckServiceHealthTool()
    result = await health_tool.execute(
        service_name="Wealth Hub",
        health_url="https://www.wealth-hub.info/"
    )
    
    print(f"\nSuccess: {result['success']}")
    if result['success']:
        data = result['data']
        print(f"Status: {data['status']}")
        print(f"Latency: {data['latency_ms']}ms")
        print(f"HTTP Code: {data['http_code']}")
        print(f"\n🤖 AI EXPLANATION:")
        print(f"{data.get('explanation', 'N/A')}")
        print(f"\n💡 AI SUGGESTED FIX:")
        print(f"{data.get('suggested_fix', 'N/A')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 2: Config Drift
    print("\n" + "=" * 60)
    print("TEST 2: Config Drift Tool")
    print("=" * 60)
    config_tool = CompareEnvironmentConfigsTool()
    result = await config_tool.execute(
        env_1="production",
        env_2="tests/fixtures/template.env",
        integrity_mode=False
    )
    
    print(f"\nSuccess: {result['success']}")
    if result['success']:
        data = result['data']
        print(f"Drift Detected: {data['drift_detected']}")
        print(f"Drift Keys: {data.get('drift_keys', [])}")
        print(f"\n🤖 AI EXPLANATION:")
        print(f"{data.get('explanation', 'N/A')}")
        print(f"\n💡 AI SUGGESTED FIX:")
        print(f"{data.get('suggested_fix', 'N/A')}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ai_tools())
