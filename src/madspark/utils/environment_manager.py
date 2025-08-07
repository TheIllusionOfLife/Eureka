"""Centralized environment configuration management.

This module provides a singleton pattern for managing environment variables,
API keys, and operational modes across the MadSpark system.
"""
import os
import logging
from typing import Optional
from .import_manager import ImportManager

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Singleton environment configuration manager."""
    
    _instance: Optional['EnvironmentManager'] = None
    _loaded: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize environment manager."""
        if not self._loaded:
            self._load_environment()
            self._loaded = True
    
    def _load_environment(self):
        """Load environment variables from .env file if available."""
        load_dotenv, find_dotenv, available = ImportManager.get_dotenv_modules()
        
        if available:
            env_file = find_dotenv()
            if env_file:
                load_dotenv(env_file)
                logger.info(f"Environment loaded from {env_file}")
                return
            
        logger.debug("No .env file found, using environment variables")
    
    def get_api_key(self) -> Optional[str]:
        """Get validated Google API key.
        
        Returns:
            API key if configured and valid, None otherwise
        """
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        
        # Remove quotes if present
        if api_key:
            api_key = api_key.strip('"').strip("'")
        
        # Skip validation in mock mode
        if self.get_mode() == "mock":
            return api_key if api_key else "mock_key"
        
        # Basic validation for real API keys
        if api_key and api_key != "YOUR_API_KEY_HERE":
            # Google API keys typically start with "AIza" and are over 30 chars
            if api_key.startswith("AIza") and len(api_key) > 30:
                return api_key
            else:
                logger.warning("API key format appears invalid")
                
        return None
    
    def get_model_name(self) -> str:
        """Get configured model name with fallback.
        
        Returns:
            Model name from environment or default
        """
        return os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    
    def get_mode(self) -> str:
        """Get operational mode.
        
        Returns:
            'mock', 'api', or 'adk' based on configuration
        """
        mode = os.getenv("MADSPARK_MODE", "").lower()
        
        # Auto-detect mode based on API key availability
        if not mode:
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key or api_key == "YOUR_API_KEY_HERE":
                return "mock"
            else:
                return "api"
        
        return mode
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode.
        
        Returns:
            True if mock mode is enabled
        """
        return self.get_mode() == "mock"
    
    def is_api_key_configured(self) -> bool:
        """Check if API key is properly configured.
        
        Returns:
            True if API key is available and valid
        """
        return self.get_api_key() is not None
    
    def get_timeout_settings(self) -> dict:
        """Get timeout configuration.
        
        Returns:
            Dictionary with timeout settings
        """
        return {
            'default': int(os.getenv("MADSPARK_DEFAULT_TIMEOUT", "1200")),
            'min': int(os.getenv("MADSPARK_MIN_TIMEOUT", "60")),
            'max': int(os.getenv("MADSPARK_MAX_TIMEOUT", "3600"))
        }
    
    def get_performance_settings(self) -> dict:
        """Get performance-related settings.
        
        Returns:
            Dictionary with performance configuration
        """
        return {
            'novelty_threshold': float(os.getenv("MADSPARK_NOVELTY_THRESHOLD", "0.8")),
            'num_top_candidates': int(os.getenv("MADSPARK_TOP_CANDIDATES", "3")),
            'batch_size': int(os.getenv("MADSPARK_BATCH_SIZE", "5"))
        }
    
    def validate_environment(self) -> dict:
        """Validate environment configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check API key
        if not self.is_mock_mode():
            if not self.is_api_key_configured():
                issues.append("GOOGLE_API_KEY not configured or invalid")
        
        # Check model name
        model = self.get_model_name()
        if not model:
            warnings.append("No model name specified, using default")
        
        # Check timeout settings
        timeouts = self.get_timeout_settings()
        if timeouts['default'] < timeouts['min']:
            issues.append("Default timeout is less than minimum timeout")
        if timeouts['default'] > timeouts['max']:
            issues.append("Default timeout exceeds maximum timeout")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'mode': self.get_mode(),
            'api_key_configured': self.is_api_key_configured(),
            'model': self.get_model_name()
        }
    
    def ensure_environment_configured(self):
        """Ensure environment is properly configured with warnings."""
        validation = self.validate_environment()
        
        # Log warnings
        for warning in validation['warnings']:
            logger.warning(f"Environment warning: {warning}")
        
        # Handle issues based on mode
        if validation['issues']:
            if self.is_mock_mode():
                logger.info("Running in mock mode - API configuration issues ignored")
            else:
                for issue in validation['issues']:
                    logger.error(f"Environment error: {issue}")
                if not self.is_api_key_configured():
                    logger.warning(
                        "API key not configured. System will run in mock mode only.\n"
                        "Tip: Run 'mad_spark config' to configure your API key."
                    )
    
    def set_defaults(self):
        """Set default environment variables if not already set."""
        defaults = {
            'GOOGLE_GENAI_MODEL': 'gemini-2.5-flash',
            'MADSPARK_DEFAULT_TIMEOUT': '1200',
            'MADSPARK_MIN_TIMEOUT': '60',
            'MADSPARK_MAX_TIMEOUT': '3600',
            'MADSPARK_NOVELTY_THRESHOLD': '0.8',
            'MADSPARK_TOP_CANDIDATES': '3'
        }
        
        for key, value in defaults.items():
            if not os.getenv(key):
                os.environ[key] = value
                logger.debug(f"Set default {key}={value}")
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance for testing."""
        cls._instance = None
        cls._loaded = False


# Convenience function for global access
def get_environment_manager() -> EnvironmentManager:
    """Get singleton environment manager instance."""
    return EnvironmentManager()