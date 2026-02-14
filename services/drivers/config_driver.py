import os
import json
import yaml
import logging
from typing import Dict, Any, List

logger = logging.getLogger("config_driver")

class DriftAnalyst:
    """
    Analyzes drift between configuration templates and actual environment files.
    """
    def compare_configs(self, template_path: str, actual_data: Dict[str, Any]) -> dict:
        """
        Compares a template file (structural source of truth) with live data.
        """
        if not os.path.exists(template_path):
            logger.warning(f"Template file {template_path} not found.")
            return {"drift_detected": False, "drift_keys": []}

        # Load template
        with open(template_path, 'r') as f:
            if template_path.endswith(('.yaml', '.yml')):
                template = yaml.safe_load(f)
            else:
                template = json.load(f)

        drift = self._find_missing_keys(template, actual_data)
        
        return {
            "drift_detected": len(drift) > 0,
            "drift_keys": drift,
            "version_mismatch": False # Would need version metadata from actual_data
        }

    def _find_missing_keys(self, template: dict, actual: dict, prefix: str = "") -> List[str]:
        missing = []
        for key, value in template.items():
            full_key = f"{prefix}{key}"
            if key not in actual:
                missing.append(full_key)
            elif isinstance(value, dict) and isinstance(actual.get(key), dict):
                missing.extend(self._find_missing_keys(value, actual[key], f"{full_key}."))
        return missing

class ValidationAnalyst:
    """
    Validates configuration data against specific semantic rules.
    """
    def validate(self, data: dict, rules: dict) -> dict:
        errors = []
        # Example: check if keys match specific patterns or ranges
        for key, rule in rules.items():
            val = data.get(key)
            if not val:
                errors.append(f"Missing mandatory key: {key}")
            # Add semantic logic here (regex, type checks, etc.)
        
        return {"valid": len(errors) == 0, "errors": errors}
