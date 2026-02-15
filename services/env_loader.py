"""
Flexible environment variable loader with regex pattern matching.
Supports multiple naming conventions for the same configuration.
"""
import os
import re
from typing import Optional, List

class FlexibleEnvLoader:
    """
    Load environment variables using flexible regex patterns.
    Supports multiple naming conventions (GITHUB_TOKEN, GH_TOKEN, etc.)
    """
    
    # Define patterns for common environment variables
    PATTERNS = {
        'github_token': [
            r'^GITHUB.*TOKEN$',
            r'^GH.*TOKEN$',
            r'^GITHUB.*PAT$',
            r'^.*GITHUB.*TOKEN.*$'
        ],
        'github_repo': [
            r'^GITHUB.*REPO',
            r'^GH.*REPO',
            r'^REPO.*NAME$',
            r'^.*REPOSITORY.*$'
        ],
        'cohere_key': [
            r'^COHERE.*KEY$',
            r'^COHERE.*API',
            r'^.*COHERE.*$'
        ],
        'slack_webhook': [
            r'^SLACK.*WEBHOOK',
            r'^WEBHOOK.*URL$',
            r'^.*SLACK.*$'
        ],
        'db_url': [
            r'^.*DB.*URL$',
            r'^DATABASE.*URL$',
            r'^.*CONNECTION.*STRING$'
        ]
    }
    
    @classmethod
    def get_env(cls, key: str, default: Optional[str] = None, patterns: Optional[List[str]] = None) -> Optional[str]:
        """
        Get environment variable using flexible pattern matching.
        
        Args:
            key: The logical key name (e.g., 'github_token')
            default: Default value if not found
            patterns: Optional custom regex patterns to use
            
        Returns:
            Environment variable value or default
        """
        # First try exact match
        if key.upper() in os.environ:
            return os.environ[key.upper()]
        
        # Use predefined patterns or custom patterns
        search_patterns = patterns or cls.PATTERNS.get(key.lower(), [])
        
        # Search through all environment variables
        for env_var, value in os.environ.items():
            for pattern in search_patterns:
                if re.match(pattern, env_var, re.IGNORECASE):
                    return value
        
        return default
    
    @classmethod
    def get_github_token(cls) -> Optional[str]:
        """Get GitHub token from any common environment variable name."""
        return cls.get_env('github_token')
    
    @classmethod
    def get_github_repo(cls) -> Optional[str]:
        """Get GitHub repository from any common environment variable name."""
        return cls.get_env('github_repo')
    
    @classmethod
    def get_cohere_key(cls) -> Optional[str]:
        """Get Cohere API key from any common environment variable name."""
        return cls.get_env('cohere_key')
    
    @classmethod
    def get_slack_webhook(cls) -> Optional[str]:
        """Get Slack webhook URL from any common environment variable name."""
        return cls.get_env('slack_webhook')
    
    @classmethod
    def get_db_url(cls) -> Optional[str]:
        """Get database URL from any common environment variable name."""
        return cls.get_env('db_url')
    
    @classmethod
    def debug_print_matches(cls):
        """Print all matched environment variables for debugging."""
        import logging
        logger = logging.getLogger("env_loader")
        
        for key, patterns in cls.PATTERNS.items():
            matches = []
            for env_var in os.environ.keys():
                for pattern in patterns:
                    if re.match(pattern, env_var, re.IGNORECASE):
                        matches.append(f"{env_var}={os.environ[env_var][:20]}...")
                        break
            
            if matches:
                logger.info(f"✅ {key}: Found {len(matches)} match(es)")
                for match in matches:
                    logger.info(f"   - {match}")
            else:
                logger.warning(f"⚠️  {key}: No matches found")
