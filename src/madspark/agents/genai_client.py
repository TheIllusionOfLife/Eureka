"""Shared Google GenAI client utilities.

This module provides centralized client initialization for all agents,
following the DRY principle to avoid code duplication.
Enhanced with centralized import and environment management.
"""
import os
import logging
from typing import Optional, Dict, Any

# Use centralized import and environment management
try:
    from ..utils.import_manager import ImportManager
    from ..utils.environment_manager import EnvironmentManager
    _CENTRALIZED_AVAILABLE = True
except ImportError:
    # Fallback to original implementation for backward compatibility
    _CENTRALIZED_AVAILABLE = False

# Maintain backward compatibility
if _CENTRALIZED_AVAILABLE:
    genai, _, GENAI_AVAILABLE = ImportManager.get_genai_modules()
else:
    try:
        from google import genai
        GENAI_AVAILABLE = True
    except ImportError:
        genai = None
        GENAI_AVAILABLE = False
    
    # Backward compatibility for dotenv
    try:
        from dotenv import load_dotenv, find_dotenv
        DOTENV_AVAILABLE = True
    except ImportError:
        DOTENV_AVAILABLE = False
        
        def load_dotenv(*args, **kwargs):
            """Dummy function when python-dotenv is not available."""
            pass
        
        def find_dotenv(*args, **kwargs):
            """Dummy function when python-dotenv is not available."""
            return None


def get_genai_client() -> Optional['genai.Client']:
    """Get a configured Google GenAI client instance.
    
    Returns:
        A configured genai.Client instance if API key is available,
        None otherwise.
        
    Note:
        The client reads GOOGLE_API_KEY from environment directly.
        This is the expected behavior for the new google-genai SDK.
    """
    if not GENAI_AVAILABLE:
        return None
    
    if _CENTRALIZED_AVAILABLE:
        env_manager = EnvironmentManager()
        if env_manager.is_mock_mode():
            return None
        api_key = env_manager.get_api_key()
        if api_key:
            return genai.Client()
        return None
    else:
        # Fallback to original implementation
        if get_mode() == "mock":
            return None
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            return genai.Client()
        else:
            logging.warning("GOOGLE_API_KEY not found in environment")
            return None


def get_model_name() -> str:
    """Get the configured model name from environment.
    
    Returns:
        The model name from environment or default "gemini-2.5-flash".
    """
    if _CENTRALIZED_AVAILABLE:
        env_manager = EnvironmentManager()
        return env_manager.get_model_name()
    else:
        # Fallback to original implementation
        return os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")


def load_env_file():
    """Load environment variables from .env file if it exists."""
    if _CENTRALIZED_AVAILABLE:
        # Environment manager handles this automatically
        EnvironmentManager()
    else:
        # Fallback to original implementation
        if DOTENV_AVAILABLE:
            env_file = find_dotenv()
            if env_file:
                load_dotenv(env_file)

# Load environment variables when module is imported
load_env_file()


def is_api_key_configured() -> bool:
    """Check if a valid API key is configured.
    
    Returns:
        True if API key is present and appears valid, False otherwise.
    """
    if _CENTRALIZED_AVAILABLE:
        env_manager = EnvironmentManager()
        return env_manager.is_api_key_configured()
    else:
        # Fallback to original implementation
        load_env_file()
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if api_key and api_key != "YOUR_API_KEY_HERE":
            api_key = api_key.strip('"').strip("'")
            return api_key.startswith("AIza") and len(api_key) > 30
        return False


def get_mode() -> str:
    """Determine the operating mode (api or mock).
    
    Returns:
        'api' if API mode should be used, 'mock' otherwise.
        
    Priority:
    1. MADSPARK_MODE environment variable (explicit override)
    2. API key presence (auto-detection)
    3. Default to mock mode
    """
    if _CENTRALIZED_AVAILABLE:
        env_manager = EnvironmentManager()
        return env_manager.get_mode()
    else:
        # Fallback to original implementation
        explicit_mode = os.getenv("MADSPARK_MODE", "").lower()
        if explicit_mode in ["api", "mock"]:
            return explicit_mode
        if is_api_key_configured():
            return "api"
        else:
            return "mock"


class GenAIClientManager:
    """Enhanced client manager with caching and agent-specific configuration."""
    
    _clients: Dict[str, Any] = {}
    _model_configs: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_client_for_agent(cls, agent_name: str) -> Optional[Any]:
        """Get configured client for specific agent with caching.
        
        Args:
            agent_name: Name of the agent requesting the client
            
        Returns:
            Configured client or None if unavailable
        """
        if agent_name not in cls._clients:
            client = get_genai_client()
            cls._clients[agent_name] = client
            if client:
                logging.debug(f"Created GenAI client for {agent_name}")
        
        return cls._clients[agent_name]
    
    @classmethod
    def get_model_config(cls, agent_name: str) -> Dict[str, Any]:
        """Get agent-specific model configuration.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Configuration dictionary for the agent
        """
        if agent_name not in cls._model_configs:
            base_config = {
                'model': get_model_name(),
                'temperature': 0.7,  # Default temperature
            }
            
            # Agent-specific configurations
            agent_configs = {
                'advocate': {'temperature': 0.5},
                'critic': {'temperature': 0.3},
                'skeptic': {'temperature': 0.5},
                'idea_generator': {'temperature': 0.9}
            }
            
            if agent_name in agent_configs:
                base_config.update(agent_configs[agent_name])
            
            cls._model_configs[agent_name] = base_config
        
        return cls._model_configs[agent_name].copy()
    
    @classmethod
    def is_mock_mode(cls) -> bool:
        """Centralized mock mode detection."""
        return get_mode() == "mock"
    
    @classmethod
    def reset_cache(cls):
        """Reset client cache (useful for testing)."""
        cls._clients.clear()
        cls._model_configs.clear()