"""Compatibility layer for package vs relative imports.

This module provides helper functions to import components with automatic fallback
from absolute (package) imports to relative imports, supporting both installed and
development modes.

This eliminates code duplication from having try/except ImportError blocks across
multiple modules.
"""


def import_agent_retry_wrappers():
    """Import agent retry wrapper functions with fallback logic.

    Returns:
        dict: Dictionary mapping function names to their import objects.
            Keys:
                - generate_ideas_with_retry
                - evaluate_ideas_with_retry
                - advocate_idea_with_retry
                - criticize_idea_with_retry
                - improve_idea_with_retry
    """
    try:
        from madspark.utils.agent_retry_wrappers import (
            generate_ideas_with_retry,
            evaluate_ideas_with_retry,
            advocate_idea_with_retry,
            criticize_idea_with_retry,
            improve_idea_with_retry
        )
    except ImportError:
        from .agent_retry_wrappers import (
            generate_ideas_with_retry,
            evaluate_ideas_with_retry,
            advocate_idea_with_retry,
            criticize_idea_with_retry,
            improve_idea_with_retry
        )

    return {
        'generate_ideas_with_retry': generate_ideas_with_retry,
        'evaluate_ideas_with_retry': evaluate_ideas_with_retry,
        'advocate_idea_with_retry': advocate_idea_with_retry,
        'criticize_idea_with_retry': criticize_idea_with_retry,
        'improve_idea_with_retry': improve_idea_with_retry
    }


def import_core_components():
    """Import core coordinator components with fallback logic.

    Returns:
        dict: Dictionary mapping component names to their import objects.
            Keys:
                - run_multistep_workflow
                - AsyncCoordinator
                - TemperatureManager
                - CacheManager
                - ExportManager
                - DEFAULT_NUM_TOP_CANDIDATES
    """
    try:
        from madspark.core.coordinator import run_multistep_workflow
        from madspark.core.async_coordinator import AsyncCoordinator
        from madspark.utils.temperature_control import TemperatureManager
        from madspark.utils.cache_manager import CacheManager
        from madspark.utils.export_utils import ExportManager
        from madspark.utils.constants import DEFAULT_NUM_TOP_CANDIDATES
    except ImportError:
        from ..core.coordinator import run_multistep_workflow
        from ..core.async_coordinator import AsyncCoordinator
        from .temperature_control import TemperatureManager
        from .cache_manager import CacheManager
        from .export_utils import ExportManager
        from .constants import DEFAULT_NUM_TOP_CANDIDATES

    return {
        'run_multistep_workflow': run_multistep_workflow,
        'AsyncCoordinator': AsyncCoordinator,
        'TemperatureManager': TemperatureManager,
        'CacheManager': CacheManager,
        'ExportManager': ExportManager,
        'DEFAULT_NUM_TOP_CANDIDATES': DEFAULT_NUM_TOP_CANDIDATES
    }


def import_genai_and_constants():
    """Import genai client and constants with fallback logic.

    Returns:
        dict: Dictionary mapping names to their import objects.
            Keys:
                - DEFAULT_IDEA_TEMPERATURE
                - DEFAULT_EVALUATION_TEMPERATURE
                - DEFAULT_NUM_TOP_CANDIDATES
                - get_genai_client
    """
    try:
        from madspark.utils.constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE,
            DEFAULT_NUM_TOP_CANDIDATES
        )
        from madspark.agents.genai_client import get_genai_client
    except ImportError:
        from ..utils.constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE,
            DEFAULT_NUM_TOP_CANDIDATES
        )
        from ..agents.genai_client import get_genai_client

    return {
        'DEFAULT_IDEA_TEMPERATURE': DEFAULT_IDEA_TEMPERATURE,
        'DEFAULT_EVALUATION_TEMPERATURE': DEFAULT_EVALUATION_TEMPERATURE,
        'DEFAULT_NUM_TOP_CANDIDATES': DEFAULT_NUM_TOP_CANDIDATES,
        'get_genai_client': get_genai_client
    }


def import_batch_functions():
    """Import batch processing functions with fallback logic.

    Returns:
        dict: Dictionary mapping function names to their import objects.
            Keys:
                - advocate_ideas_batch
                - criticize_ideas_batch
                - improve_ideas_batch
    """
    try:
        from madspark.agents.advocate import advocate_ideas_batch
        from madspark.agents.skeptic import criticize_ideas_batch
        from madspark.agents.idea_generator import improve_ideas_batch
    except ImportError:
        from ..agents.advocate import advocate_ideas_batch
        from ..agents.skeptic import criticize_ideas_batch
        from ..agents.idea_generator import improve_ideas_batch

    return {
        'advocate_ideas_batch': advocate_ideas_batch,
        'criticize_ideas_batch': criticize_ideas_batch,
        'improve_ideas_batch': improve_ideas_batch
    }


def import_coordinator_batch_retry_wrappers():
    """Import retry wrappers specific to coordinator_batch with fallback logic.

    Returns:
        dict: Dictionary mapping function names to their import objects.
            Keys:
                - call_idea_generator_with_retry
                - call_critic_with_retry
    """
    try:
        from madspark.utils.agent_retry_wrappers import (
            call_idea_generator_with_retry,
            call_critic_with_retry
        )
    except ImportError:
        from ..utils.agent_retry_wrappers import (
            call_idea_generator_with_retry,
            call_critic_with_retry
        )

    return {
        'call_idea_generator_with_retry': call_idea_generator_with_retry,
        'call_critic_with_retry': call_critic_with_retry
    }
