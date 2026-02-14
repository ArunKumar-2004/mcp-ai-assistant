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
        Compares configuration. 
        If integrity_mode=True (single-env), skips drift detection and performs an Integrity Audit.
        Otherwise, performs a Cross-Environment Drift Analysis.
        """
        issues = []
        analysis_type = "INTEGRITY" if integrity_mode else "DRIFT"
        
        # Load baseline for context (even in integrity mode, we might want to check against expected keys)
        template = {}
        if os.path.exists(template_path):
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    ext = os.path.splitext(template_path)[1].lower()
                    if ext in ['.yaml', '.yml']: template = yaml.safe_load(content)
                    elif ext == '.json': template = json.loads(content)
                    elif '.env' in template_path or template_path.endswith('.local'): template = self._parse_dotenv(content)
                    elif ext == '.properties': template = self._parse_properties(content)
                    elif template_path.endswith('pom.xml'): template = self._parse_pom_xml(content)
                    elif 'Dockerfile' in template_path: template = self._parse_dockerfile(content)
                    else: template = self._parse_dotenv(content) # Fallback to flat/env
            except Exception as e:
                logger.error(f"Failed to parse baseline {template_path}: {e}")

        if integrity_mode:
            # For single-environment projects, audit the configuration file itself for completion
            issues = self._find_value_issues(template)
        else:
            # For multi-environment projects, identify drift between baseline and target
            if template:
                issues = self._find_missing_keys(template, actual_data)

        issues = list(set(issues))
        explanation = self._generate_explanation(template_path, issues, integrity_mode)
        suggested_fix = self._generate_suggested_fix(template_path, issues, integrity_mode)

        return {
            "drift_detected": len(issues) > 0,
            "drift_keys": issues,
            "explanation": explanation,
            "suggested_fix": suggested_fix,
            "version_mismatch": False,
            "analysis_type": analysis_type
        }

    def _generate_explanation(self, path: str, issues: List[str], integrity_mode: bool) -> str:
        file_name = os.path.basename(path)
        if not issues:
            return f"✅ Readiness Audit Passed. The environment configuration is complete and contains no empty or placeholder values." if integrity_mode else f"✅ Configuration Alignment Verified. No drift detected between the target environment and the '{file_name}' baseline."

        count = len(issues)
        if integrity_mode:
            return f"⚠️ Readiness Alert: Your environment setup is incomplete. {count} configuration key(s) are currently set to empty or placeholder values (e.g., TODO/CHANGE_ME). This will prevent a successful deployment."
        else:
            return f"❌ Deployment Risk: Configuration drift detected. {count} key(s) defined in your baseline '{file_name}' are missing from the target environment. This environment is out of sync with your deployment template."

    def _generate_suggested_fix(self, path: str, issues: List[str], integrity_mode: bool) -> str:
        if not issues:
            return "No remediation required. Your configuration adheres to the defined deployment standard."

        file_name = os.path.basename(path)
        if integrity_mode:
            formatted_issues = "\n".join([f"  - {i}" for i in issues])
            return f"To finalize your setup, replace the placeholders or empty strings for the following keys with real secrets or valid configuration values:\n\n{formatted_issues}\n\nSearch your .env or configuration files for 'TODO' or 'CHANGE_ME' to find these items."
        else:
            formatted_issues = "\n".join([f"  - {i}" for i in issues])
            return f"To align this environment with the '{file_name}' baseline, append the following missing keys to your target configuration:\n\n{formatted_issues}"

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
