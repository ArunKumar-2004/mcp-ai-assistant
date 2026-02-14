"""
Simple test to see LLMClient logging output.
"""
import logging
import os
import sys
from dotenv import load_dotenv

# Configure logging to see everything
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.llm_client import LLMClient

def test_llm_direct():
    print("=" * 60)
    print("DIRECT LLM CLIENT TEST")
    print("=" * 60)
    
    client = LLMClient()
    
    prompt = """As a DevOps specialist, analyze this health check result and return JSON:
    
Service: Wealth Hub
Status: UP
HTTP Code: 200
Latency: 732ms

Return JSON with 'explanation' and 'suggested_fix' fields."""
    
    print("\n📤 Sending prompt to Cohere...")
    try:
        result = client.generate_with_tools(prompt)
        print(f"\n📥 Received response:")
        print(f"Type: {type(result)}")
        print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        print(f"Content: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_llm_direct()
