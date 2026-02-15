import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("config_service")

class ConfigService:
    """
    Centralized configuration service that fetches environment configs from various sources.
    Supports: Environment Variables, JSON files, and extensible for Vault/AWS Secrets Manager.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize the config service.
        
        Args:
            config_dir: Directory containing environment config files (optional)
        """
        self.config_dir = config_dir or os.getenv("CONFIG_DIR", "./config")
        self.cache = {}
        
    def fetch_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Fetch configuration for a specific environment.
        
        Priority order:
        1. Environment variables (prefixed with ENV_NAME_)
        2. JSON config file (config/{environment}.json)
        3. YAML config file (config/{environment}.yaml)
        
        Args:
            environment: Environment name (e.g., 'production', 'staging', 'development')
            
        Returns:
            Dictionary of configuration key-value pairs
            
        Raises:
            RuntimeError: If no configuration source is available
        """
        logger.info(f"Fetching configuration for environment: {environment}")
        
        # Try environment variables first
        env_config = self._fetch_from_env_vars(environment)
        if env_config:
            logger.info(f"Loaded {len(env_config)} config values from environment variables")
            return env_config
        
        # Try JSON file
        json_config = self._fetch_from_json_file(environment)
        if json_config:
            logger.info(f"Loaded {len(json_config)} config values from JSON file")
            return json_config
        
        # Try YAML file
        yaml_config = self._fetch_from_yaml_file(environment)
        if yaml_config:
            logger.info(f"Loaded {len(yaml_config)} config values from YAML file")
            return yaml_config
        
        # No config found
        logger.error(f"No configuration found for environment: {environment}")
        raise RuntimeError(
            f"No configuration found for environment '{environment}'. "
            f"Please provide config via:\n"
            f"1. Environment variables (prefixed with {environment.upper()}_)\n"
            f"2. JSON file at {self.config_dir}/{environment}.json\n"
            f"3. YAML file at {self.config_dir}/{environment}.yaml"
        )
    
    def _fetch_from_env_vars(self, environment: str) -> Optional[Dict[str, Any]]:
        """
        Fetch config from environment variables.
        Looks for variables prefixed with {ENVIRONMENT}_ (e.g., PRODUCTION_DB_URL)
        """
        prefix = f"{environment.upper()}_"
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and store
                config_key = key[len(prefix):]
                config[config_key] = self._parse_value(value)
        
        return config if config else None
    
    def _fetch_from_json_file(self, environment: str) -> Optional[Dict[str, Any]]:
        """Fetch config from JSON file."""
        file_path = Path(self.config_dir) / f"{environment}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load JSON config from {file_path}: {e}")
            return None
    
    def _fetch_from_yaml_file(self, environment: str) -> Optional[Dict[str, Any]]:
        """Fetch config from YAML file."""
        try:
            import yaml
        except ImportError:
            logger.debug("PyYAML not installed, skipping YAML config loading")
            return None
        
        file_path = Path(self.config_dir) / f"{environment}.yaml"
        
        if not file_path.exists():
            # Also try .yml extension
            file_path = Path(self.config_dir) / f"{environment}.yml"
            if not file_path.exists():
                return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load YAML config from {file_path}: {e}")
            return None
    
    def _parse_value(self, value: str) -> Any:
        """
        Parse string value to appropriate type.
        Handles: int, float, bool, JSON objects/arrays
        """
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Try int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try JSON (for objects/arrays)
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # Return as string
        return value
    
    def get_config_value(self, environment: str, key: str, default: Any = None) -> Any:
        """
        Get a specific config value for an environment.
        
        Args:
            environment: Environment name
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            config = self.fetch_environment_config(environment)
            return config.get(key, default)
        except RuntimeError:
            return default
    
    def validate_required_keys(self, environment: str, required_keys: list) -> Dict[str, Any]:
        """
        Validate that all required keys are present in the configuration.
        
        Args:
            environment: Environment name
            required_keys: List of required configuration keys
            
        Returns:
            Configuration dictionary
            
        Raises:
            RuntimeError: If any required keys are missing
        """
        config = self.fetch_environment_config(environment)
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            raise RuntimeError(
                f"Missing required configuration keys for environment '{environment}': "
                f"{', '.join(missing_keys)}"
            )
        
        return config


class VaultConfigService(ConfigService):
    """
    Extended config service with HashiCorp Vault support.
    Requires: hvac library
    """
    
    def __init__(self, vault_url: str = None, vault_token: str = None, **kwargs):
        super().__init__(**kwargs)
        self.vault_url = vault_url or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.vault_client = None
        
        if self.vault_url and self.vault_token:
            try:
                import hvac
                self.vault_client = hvac.Client(url=self.vault_url, token=self.vault_token)
                logger.info("Vault client initialized successfully")
            except ImportError:
                logger.warning("hvac library not installed. Vault support disabled.")
            except Exception as e:
                logger.warning(f"Failed to initialize Vault client: {e}")
    
    def fetch_environment_config(self, environment: str) -> Dict[str, Any]:
        """Fetch config from Vault first, then fall back to parent implementation."""
        if self.vault_client:
            vault_config = self._fetch_from_vault(environment)
            if vault_config:
                logger.info(f"Loaded {len(vault_config)} config values from Vault")
                return vault_config
        
        # Fall back to standard sources
        return super().fetch_environment_config(environment)
    
    def _fetch_from_vault(self, environment: str) -> Optional[Dict[str, Any]]:
        """Fetch config from HashiCorp Vault."""
        if not self.vault_client:
            return None
        
        try:
            # Read from secret/data/{environment} path (KV v2)
            secret_path = f"secret/data/{environment}"
            response = self.vault_client.secrets.kv.v2.read_secret_version(
                path=environment,
                mount_point='secret'
            )
            return response['data']['data']
        except Exception as e:
            logger.warning(f"Failed to fetch from Vault: {e}")
            return None


class AWSSecretsManagerConfigService(ConfigService):
    """
    Extended config service with AWS Secrets Manager support.
    Requires: boto3 library
    """
    
    def __init__(self, region_name: str = None, **kwargs):
        super().__init__(**kwargs)
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.secrets_client = None
        
        try:
            import boto3
            self.secrets_client = boto3.client('secretsmanager', region_name=self.region_name)
            logger.info("AWS Secrets Manager client initialized successfully")
        except ImportError:
            logger.warning("boto3 library not installed. AWS Secrets Manager support disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize AWS Secrets Manager client: {e}")
    
    def fetch_environment_config(self, environment: str) -> Dict[str, Any]:
        """Fetch config from AWS Secrets Manager first, then fall back to parent implementation."""
        if self.secrets_client:
            aws_config = self._fetch_from_aws_secrets(environment)
            if aws_config:
                logger.info(f"Loaded {len(aws_config)} config values from AWS Secrets Manager")
                return aws_config
        
        # Fall back to standard sources
        return super().fetch_environment_config(environment)
    
    def _fetch_from_aws_secrets(self, environment: str) -> Optional[Dict[str, Any]]:
        """Fetch config from AWS Secrets Manager."""
        if not self.secrets_client:
            return None
        
        try:
            # Secret name format: {environment}/config
            secret_name = f"{environment}/config"
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret string (should be JSON)
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                logger.warning(f"Secret {secret_name} is binary, expected JSON string")
                return None
        except Exception as e:
            logger.warning(f"Failed to fetch from AWS Secrets Manager: {e}")
            return None
