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
        
        # Debug logging
        import logging
        logger = logging.getLogger("llm_client")
        if not self.api_key:
            logger.error("COHERE_API_KEY is not set in environment!")
        else:
            logger.info(f"LLMClient initialized with API key (length: {len(self.api_key)})")

    def generate_with_tools(self, prompt: str, tools: list = None) -> dict:
        """
        Gemini-style method signature as per contract.
        """
        import logging
        logger = logging.getLogger("llm_client")
        
        if not self.api_key:
            logger.error("Cannot make LLM request: API key is missing")
            raise RuntimeError("COHERE_API_KEY not configured")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "message": prompt,
            "model": "command-r-08-2024",
            "temperature": 0.2,
        }
        
        import time
        
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Calling Cohere API (attempt {attempt + 1}/{max_retries + 1})...")
                response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
                
                if not response.ok:
                    logger.error(f"Cohere API error: {response.status_code} - {response.text}")
                    raise RuntimeError(f"LLM request failed: HTTP {response.status_code} - {response.text[:200]}")

                # Log the raw response for debugging
                raw_response = response.json()
                logger.info(f"Cohere API raw response keys: {list(raw_response.keys())}")
                
                text = raw_response.get("text", "").strip()
                logger.info(f"Extracted text (first 200 chars): {text[:200]}")
                
                # Attempt to parse JSON if possible
                json_str = text
                try:
                    # 1. Look for JSON block in markdown
                    if "```json" in text:
                        json_str = text.split("```json")[1].split("```")[0].strip()
                        logger.info("Found JSON in markdown block")
                    elif "```" in text:
                         json_str = text.split("```")[1].split("```")[0].strip()
                         logger.info("Found content in generic markdown block")
                    
                    # 2. Heuristic: Find first '{' and last '}' if not already parsed
                    if "{" in json_str and "}" in json_str:
                        start = json_str.find("{")
                        end = json_str.rfind("}") + 1
                        json_str = json_str[start:end]
                        logger.info(f"Extracted JSON string (first 100 chars): {json_str[:100]}")

                    parsed = json.loads(json_str)
                    logger.info(f"✅ Successfully parsed JSON with keys: {list(parsed.keys())}")
                    return parsed
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"JSON parsing failed: {e}. Returning raw text.")
                    return {"raw_text": text}
                    
            except requests.exceptions.Timeout as e:
                if attempt < max_retries:
                    logger.warning(f"Timeout on attempt {attempt + 1}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"All {max_retries + 1} attempts timed out")
                    raise RuntimeError(f"Cohere API timeout after {max_retries + 1} attempts")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error calling Cohere API: {e}")
                raise RuntimeError(f"Failed to connect to Cohere API: {str(e)}")

    def _handle_rate_limit(self):
        pass

    def _retry_request(self):
        pass
