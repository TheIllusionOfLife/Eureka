"""Centralized import management for the MadSpark multi-agent system.

This module provides standardized import patterns and fallback logic to eliminate
code duplication across the codebase and ensure consistent behavior.
"""
import logging
from typing import Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ImportManager:
    """Centralized manager for handling imports with consistent fallback logic."""
    
    _genai_cache: Optional[Tuple[Any, Any, bool]] = None
    _dotenv_cache: Optional[Tuple[Any, Any, bool]] = None
    
    @classmethod
    def get_genai_modules(cls) -> Tuple[Optional[Any], Optional[Any], bool]:
        """Get Google GenAI modules with consistent fallback.
        
        Returns:
            Tuple of (genai module, types module, availability flag)
        """
        if cls._genai_cache is None:
            try:
                from google import genai
                from google.genai import types
                cls._genai_cache = (genai, types, True)
                logger.debug("Successfully imported Google GenAI modules")
            except ImportError as e:
                logger.debug(f"Google GenAI modules not available: {e}")
                cls._genai_cache = (None, None, False)
        
        return cls._genai_cache
    
    @classmethod
    def get_dotenv_modules(cls) -> Tuple[Optional[Any], Optional[Any], bool]:
        """Get python-dotenv modules with consistent fallback.
        
        Returns:
            Tuple of (load_dotenv function, find_dotenv function, availability flag)
        """
        if cls._dotenv_cache is None:
            try:
                from dotenv import load_dotenv, find_dotenv
                cls._dotenv_cache = (load_dotenv, find_dotenv, True)
                logger.debug("Successfully imported python-dotenv modules")
            except ImportError as e:
                logger.debug(f"python-dotenv modules not available: {e}")
                # Create dummy functions
                def dummy_load_dotenv(*args, **kwargs):
                    pass
                def dummy_find_dotenv(*args, **kwargs):
                    return None
                cls._dotenv_cache = (dummy_load_dotenv, dummy_find_dotenv, False)
        
        return cls._dotenv_cache
    
    @classmethod
    def safe_import_madspark_module(cls, module_path: str, fallback_relative: Optional[str] = None) -> Optional[Any]:
        """Import MadSpark module with standardized fallback pattern.
        
        Args:
            module_path: Full module path (e.g., 'madspark.utils.constants')
            fallback_relative: Optional relative import path (e.g., '..utils.constants')
            
        Returns:
            The imported module or None if unavailable
        """
        # Try primary package import
        try:
            parts = module_path.split('.')
            if len(parts) > 1:
                # Handle submodule import
                module = __import__(module_path, fromlist=[parts[-1]])
                return module
            else:
                return __import__(module_path)
        except ImportError:
            logger.debug(f"Primary import failed for {module_path}")
        
        # Try fallback relative import if provided
        if fallback_relative:
            try:
                # This requires the calling module to be in the right package context
                return __import__(fallback_relative, fromlist=[''])
            except ImportError:
                logger.debug(f"Fallback import failed for {fallback_relative}")
        
        logger.warning(f"Failed to import module: {module_path}")
        return None
    
    @classmethod
    def import_agent_dependencies(cls) -> dict:
        """Import common agent dependencies with fallback.
        
        Returns:
            Dictionary with imported modules and availability flags
        """
        dependencies = {}
        
        # Import novelty filter
        try:
            from madspark.utils.novelty_filter import NoveltyFilter
            dependencies['NoveltyFilter'] = NoveltyFilter
        except ImportError:
            try:
                from ..novelty_filter import NoveltyFilter
                dependencies['NoveltyFilter'] = NoveltyFilter
            except ImportError:
                dependencies['NoveltyFilter'] = None
                logger.warning("NoveltyFilter not available")
        
        # Import temperature control
        try:
            from madspark.utils.temperature_control import TemperatureManager
            dependencies['TemperatureManager'] = TemperatureManager
        except ImportError:
            try:
                from ..temperature_control import TemperatureManager
                dependencies['TemperatureManager'] = TemperatureManager
            except ImportError:
                dependencies['TemperatureManager'] = None
                logger.warning("TemperatureManager not available")
        
        # Import enhanced reasoning
        try:
            from madspark.core.enhanced_reasoning import ReasoningEngine
            dependencies['ReasoningEngine'] = ReasoningEngine
        except ImportError:
            try:
                from ..core.enhanced_reasoning import ReasoningEngine
                dependencies['ReasoningEngine'] = ReasoningEngine
            except ImportError:
                dependencies['ReasoningEngine'] = None
                logger.warning("ReasoningEngine not available")
        
        # Import constants
        try:
            from madspark.utils.constants import (
                DEFAULT_TIMEOUT_SECONDS, 
                DEFAULT_NOVELTY_THRESHOLD,
                DEFAULT_GOOGLE_GENAI_MODEL
            )
            dependencies['DEFAULT_TIMEOUT_SECONDS'] = DEFAULT_TIMEOUT_SECONDS
            dependencies['DEFAULT_NOVELTY_THRESHOLD'] = DEFAULT_NOVELTY_THRESHOLD
            dependencies['DEFAULT_GOOGLE_GENAI_MODEL'] = DEFAULT_GOOGLE_GENAI_MODEL
        except ImportError:
            # Set fallback defaults
            dependencies['DEFAULT_TIMEOUT_SECONDS'] = 1200
            dependencies['DEFAULT_NOVELTY_THRESHOLD'] = 0.8
            dependencies['DEFAULT_GOOGLE_GENAI_MODEL'] = "gemini-2.5-flash"
            logger.warning("Using fallback constants")
        
        return dependencies
    
    @classmethod
    def import_batch_functions(cls) -> dict:
        """Import batch processing functions with fallback.
        
        Returns:
            Dictionary of batch functions or empty dict if unavailable
        """
        batch_functions = {}
        
        try:
            from madspark.agents.advocate import advocate_ideas_batch
            batch_functions['advocate_ideas_batch'] = advocate_ideas_batch
        except ImportError:
            try:
                from ..agents.advocate import advocate_ideas_batch
                batch_functions['advocate_ideas_batch'] = advocate_ideas_batch
            except ImportError:
                logger.warning("advocate_ideas_batch not available")
        
        try:
            from madspark.agents.skeptic import criticize_ideas_batch
            batch_functions['criticize_ideas_batch'] = criticize_ideas_batch
        except ImportError:
            try:
                from ..agents.skeptic import criticize_ideas_batch
                batch_functions['criticize_ideas_batch'] = criticize_ideas_batch
            except ImportError:
                logger.warning("criticize_ideas_batch not available")
        
        try:
            from madspark.agents.idea_generator import improve_ideas_batch
            batch_functions['improve_ideas_batch'] = improve_ideas_batch
        except ImportError:
            try:
                from ..agents.idea_generator import improve_ideas_batch
                batch_functions['improve_ideas_batch'] = improve_ideas_batch
            except ImportError:
                logger.warning("improve_ideas_batch not available")
        
        return batch_functions
    
    @classmethod
    def is_mock_mode(cls) -> bool:
        """Check if the system should run in mock mode.
        
        Returns:
            True if mock mode is enabled, False otherwise
        """
        import os
        return os.getenv("MADSPARK_MODE", "").lower() == "mock"
    
    @classmethod
    def reset_cache(cls):
        """Reset import cache for testing purposes."""
        cls._genai_cache = None
        cls._dotenv_cache = None


# Convenience functions for backward compatibility
def get_genai_client_safe():
    """Get GenAI client with safe import handling."""
    genai, _, available = ImportManager.get_genai_modules()
    if not available or ImportManager.is_mock_mode():
        return None
    
    import os
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return genai.Client()
    return None


def load_env_file_safe():
    """Load environment file with safe import handling."""
    load_dotenv, find_dotenv, available = ImportManager.get_dotenv_modules()
    
    if available:
        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
        else:
            logger.debug("No .env file found in directory tree")
    else:
        logger.debug("python-dotenv not available, relying on environment variables")