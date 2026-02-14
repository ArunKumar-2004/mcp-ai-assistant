import json
import os
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("config_loader")

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

class ConfigLoader:
    def __init__(self, config_path: str = "readiness_schema.json"):
        self.config_path = Path(config_path)
        self.config = None

    def load(self, fail_fast: bool = True) -> dict:
        """
        Loads and validates the configuration.
        """
        if not self.config_path.exists():
            if fail_fast:
                raise ConfigError(
                    f"Config file not found: {self.config_path}\n"
                    f"To generate a default config, run the 'initialize_config' tool or: python server.py --init-config"
                )
            return {}

        self._read_json()
        self._validate_structure()
        self._apply_env_overrides()
        self._validate_env_vars()

        logger.info("Configuration validated and loaded successfully")
        return self.config

    def exists(self) -> bool:
        return self.config_path.exists()

    def _read_json(self):
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        except Exception as e:
            raise ConfigError(f"Invalid JSON format in {self.config_path}: {e}")

    def _validate_structure(self):
        required_top_keys = [
            "project_name",
            "projects",
            "mandatory_env_vars"
        ]

        for key in required_top_keys:
            if key not in self.config:
                raise ConfigError(f"Missing required top-level key: '{key}'")

        if not isinstance(self.config["projects"], dict):
            raise ConfigError("'projects' must be a JSON object")

        for proj_name, proj_data in self.config["projects"].items():
            if "environments" not in proj_data:
                raise ConfigError(f"Project '{proj_name}' is missing 'environments' object")
            
            for env_name, env_data in proj_data["environments"].items():
                required_env_keys = ["health_url", "db_url", "config_template"]
                for key in required_env_keys:
                    if key not in env_data:
                        raise ConfigError(f"Project '{proj_name}' env '{env_name}' is missing required key: '{key}'")

    def _apply_env_overrides(self):
        """
        Priority: ENV VAR > JSON Config.
        """
        # For multi-project, we skip simple global overrides for now
        pass

    def _validate_env_vars(self):
        missing = []
        for var in self.config.get("mandatory_env_vars", []):
            if not os.getenv(var):
                missing.append(var)

        if missing:
            raise ConfigError(
                "Missing required environment variables in .env:\n" +
                "\n".join([f" - {m}" for m in missing])
            )

    @staticmethod
    def discover_workspace_projects(root_dir: str = ".") -> dict:
        """
        Scans workspace for polyglot markers (React, Spring, Python, Docker, K8s).
        Returns a suggested project structure for readiness_schema.json.
        """
        discovered = {}
        root = Path(root_dir)
        
        # Discovery Markers
        markers = {
            "package.json": {"type": "frontend", "hint": "React/Node"},
            "pom.xml": {"type": "backend", "hint": "Spring Boot"},
            "pyproject.toml": {"type": "backend", "hint": "Python"},
            "requirements.txt": {"type": "backend", "hint": "Python"},
            "Dockerfile": {"type": "service", "hint": "Containerized"},
            "docker-compose.yml": {"type": "orchestration", "hint": "Docker Compose"},
            "k8s": {"type": "infrastructure", "hint": "Kubernetes"},
            ".github/workflows": {"type": "ci", "hint": "GitHub Actions"}
        }

        for marker_file, info in markers.items():
            # Check for files or directories
            search_pattern = f"**/{marker_file}"
            for p in root.glob(search_pattern):
                # Ignore common noise
                if any(x in str(p) for x in ["node_modules", "target", ".venv", ".git"]):
                    continue
                
                # Use absolute path to get folder name if p.parent is "."
                project_name = p.parent.resolve().name
                if project_name == "": project_name = "root-project"
                
                # Update discovered info (don't overwrite if already typed as specific app)
                if project_name not in discovered or discovered[project_name]["type"] == "service":
                    discovered[project_name] = {
                        "type": info["type"],
                        "path": str(p.parent),
                        "hint": info["hint"],
                        "repo": f"auto/{project_name}"
                    }

        return discovered

    @staticmethod
    def generate_default_config(path: str = "readiness_schema.json", discovered_projects: dict = None):
        """Utility to generate a starter config file."""
        projects = {}
        if discovered_projects:
            for name, data in discovered_projects.items():
                # Smart guessing for config templates
                template = "config/staging.json"
                if data["type"] == "backend":
                    template = "src/main/resources/application-staging.yml" if data["hint"] == "Spring Boot" else "config.yaml"
                elif data["type"] == "infrastructure":
                    template = "values.yaml"
                
                projects[name] = {
                    "repo": data["repo"],
                    "type_hint": data["hint"],
                    "environments": {
                        "staging": {
                            "health_url": f"http://localhost:8080/{name}/health",
                            "db_url": "none",
                            "config_template": f"{data['path']}/{template}"
                        }
                    }
                }

        default_config = {
            "project_name": "Enterprise Readiness Hub",
            "projects": projects or {
                "frontend": {
                    "repo": "owner/frontend-react-app",
                    "environments": {
                        "staging": {
                            "health_url": "http://localhost:8080/frontend/health",
                            "db_url": "none",
                            "config_template": "frontend-react-app/config/staging.json"
                        }
                    }
                }
            },
            "mandatory_env_vars": [
                "COHERE_API_KEY",
                "GITHUB_TOKEN"
            ],
            "timeouts": {
                "health_check_seconds": 10
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        print(f"Generated default config at {path}")
