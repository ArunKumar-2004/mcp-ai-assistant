"""
Test Cohere API directly to verify the API key and connection.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_cohere_api():
    api_key = os.environ.get("COHERE_API_KEY")
    
    if not api_key:
        print("❌ COHERE_API_KEY not found!")
        return
    
    print(f"✅ API Key loaded (length: {len(api_key)})")
    print(f"First 10 chars: {api_key[:10]}...")
    
    # Test the API
    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "message": "Say 'Hello' in JSON format with a 'greeting' field.",
        "model": "command-r-08-2024",
        "temperature": 0.2
    }
    
    print("\n🔄 Testing Cohere API...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.ok:
            print("✅ API call successful!")
            result = response.json()
            print(f"Response: {result.get('text', 'N/A')[:200]}")
        else:
            print(f"❌ API call failed!")
            print(f"Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_cohere_api()
