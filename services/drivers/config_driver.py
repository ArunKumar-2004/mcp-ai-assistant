import os
import json
import yaml
import logging
from typing import Dict, Any, List

logger = logging.getLogger("config_driver")

class DriftAnalyst:
    """
    Analyzes drift between configuration templates and actual environment files.
    Purely deterministic: gathers technical facts (missing keys, value issues).
    """
    def compare_configs(self, template_path: str, actual_data: Dict[str, Any], integrity_mode: bool = False) -> dict:
        issues = []
        analysis_type = "INTEGRITY" if integrity_mode else "DRIFT"
        
        # 1. Fuzzy Resolution
        resolved_path = self._resolve_fuzzy_path(template_path)
        if not os.path.exists(resolved_path):
             # We treat file missing as a high-priority drift issue for the AI to narrate
             return {
                "drift_detected": True,
                "drift_keys": ["BASELINE_FILE_MISSING"],
                "resolved_path": resolved_path,
                "analysis_type": analysis_type
             }

        # 2. Load and Parse baseline
        template = {}
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
                ext = os.path.splitext(resolved_path)[1].lower()
                if ext in ['.yaml', '.yml']: template = yaml.safe_load(content)
                elif ext == '.json': template = json.loads(content)
                elif '.env' in resolved_path or resolved_path.endswith('.local'): template = self._parse_dotenv(content)
                elif ext == '.properties': template = self._parse_properties(content)
                elif resolved_path.endswith('pom.xml'): template = self._parse_pom_xml(content)
                elif 'Dockerfile' in resolved_path: template = self._parse_dockerfile(content)
                else: template = self._parse_dotenv(content) if '=' in content else json.loads(content)
        except Exception as e:
            return {
                "drift_detected": True,
                "drift_keys": [f"PARSE_ERROR: {str(e)}"],
                "resolved_path": resolved_path,
                "analysis_type": analysis_type
            }

        if not template:
            return {
                "drift_detected": True, 
                "drift_keys": ["EMPTY_BASELINE_FILE"], 
                "resolved_path": resolved_path, 
                "analysis_type": analysis_type
            }

        # 3. Perform Audit
        if integrity_mode:
            issues = self._find_value_issues(template)
        else:
            issues = self._find_missing_keys(template, actual_data)

        return {
            "drift_detected": len(issues) > 0,
            "drift_keys": list(set(issues)),
            "resolved_path": resolved_path,
            "analysis_type": analysis_type
        }

    def _resolve_fuzzy_path(self, path: str) -> str:
        if os.path.exists(path): return path
        if ".env" in path or path.endswith(".local") or path.endswith(".example"):
            base_dir = os.path.dirname(path) or "."
            for var in [".env", ".env.local", ".env.example", ".env.production"]:
                check_path = os.path.join(base_dir, var)
                if os.path.exists(check_path): return check_path
        return path

    def _find_value_issues(self, data: dict, prefix: str = "") -> List[str]:
        """Detects empty or 'placeholder' values while avoiding false positives."""
        issues = []
        # Exact match placeholders (case-insensitive)
        exact_placeholders = ["NONE", "NULL", "TODO", "CHANGE_ME", "PLACEHOLDER", "YOUR_KEY_HERE"]
        
        for key, value in data.items():
            full_key = f"{prefix}{key}"
            if value is None:
                issues.append(f"{full_key} (NULL)")
                continue
                
            if isinstance(value, str):
                v_strip = value.strip()
                v_upper = v_strip.upper()
                
                # 1. Empty check
                if not v_strip:
                    issues.append(f"{full_key} (EMPTY)")
                # 2. Strict placeholder check
                elif v_upper in exact_placeholders:
                    issues.append(f"{full_key} ({v_upper})")
                # 3. Pattern check for common placeholders
                elif any(p in v_upper for p in ["YOUR_KEY_HERE", "INSERT_SECRET"]):
                    issues.append(f"{full_key} (PLACEHOLDER)")
                # Note: We omit "EXAMPLE" from partial matches to avoid flagging "example.com"
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
