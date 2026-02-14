import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    Generic LLM Client. Following the contract for GeminiClient but using Cohere 
    as per existing working setup.
    """
    def __init__(self):
        self.api_url = "https://api.cohere.ai/v1/chat"
        self.api_key = os.environ.get("COHERE_API_KEY")

    def generate_with_tools(self, prompt: str, tools: list = None) -> dict:
        """
        Gemini-style method signature as per contract.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "message": prompt,
            "model": "command-r-08-2024",
            "temperature": 0.2,
        }
        
        response = requests.post(self.api_url, headers=headers, json=data)
        if not response.ok:
            raise RuntimeError(f"LLM request failed: {response.text}")

        text = response.json().get("text", "").strip()
        
        # Attempt to parse JSON if possible, otherwise return as summary
        try:
            # Look for JSON block in markdown if LLM includes it
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}

    def _handle_rate_limit(self):
        pass

    def _retry_request(self):
        pass
