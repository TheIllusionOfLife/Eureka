"""Centralized execution configuration for MadSpark.

This module provides centralized configuration constants for all MadSpark operations.
All timeout values, limits, thresholds, and other configuration parameters should
be defined here for easy customization and maintenance.

Configuration is organized into logical classes:
- MultiModalConfig: File size limits and format support for URLs, PDFs, images
- TimeoutConfig: Workflow step timeouts and general timeout values
- ConcurrencyConfig: Thread pool sizes and concurrency limits
- RetryConfig: Retry attempts and backoff parameters for all agents
- LimitsConfig: Size limits, cache configuration, candidate limits
- ThresholdConfig: Similarity and detection thresholds
- TemperatureConfig: Temperature values for different operations
- ContentSafetyConfig: Content safety threshold settings
"""
import os


# ========================================
# Multi-Modal Input Limits
# ========================================
class MultiModalConfig:
    """Multi-modal input configuration.

    File size limits are DOUBLED from original proposal to support larger documents.
    """

    # File size limits (bytes) - DOUBLED for better multi-modal support
    MAX_FILE_SIZE = 20_000_000      # 20MB (was 10MB in original proposal)
    MAX_IMAGE_SIZE = 8_000_000      # 8MB (was 4MB in original proposal)
    MAX_PDF_SIZE = 40_000_000       # 40MB (was 20MB in original proposal)

    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
    SUPPORTED_DOC_FORMATS = {'pdf', 'txt', 'md', 'doc', 'docx'}

    # File type rules (format → (type_name, max_size))
    # More data-driven approach for validation
    FILE_TYPE_RULES = {
        'png': ('images', MAX_IMAGE_SIZE),
        'jpg': ('images', MAX_IMAGE_SIZE),
        'jpeg': ('images', MAX_IMAGE_SIZE),
        'webp': ('images', MAX_IMAGE_SIZE),
        'gif': ('images', MAX_IMAGE_SIZE),
        'bmp': ('images', MAX_IMAGE_SIZE),
        'pdf': ('PDFs', MAX_PDF_SIZE),
        'txt': ('documents', MAX_FILE_SIZE),
        'md': ('documents', MAX_FILE_SIZE),
        'doc': ('documents', MAX_FILE_SIZE),
        'docx': ('documents', MAX_FILE_SIZE),
    }

    # Processing limits
    MAX_PDF_PAGES = 100
    IMAGE_MAX_DIMENSION = 4096
    MAX_URL_CONTENT_LENGTH = 5_000_000  # 5MB


# ========================================
# API & Networking Timeouts
# ========================================
class TimeoutConfig:
    """Timeout configuration for all workflow operations.

    Values are reconciled between async_coordinator.py hardcoded values
    and workflow_constants.py definitions. Uses the longer timeout values
    to reduce premature timeout errors.
    """

    # General timeouts (in seconds)
    # Override via environment variables: MADSPARK_DEFAULT_TIMEOUT, MADSPARK_IDEA_TIMEOUT, etc.
    DEFAULT_REQUEST_TIMEOUT = float(os.getenv("MADSPARK_DEFAULT_TIMEOUT", "1200.0"))  # 20 minutes
    SHORT_TIMEOUT = 30.0
    MEDIUM_TIMEOUT = 60.0
    LONG_TIMEOUT = 120.0

    # Workflow step timeouts (from workflow_constants.py)
    # These are longer than the hardcoded values in async_coordinator.py
    # to reduce premature timeout errors
    # Increased significantly for Ollama which can be much slower than cloud APIs
    # Override via MADSPARK_*_TIMEOUT environment variables for per-environment tuning
    IDEA_GENERATION_TIMEOUT = float(os.getenv("MADSPARK_IDEA_TIMEOUT", "300.0"))  # 5 min
    EVALUATION_TIMEOUT = float(os.getenv("MADSPARK_EVAL_TIMEOUT", "300.0"))       # 5 min
    ADVOCACY_TIMEOUT = float(os.getenv("MADSPARK_ADVOCACY_TIMEOUT", "240.0"))     # 4 min
    SKEPTICISM_TIMEOUT = float(os.getenv("MADSPARK_SKEPTICISM_TIMEOUT", "240.0")) # 4 min
    IMPROVEMENT_TIMEOUT = float(os.getenv("MADSPARK_IMPROVEMENT_TIMEOUT", "300.0"))  # 5 min
    REEVALUATION_TIMEOUT = float(os.getenv("MADSPARK_REEVAL_TIMEOUT", "240.0"))   # 4 min
    MULTI_DIMENSIONAL_EVAL_TIMEOUT = float(os.getenv("MADSPARK_MULTIDIM_TIMEOUT", "300.0"))  # 5 min
    LOGICAL_INFERENCE_TIMEOUT = float(os.getenv("MADSPARK_INFERENCE_TIMEOUT", "240.0"))     # 4 min

    # URL fetch timeout (new for multi-modal support)
    URL_FETCH_TIMEOUT = 30.0


# ========================================
# Concurrency & Threading
# ========================================
class ConcurrencyConfig:
    """Thread pool and concurrency configuration.

    Controls parallelization across the MadSpark system.
    """

    # Thread pool sizes
    MAX_ASYNC_WORKERS = 4
    MAX_BATCH_WORKERS = 4
    BATCH_COORDINATOR_WORKERS = 1

    # Concurrency limits
    MAX_CONCURRENT_CACHE_OPS = 5


# ========================================
# Retry Configuration
# ========================================
class RetryConfig:
    """Retry and backoff configuration for all agents.

    Centralized retry parameters to ensure consistent error handling
    across the system.
    """

    # Default retry parameters (for exponential_backoff_retry function)
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_RETRY_DELAY = 1.0
    DEFAULT_BACKOFF_FACTOR = 2.0
    DEFAULT_MAX_RETRY_DELAY = 60.0

    # Agent-specific retry configurations
    # Values from agent_retry_wrappers.py
    IDEA_GENERATOR_MAX_RETRIES = 3
    IDEA_GENERATOR_INITIAL_DELAY = 2.0

    CRITIC_MAX_RETRIES = 3
    CRITIC_INITIAL_DELAY = 2.0

    ADVOCATE_MAX_RETRIES = 2
    ADVOCATE_INITIAL_DELAY = 1.0

    SKEPTIC_MAX_RETRIES = 2
    SKEPTIC_INITIAL_DELAY = 1.0

    IMPROVEMENT_MAX_RETRIES = 3
    IMPROVEMENT_INITIAL_DELAY = 2.0

    CONTENT_SAFETY_MAX_RETRIES = 3


# ========================================
# Size & Limit Configuration
# ========================================
class LimitsConfig:
    """Size and limit configuration for various operations."""

    # JSON parsing limits
    MAX_JSON_INPUT_SIZE = 1_000_000     # 1MB

    # Cache configuration
    MAX_CACHE_SIZE_MB = 100
    MAX_CACHE_KEYS_CHECK = 1000
    DEFAULT_CACHE_TTL = 3600            # 1 hour (in seconds)

    # Batch processing configuration
    CACHE_BATCH_SIZE = 10
    DEFAULT_BATCH_SIZE = 5

    # Candidate limits (for idea generation)
    MIN_NUM_CANDIDATES = 1
    MAX_NUM_CANDIDATES = 5
    DEFAULT_NUM_TOP_CANDIDATES = 3


# ========================================
# Threshold Configuration
# ========================================
class ThresholdConfig:
    """Similarity and threshold configuration.

    Controls duplicate detection, improvement detection,
    and context search sensitivity.
    """

    # Duplicate detection thresholds (0.0-1.0)
    EXACT_MATCH_THRESHOLD = 0.95
    HIGH_SIMILARITY_THRESHOLD = 0.8
    MEDIUM_SIMILARITY_THRESHOLD = 0.6

    # Improvement detection
    MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD = 0.9
    MEANINGFUL_IMPROVEMENT_SCORE_DELTA = 0.3

    # Context search thresholds (for enhanced_reasoning.py)
    CONTEXT_SIMILARITY_THRESHOLD = 0.5
    RELEVANT_CONTEXT_THRESHOLD = 0.3
    LOOSE_CONTEXT_THRESHOLD = 0.2

    # Score highlighting
    HIGH_SCORE_THRESHOLD = 7


# ========================================
# Temperature Configuration
# ========================================
class TemperatureConfig:
    """Temperature configuration for different LLM operations.

    Temperature controls randomness in LLM responses:
    - 0.0 = deterministic (same output each time)
    - 0.7 = balanced creativity and consistency
    - 2.0 = maximum creativity/randomness
    """

    DETERMINISTIC_TEMPERATURE = 0.0
    STANDARD_BASE_TEMPERATURE = 0.7
    REASONING_TEMPERATURE = 0.7


# ========================================
# Content Safety Configuration
# ========================================
class ContentSafetyConfig:
    """Content safety configuration for Gemini API.

    Controls how aggressively Gemini filters potentially harmful content.
    """

    # Gemini safety threshold setting
    # Options: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE
    SAFETY_THRESHOLD = "BLOCK_ONLY_HIGH"
