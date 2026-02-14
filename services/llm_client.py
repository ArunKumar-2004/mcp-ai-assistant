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
        
        # Attempt to parse JSON if possible
        json_str = text
        try:
            # 1. Look for JSON block in markdown
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                 json_str = text.split("```")[1].split("```")[0].strip()
            
            # 2. Heuristic: Find first '{' and last '}' if not already parsed
            if "{" in json_str and "}" in json_str:
                start = json_str.find("{")
                end = json_str.rfind("}") + 1
                json_str = json_str[start:end]

            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            return {"raw_text": text}

    def _handle_rate_limit(self):
        pass

    def _retry_request(self):
        pass
