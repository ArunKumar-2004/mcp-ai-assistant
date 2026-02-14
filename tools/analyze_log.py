from services.llm_client import LLMClient
from models import LogCategory, Severity
import json

class AnalyzeBuildLogTool:
    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client or LLMClient()

    async def execute(self, log_text: str) -> dict:
        prompt = (
            "Analyze the following build log and determine the root cause. "
            "Return JSON only with keys: category (INFRA|CODE|CONFIG|DEPENDENCY|FLAKY), "
            "severity (LOW|MEDIUM|HIGH), confidence (float 0-1), root_cause_summary (string), suggested_fix (string).\n\n"
            f"Log:\n{log_text}"
        )
        
        try:
            analysis = self.llm_client.generate_with_tools(prompt)
            validated = self._validate_llm_response(analysis)
            return {
                "success": True,
                "data": validated
            }
        except Exception as e:
            # Fallback to rule-based if LLM fails or returns garbage
            return {
                "success": True,
                "data": self._fallback_rule_classifier(log_text)
            }

    def _validate_llm_response(self, response: dict) -> dict:
        # Ensure fields exist and are in correct format
        if not isinstance(response, dict):
             raise ValueError("LLM response is not a dict")
             
        return {
            "category": response.get("category", LogCategory.INFRA).upper(),
            "severity": response.get("severity", Severity.MEDIUM).upper(),
            "confidence": float(response.get("confidence", 0.5)),
            "root_cause_summary": response.get("root_cause_summary", "Unknown"),
            "suggested_fix": response.get("suggested_fix", "Manual review required")
        }

    def _fallback_rule_classifier(self, log_text: str) -> dict:
        severity = Severity.MEDIUM
        category = LogCategory.CODE
        
        if "DB" in log_text.upper() or "DATABASE" in log_text.upper():
            category = LogCategory.INFRA
            severity = Severity.HIGH
        elif "DRIFT" in log_text.upper():
            category = LogCategory.CONFIG
            
        return {
            "category": category,
            "severity": severity,
            "confidence": 0.4,
            "root_cause_summary": "Rule-based analysis (Fallback)",
            "suggested_fix": "Check logs manually for specific error."
        }
