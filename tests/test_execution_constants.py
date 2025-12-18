"""Tests for centralized execution constants.

This test module follows TDD - written BEFORE implementation.
Tests verify the configuration centralization works correctly.
"""
import pytest


class TestMultiModalConfig:
    """Test multi-modal configuration."""

    def test_file_size_limits_doubled(self):
        """Verify file sizes are doubled from original proposal."""
        from madspark.config.execution_constants import MultiModalConfig

        assert MultiModalConfig.MAX_FILE_SIZE == 20_000_000  # 20MB
        assert MultiModalConfig.MAX_IMAGE_SIZE == 8_000_000  # 8MB
        assert MultiModalConfig.MAX_PDF_SIZE == 40_000_000   # 40MB

    def test_supported_image_formats(self):
        """Verify supported image format set."""
        from madspark.config.execution_constants import MultiModalConfig

        assert 'png' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'jpg' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'jpeg' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'webp' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert len(MultiModalConfig.SUPPORTED_IMAGE_FORMATS) >= 5

    def test_supported_doc_formats(self):
        """Verify supported document format set."""
        from madspark.config.execution_constants import MultiModalConfig

        assert 'pdf' in MultiModalConfig.SUPPORTED_DOC_FORMATS
        assert 'txt' in MultiModalConfig.SUPPORTED_DOC_FORMATS
        assert 'md' in MultiModalConfig.SUPPORTED_DOC_FORMATS

    def test_processing_limits(self):
        """Verify processing limits are defined."""
        from madspark.config.execution_constants import MultiModalConfig

        assert MultiModalConfig.MAX_PDF_PAGES > 0
        assert MultiModalConfig.IMAGE_MAX_DIMENSION > 0
        assert MultiModalConfig.MAX_URL_CONTENT_LENGTH > 0


class TestTimeoutConfig:
    """Test timeout configuration."""

    def test_workflow_timeouts_defined(self):
        """Verify all workflow step timeouts exist and are positive."""
        from madspark.config.execution_constants import TimeoutConfig

        assert TimeoutConfig.IDEA_GENERATION_TIMEOUT > 0
        assert TimeoutConfig.EVALUATION_TIMEOUT > 0
        assert TimeoutConfig.ADVOCACY_TIMEOUT > 0
        assert TimeoutConfig.SKEPTICISM_TIMEOUT > 0
        assert TimeoutConfig.IMPROVEMENT_TIMEOUT > 0
        assert TimeoutConfig.REEVALUATION_TIMEOUT > 0
        assert TimeoutConfig.MULTI_DIMENSIONAL_EVAL_TIMEOUT > 0
        assert TimeoutConfig.LOGICAL_INFERENCE_TIMEOUT > 0

    def test_general_timeouts(self):
        """Verify general timeout hierarchy."""
        from madspark.config.execution_constants import TimeoutConfig

        assert TimeoutConfig.SHORT_TIMEOUT < TimeoutConfig.MEDIUM_TIMEOUT
        assert TimeoutConfig.MEDIUM_TIMEOUT < TimeoutConfig.LONG_TIMEOUT
        assert TimeoutConfig.LONG_TIMEOUT < TimeoutConfig.DEFAULT_REQUEST_TIMEOUT

    def test_url_fetch_timeout(self):
        """Verify URL fetch timeout for multi-modal support."""
        from madspark.config.execution_constants import TimeoutConfig

        assert TimeoutConfig.URL_FETCH_TIMEOUT > 0
        assert TimeoutConfig.URL_FETCH_TIMEOUT <= TimeoutConfig.MEDIUM_TIMEOUT


class TestConcurrencyConfig:
    """Test concurrency configuration."""

    def test_worker_counts(self):
        """Verify all worker counts are positive."""
        from madspark.config.execution_constants import ConcurrencyConfig

        assert ConcurrencyConfig.MAX_ASYNC_WORKERS > 0
        assert ConcurrencyConfig.MAX_BATCH_WORKERS > 0
        assert ConcurrencyConfig.BATCH_COORDINATOR_WORKERS > 0
        assert ConcurrencyConfig.MAX_CONCURRENT_CACHE_OPS > 0

    def test_worker_counts_reasonable(self):
        """Verify worker counts are reasonable (not too high)."""
        from madspark.config.execution_constants import ConcurrencyConfig

        # Should not exceed typical CPU count
        assert ConcurrencyConfig.MAX_ASYNC_WORKERS <= 16
        assert ConcurrencyConfig.MAX_BATCH_WORKERS <= 16


class TestRetryConfig:
    """Test retry configuration."""

    def test_default_retry_params(self):
        """Verify default retry parameters are sensible."""
        from madspark.config.execution_constants import RetryConfig

        assert RetryConfig.DEFAULT_MAX_RETRIES >= 1
        assert RetryConfig.DEFAULT_INITIAL_RETRY_DELAY > 0
        assert RetryConfig.DEFAULT_BACKOFF_FACTOR >= 1.0
        assert RetryConfig.DEFAULT_MAX_RETRY_DELAY > RetryConfig.DEFAULT_INITIAL_RETRY_DELAY

    def test_agent_retry_configs(self):
        """Verify all agents have retry configs."""
        from madspark.config.execution_constants import RetryConfig

        assert RetryConfig.IDEA_GENERATOR_MAX_RETRIES > 0
        assert RetryConfig.CRITIC_MAX_RETRIES > 0
        assert RetryConfig.ADVOCATE_MAX_RETRIES > 0
        assert RetryConfig.SKEPTIC_MAX_RETRIES > 0
        assert RetryConfig.IMPROVEMENT_MAX_RETRIES > 0

    def test_agent_initial_delays(self):
        """Verify all agents have initial delay configs."""
        from madspark.config.execution_constants import RetryConfig

        assert RetryConfig.IDEA_GENERATOR_INITIAL_DELAY > 0
        assert RetryConfig.CRITIC_INITIAL_DELAY > 0
        assert RetryConfig.ADVOCATE_INITIAL_DELAY > 0
        assert RetryConfig.SKEPTIC_INITIAL_DELAY > 0
        assert RetryConfig.IMPROVEMENT_INITIAL_DELAY > 0


class TestLimitsConfig:
    """Test limits configuration."""

    def test_size_limits(self):
        """Verify size limits are positive."""
        from madspark.config.execution_constants import LimitsConfig

        assert LimitsConfig.MAX_JSON_INPUT_SIZE > 0
        assert LimitsConfig.MAX_CACHE_SIZE_MB > 0
        assert LimitsConfig.MAX_CACHE_KEYS_CHECK > 0

    def test_candidate_limits(self):
        """Verify candidate limits are logical."""
        from madspark.config.execution_constants import LimitsConfig

        assert LimitsConfig.MIN_NUM_CANDIDATES >= 1
        assert LimitsConfig.MAX_NUM_CANDIDATES >= LimitsConfig.MIN_NUM_CANDIDATES
        assert LimitsConfig.DEFAULT_NUM_TOP_CANDIDATES >= LimitsConfig.MIN_NUM_CANDIDATES
        assert LimitsConfig.DEFAULT_NUM_TOP_CANDIDATES <= LimitsConfig.MAX_NUM_CANDIDATES

    def test_cache_config(self):
        """Verify cache configuration."""
        from madspark.config.execution_constants import LimitsConfig

        assert LimitsConfig.DEFAULT_CACHE_TTL > 0
        assert LimitsConfig.CACHE_BATCH_SIZE > 0
        assert LimitsConfig.DEFAULT_BATCH_SIZE > 0


class TestThresholdConfig:
    """Test threshold configuration."""

    def test_similarity_thresholds(self):
        """Verify similarity thresholds are in valid range."""
        from madspark.config.execution_constants import ThresholdConfig

        assert 0.0 <= ThresholdConfig.EXACT_MATCH_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.HIGH_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD <= 1.0

    def test_threshold_ordering(self):
        """Verify thresholds are properly ordered."""
        from madspark.config.execution_constants import ThresholdConfig

        # Should be ordered from high to low
        assert ThresholdConfig.EXACT_MATCH_THRESHOLD >= ThresholdConfig.HIGH_SIMILARITY_THRESHOLD
        assert ThresholdConfig.HIGH_SIMILARITY_THRESHOLD >= ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD

    def test_improvement_thresholds(self):
        """Verify improvement detection thresholds."""
        from madspark.config.execution_constants import ThresholdConfig

        assert 0.0 <= ThresholdConfig.MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD <= 1.0
        assert ThresholdConfig.MEANINGFUL_IMPROVEMENT_SCORE_DELTA > 0

    def test_context_search_thresholds(self):
        """Verify context search thresholds."""
        from madspark.config.execution_constants import ThresholdConfig

        assert 0.0 <= ThresholdConfig.CONTEXT_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.RELEVANT_CONTEXT_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.LOOSE_CONTEXT_THRESHOLD <= 1.0

        # Should be ordered from strict to loose
        assert ThresholdConfig.CONTEXT_SIMILARITY_THRESHOLD >= ThresholdConfig.RELEVANT_CONTEXT_THRESHOLD
        assert ThresholdConfig.RELEVANT_CONTEXT_THRESHOLD >= ThresholdConfig.LOOSE_CONTEXT_THRESHOLD


class TestTemperatureConfig:
    """Test temperature configuration."""

    def test_temperature_ranges(self):
        """Verify temperature values are in valid range."""
        from madspark.config.execution_constants import TemperatureConfig

        # Temperature typically 0.0-2.0 for Gemini
        assert 0.0 <= TemperatureConfig.DETERMINISTIC_TEMPERATURE <= 2.0
        assert 0.0 <= TemperatureConfig.STANDARD_BASE_TEMPERATURE <= 2.0
        assert 0.0 <= TemperatureConfig.REASONING_TEMPERATURE <= 2.0

    def test_deterministic_is_zero(self):
        """Verify deterministic temperature is zero."""
        from madspark.config.execution_constants import TemperatureConfig

        assert TemperatureConfig.DETERMINISTIC_TEMPERATURE == 0.0


class TestContentSafetyConfig:
    """Test content safety configuration."""

    def test_safety_threshold_value(self):
        """Verify safety threshold is a valid Gemini setting."""
        from madspark.config.execution_constants import ContentSafetyConfig

        valid_settings = [
            "BLOCK_NONE",
            "BLOCK_ONLY_HIGH",
            "BLOCK_MEDIUM_AND_ABOVE",
            "BLOCK_LOW_AND_ABOVE"
        ]

        assert ContentSafetyConfig.SAFETY_THRESHOLD in valid_settings


class TestConstantUsage:
    """Test that constants are actually used in codebase after migration."""

    def test_no_hardcoded_timeouts_in_async_coordinator(self):
        """Verify AsyncCoordinator uses config constants."""
        # This test will pass after migration is complete
        module = pytest.importorskip("madspark.core.async_coordinator")
        import inspect
        source = inspect.getsource(module)

        # Should not contain hardcoded timeout values
        import re
        # Look for timeout=<number> pattern (but allow timeout=0)
        hardcoded_timeouts = re.findall(r'timeout=(?!0\.?0?\b)\d+\.?\d*(?!\w)', source)

        assert len(hardcoded_timeouts) == 0, \
            f"Found hardcoded timeouts in async_coordinator: {hardcoded_timeouts}"

    def test_no_hardcoded_max_workers(self):
        """Verify thread pools use config constants."""
        # This test will pass after migration is complete
        module = pytest.importorskip("madspark.core.batch_operations_base")
        import inspect
        source = inspect.getsource(module)

        # Should not contain max_workers=4
        assert 'max_workers=4' not in source, \
            "Found hardcoded max_workers=4 in batch_operations_base"

    def test_no_hardcoded_model_names(self):
        """Verify model names use constant."""
        # This test will pass after migration is complete
        module = pytest.importorskip("madspark.agents.genai_client")
        import inspect
        source = inspect.getsource(module)

        # Count occurrences of hardcoded model name (should be minimal after migration)
        # Note: We check for the current default model name. Legacy model names in
        # pricing_config.py are intentionally kept for backward compatibility.
        hardcoded_count = source.count('"gemini-3-flash-preview"') + source.count("'gemini-3-flash-preview'")

        # Should have at most 1 (in the constant definition itself)
        assert hardcoded_count <= 1, \
            f"Found {hardcoded_count} hardcoded model name references (expected <= 1)"


class TestBackwardCompatibility:
    """Test backward compatibility with workflow_constants.py."""

    def test_workflow_constants_still_importable(self):
        """Verify workflow_constants.py still works for backward compatibility."""
        # Module should still be importable with timeout constants
        from madspark.config import workflow_constants

        # Should still have the timeout constants
        assert hasattr(workflow_constants, 'IDEA_GENERATION_TIMEOUT')
        assert hasattr(workflow_constants, 'EVALUATION_TIMEOUT')

        # Verify deprecation note in docstring
        assert workflow_constants.__doc__ is not None
        assert "deprecated" in workflow_constants.__doc__.lower() or "NOTE" in workflow_constants.__doc__


class TestModuleStructure:
    """Test that the module is properly structured."""

    def test_all_config_classes_exist(self):
        """Verify all config classes are defined."""
        from madspark.config import execution_constants

        assert hasattr(execution_constants, 'MultiModalConfig')
        assert hasattr(execution_constants, 'TimeoutConfig')
        assert hasattr(execution_constants, 'ConcurrencyConfig')
        assert hasattr(execution_constants, 'RetryConfig')
        assert hasattr(execution_constants, 'LimitsConfig')
        assert hasattr(execution_constants, 'ThresholdConfig')
        assert hasattr(execution_constants, 'TemperatureConfig')
        assert hasattr(execution_constants, 'ContentSafetyConfig')

    def test_config_classes_are_classes(self):
        """Verify config classes are actually classes (not instances)."""
        from madspark.config import execution_constants
        import inspect

        assert inspect.isclass(execution_constants.MultiModalConfig)
        assert inspect.isclass(execution_constants.TimeoutConfig)
        assert inspect.isclass(execution_constants.ConcurrencyConfig)
        assert inspect.isclass(execution_constants.RetryConfig)
        assert inspect.isclass(execution_constants.LimitsConfig)
        assert inspect.isclass(execution_constants.ThresholdConfig)
        assert inspect.isclass(execution_constants.TemperatureConfig)
        assert inspect.isclass(execution_constants.ContentSafetyConfig)
