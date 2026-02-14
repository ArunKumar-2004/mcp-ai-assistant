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
    def compare_configs(self, template_path: str, actual_data: Dict[str, Any], integrity_mode: bool = False) -> dict:
        """
        Compares a template file with live data.
        If integrity_mode is True, it focuses on whether values are filled and valid
        (useful for single-environment projects).
        """
        if not os.path.exists(template_path):
            logger.warning(f"Template file {template_path} not found.")
            return {"drift_detected": False, "drift_keys": []}

        # Load template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            ext = os.path.splitext(template_path)[1].lower()
            
            if ext in ['.yaml', '.yml']:
                template = yaml.safe_load(content)
            elif ext == '.json':
                template = json.loads(content)
            elif '.env' in template_path or template_path.endswith('.local'):
                template = self._parse_dotenv(content)
            elif ext == '.properties':
                template = self._parse_properties(content)
            elif template_path.endswith('pom.xml'):
                template = self._parse_pom_xml(content)
            elif 'Dockerfile' in template_path:
                template = self._parse_dockerfile(content)
            else:
                try:
                    template = json.loads(content)
                except:
                    template = self._parse_dotenv(content)

        if not isinstance(template, dict):
             logger.warning(f"Template at {template_path} did not parse to a dictionary.")
             return {"drift_detected": False, "drift_keys": []}

        drift = self._find_missing_keys(template, actual_data)
        value_issues = []
        
        # In Integrity Mode, we also check if the existing values are empty/dummy
        if integrity_mode:
            value_issues = self._find_value_issues(actual_data)
            drift.extend(value_issues)

        return {
            "drift_detected": len(drift) > 0,
            "drift_keys": list(set(drift)),
            "version_mismatch": False,
            "analysis_type": "INTEGRITY" if integrity_mode else "DRIFT"
        }

    def _find_value_issues(self, data: dict, prefix: str = "") -> List[str]:
        """Detects empty or 'placeholder' values (e.g., 'your_key_here')."""
        issues = []
        placeholders = ["YOUR_KEY_HERE", "TODO", "NONE", "NULL", "CHANGE_ME", "EXAMPLE"]
        for key, value in data.items():
            full_key = f"{prefix}{key}"
            if value is None or (isinstance(value, str) and (not value.strip() or any(p in value.upper() for p in placeholders))):
                issues.append(f"{full_key} (EMPTY_OR_PLACEHOLDER)")
            elif isinstance(value, dict):
                issues.extend(self._find_value_issues(value, f"{full_key}."))
        return issues

    def _parse_dotenv(self, content: str) -> dict:
        """Parses KEY=VALUE pairs from a string."""
        results = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                results[key.strip()] = value.strip().strip('"').strip("'")
        return results

    def _parse_properties(self, content: str) -> dict:
        """Parses Java-style .properties files."""
        return self._parse_dotenv(content) # Very similar syntax

    def _parse_pom_xml(self, content: str) -> dict:
        """Flattened basic properties and dependencies from Maven pom.xml."""
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(content)
            ns = {'ns': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
            
            results = {}
            # Extract basic metadata
            for child in root:
                tag = child.tag.split('}')[-1]
                if tag in ['groupId', 'artifactId', 'version']:
                    results[tag] = child.text
            
            # Extract properties
            props = root.find('.//ns:properties', ns) if ns else root.find('.//properties')
            if props is not None:
                for p in props:
                    results[f"prop.{p.tag.split('}')[-1]}"] = p.text
            return results
        except:
            return {}

    def _parse_dockerfile(self, content: str) -> dict:
        """Extracts ENV instructions from Dockerfile."""
        results = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('ENV'):
                parts = line[3:].strip().split(' ', 1)
                if len(parts) == 2:
                    key, val = parts
                elif '=' in line:
                    key, val = line[3:].strip().split('=', 1)
                else:
                    continue
                results[key.strip()] = val.strip()
        return results

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
