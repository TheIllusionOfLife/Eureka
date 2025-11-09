# Phase 1: Foundation - Configuration Centralization Implementation Plan

**Date**: November 10, 2025
**Effort**: 3-4 hours | **Risk**: Low | **Files Modified**: ~15-20

---

## Overview

Centralize all configuration constants into a unified module structure, with **doubled file size limits** for multi-modal support.

This is Phase 1 of the multi-modal capabilities implementation (Option A - Hybrid Approach).

---

## Implementation Steps

### Step 1: Create Unified Configuration Module (45 min)

**Create**: `src/madspark/config/execution_constants.py`

```python
"""Centralized execution configuration for MadSpark."""

# ========================================
# Multi-Modal Input Limits (DOUBLED)
# ========================================
class MultiModalConfig:
    """Multi-modal input configuration."""
    # File size limits (bytes) - DOUBLED from original
    MAX_FILE_SIZE = 20_000_000      # 20MB (was 10MB)
    MAX_IMAGE_SIZE = 8_000_000      # 8MB (was 4MB)
    MAX_PDF_SIZE = 40_000_000       # 40MB (was 20MB)

    # Format support
    SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
    SUPPORTED_DOC_FORMATS = {'pdf', 'txt', 'md', 'doc', 'docx'}

    # Processing limits
    MAX_PDF_PAGES = 100
    IMAGE_MAX_DIMENSION = 4096
    MAX_URL_CONTENT_LENGTH = 5_000_000  # 5MB

# ========================================
# API & Networking Timeouts
# ========================================
class TimeoutConfig:
    """Timeout configuration - reconciled values."""
    # General timeouts
    DEFAULT_REQUEST_TIMEOUT = 1200.0    # 20 minutes (consolidated)
    SHORT_TIMEOUT = 30.0
    MEDIUM_TIMEOUT = 60.0
    LONG_TIMEOUT = 120.0

    # Workflow step timeouts (from workflow_constants.py)
    IDEA_GENERATION_TIMEOUT = 60.0
    EVALUATION_TIMEOUT = 60.0
    ADVOCACY_TIMEOUT = 90.0
    SKEPTICISM_TIMEOUT = 90.0
    IMPROVEMENT_TIMEOUT = 120.0
    REEVALUATION_TIMEOUT = 60.0
    MULTI_DIMENSIONAL_EVAL_TIMEOUT = 120.0
    LOGICAL_INFERENCE_TIMEOUT = 90.0

    # URL fetch timeout (new for multi-modal)
    URL_FETCH_TIMEOUT = 30.0

# ========================================
# Concurrency & Threading
# ========================================
class ConcurrencyConfig:
    """Thread pool and concurrency configuration."""
    MAX_ASYNC_WORKERS = 4
    MAX_BATCH_WORKERS = 4
    BATCH_COORDINATOR_WORKERS = 1
    MAX_CONCURRENT_CACHE_OPS = 5

# ========================================
# Retry Configuration
# ========================================
class RetryConfig:
    """Retry and backoff configuration."""
    # Default retry parameters
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_RETRY_DELAY = 1.0
    DEFAULT_BACKOFF_FACTOR = 2.0
    DEFAULT_MAX_RETRY_DELAY = 60.0

    # Agent-specific retries
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
    """Size and limit configuration."""
    MAX_JSON_INPUT_SIZE = 1_000_000     # 1MB
    MAX_CACHE_SIZE_MB = 100
    MAX_CACHE_KEYS_CHECK = 1000
    DEFAULT_CACHE_TTL = 3600            # 1 hour
    CACHE_BATCH_SIZE = 10
    DEFAULT_BATCH_SIZE = 5

    # Candidate limits
    MIN_NUM_CANDIDATES = 1
    MAX_NUM_CANDIDATES = 5
    DEFAULT_NUM_TOP_CANDIDATES = 3

# ========================================
# Threshold Configuration
# ========================================
class ThresholdConfig:
    """Similarity and threshold configuration."""
    # Duplicate detection
    EXACT_MATCH_THRESHOLD = 0.95
    HIGH_SIMILARITY_THRESHOLD = 0.8
    MEDIUM_SIMILARITY_THRESHOLD = 0.6

    # Improvement detection
    MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD = 0.9
    MEANINGFUL_IMPROVEMENT_SCORE_DELTA = 0.3

    # Context search
    CONTEXT_SIMILARITY_THRESHOLD = 0.5
    RELEVANT_CONTEXT_THRESHOLD = 0.3
    LOOSE_CONTEXT_THRESHOLD = 0.2

    # Score highlighting
    HIGH_SCORE_THRESHOLD = 7

# ========================================
# Temperature Configuration
# ========================================
class TemperatureConfig:
    """Temperature configuration for different operations."""
    DETERMINISTIC_TEMPERATURE = 0.0
    STANDARD_BASE_TEMPERATURE = 0.7
    REASONING_TEMPERATURE = 0.7

# ========================================
# Content Safety Configuration
# ========================================
class ContentSafetyConfig:
    """Content safety configuration."""
    SAFETY_THRESHOLD = "BLOCK_ONLY_HIGH"
```

---

### Step 2: Fix Critical Issues (30 min)

#### 2.1: Remove Duplicate Constant in `src/madspark/utils/constants.py`
- **Line 185**: Remove duplicate `DEFAULT_NOVELTY_THRESHOLD = 0.8` (keep line 23)

#### 2.2: Deprecate `workflow_constants.py`
- Add deprecation notice at top of file
- Import from `execution_constants.py` for backward compatibility

```python
# At top of src/madspark/config/workflow_constants.py
import warnings
from .execution_constants import TimeoutConfig

warnings.warn(
    "workflow_constants.py is deprecated. Use execution_constants.py instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
IDEA_GENERATION_TIMEOUT = TimeoutConfig.IDEA_GENERATION_TIMEOUT
EVALUATION_TIMEOUT = TimeoutConfig.EVALUATION_TIMEOUT
# ... etc
```

---

### Step 3: Migrate AsyncCoordinator Timeouts (45 min)

**File**: `src/madspark/core/async_coordinator.py`

**Add import**:
```python
from ..config.execution_constants import TimeoutConfig
```

**Replace hardcoded timeouts** (8 locations):
- Line 816: `timeout=60.0` → `timeout=TimeoutConfig.IDEA_GENERATION_TIMEOUT`
- Line 856: `timeout=30.0` → `timeout=TimeoutConfig.EVALUATION_TIMEOUT`
- Line 872: `timeout=45.0` → `timeout=TimeoutConfig.MULTI_DIMENSIONAL_EVAL_TIMEOUT`
- Line 1137: `timeout=30.0` → `timeout=TimeoutConfig.ADVOCACY_TIMEOUT`
- Line 1153: `timeout=30.0` → `timeout=TimeoutConfig.SKEPTICISM_TIMEOUT`
- Line 1240: `timeout=45.0` → `timeout=TimeoutConfig.IMPROVEMENT_TIMEOUT`
- Line 1282: `timeout=30.0` → `timeout=TimeoutConfig.REEVALUATION_TIMEOUT`
- Line 1294: `timeout=30.0` → `timeout=TimeoutConfig.MULTI_DIMENSIONAL_EVAL_TIMEOUT`

**Note**: These will now use the longer timeouts from TimeoutConfig (60-120s instead of 30-60s), which should reduce premature timeout errors.

---

### Step 4: Migrate Thread Pool Configurations (20 min)

**Add import to each file**:
```python
from ..config.execution_constants import ConcurrencyConfig
```

**Files to update**:

1. **`src/madspark/core/async_coordinator.py:46`**
   ```python
   # Before
   self.executor = ThreadPoolExecutor(max_workers=4)

   # After
   self.executor = ThreadPoolExecutor(max_workers=ConcurrencyConfig.MAX_ASYNC_WORKERS)
   ```

2. **`src/madspark/core/batch_operations_base.py:37`**
   ```python
   # Before
   self.executor = ThreadPoolExecutor(max_workers=4)

   # After
   self.executor = ThreadPoolExecutor(max_workers=ConcurrencyConfig.MAX_BATCH_WORKERS)
   ```

3. **`src/madspark/core/coordinator_batch.py:88`**
   ```python
   # Before
   self.executor = ThreadPoolExecutor(max_workers=1)

   # After
   self.executor = ThreadPoolExecutor(max_workers=ConcurrencyConfig.BATCH_COORDINATOR_WORKERS)
   ```

---

### Step 5: Migrate Retry Configurations (30 min)

**File**: `src/madspark/utils/agent_retry_wrappers.py`

**Add import**:
```python
from ..config.execution_constants import RetryConfig
```

**Update decorator calls** (5 functions):

```python
# Line 23 - idea_generator
@exponential_backoff_retry(
    max_retries=RetryConfig.IDEA_GENERATOR_MAX_RETRIES,
    initial_delay=RetryConfig.IDEA_GENERATOR_INITIAL_DELAY
)

# Line 29 - critic
@exponential_backoff_retry(
    max_retries=RetryConfig.CRITIC_MAX_RETRIES,
    initial_delay=RetryConfig.CRITIC_INITIAL_DELAY
)

# Line 35 - advocate
@exponential_backoff_retry(
    max_retries=RetryConfig.ADVOCATE_MAX_RETRIES,
    initial_delay=RetryConfig.ADVOCATE_INITIAL_DELAY
)

# Line 41 - skeptic
@exponential_backoff_retry(
    max_retries=RetryConfig.SKEPTIC_MAX_RETRIES,
    initial_delay=RetryConfig.SKEPTIC_INITIAL_DELAY
)

# Line 47 - improve_idea_agent
@exponential_backoff_retry(
    max_retries=RetryConfig.IMPROVEMENT_MAX_RETRIES,
    initial_delay=RetryConfig.IMPROVEMENT_INITIAL_DELAY
)
```

---

### Step 6: Migrate Model Name References (15 min)

**Files to update** (6 locations):

1. **`src/madspark/agents/genai_client.py:66`**
   ```python
   from ..utils.constants import DEFAULT_GOOGLE_GENAI_MODEL
   # Change "gemini-2.5-flash" to DEFAULT_GOOGLE_GENAI_MODEL
   ```

2. **`src/madspark/core/coordinator.py:74`**
   ```python
   from ..utils.constants import DEFAULT_GOOGLE_GENAI_MODEL
   # Change "gemini-2.5-flash" to DEFAULT_GOOGLE_GENAI_MODEL
   ```

3. **`src/madspark/agents/structured_idea_generator.py:51, 160`**
   ```python
   from ..utils.constants import DEFAULT_GOOGLE_GENAI_MODEL
   # Change both occurrences
   ```

4. **`bin/mad_spark_config:44, 105, 184`**
   ```python
   # Import from constants module
   # Change all 3 occurrences
   ```

---

### Step 7: Migrate Threshold Configurations (20 min)

**Files to update**:

1. **`src/madspark/utils/duplicate_detector.py:168-170`**
   ```python
   from ..config.execution_constants import ThresholdConfig

   # Line 168
   if similarity >= ThresholdConfig.EXACT_MATCH_THRESHOLD:
   # Line 169
   elif similarity >= ThresholdConfig.HIGH_SIMILARITY_THRESHOLD:
   # Line 170
   elif similarity >= ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD:
   ```

2. **`src/madspark/core/enhanced_reasoning.py:161, 1394, 1556`**
   ```python
   from ..config.execution_constants import ThresholdConfig

   # Line 161
   threshold=ThresholdConfig.CONTEXT_SIMILARITY_THRESHOLD
   # Line 1394
   threshold=ThresholdConfig.RELEVANT_CONTEXT_THRESHOLD
   # Line 1556
   threshold=ThresholdConfig.LOOSE_CONTEXT_THRESHOLD
   ```

3. **`src/madspark/cli/cli.py:667`**
   ```python
   from ..config.execution_constants import LimitsConfig

   # Line 667
   min(max(args.num_candidates, LimitsConfig.MIN_NUM_CANDIDATES), LimitsConfig.MAX_NUM_CANDIDATES)
   ```

---

### Step 8: Migrate Content Safety Threshold (10 min)

**Add import**:
```python
from ..config.execution_constants import ContentSafetyConfig
```

**Files to update**:

1. **`src/madspark/agents/idea_generator.py:47, 51, 55, 59`**
   ```python
   # All 4 locations
   threshold=ContentSafetyConfig.SAFETY_THRESHOLD
   ```

2. **`src/madspark/agents/content_safety.py:118, 122, 126, 130`**
   ```python
   # All 4 locations
   threshold=ContentSafetyConfig.SAFETY_THRESHOLD
   ```

---

### Step 9: Migrate Temperature Values (15 min)

**Add import**:
```python
from ..config.execution_constants import TemperatureConfig
```

**Files to update**:

1. **`src/madspark/core/enhanced_reasoning.py:793`**
   ```python
   temperature=TemperatureConfig.DETERMINISTIC_TEMPERATURE
   ```

2. **`src/madspark/core/async_coordinator.py:753`**
   ```python
   TemperatureConfig.STANDARD_BASE_TEMPERATURE
   ```

3. **`src/madspark/utils/logical_inference_engine.py:142, 230`**
   ```python
   # Both locations
   temperature=TemperatureConfig.REASONING_TEMPERATURE
   ```

---

### Step 10: Add Tests (30 min)

**Create**: `tests/test_execution_constants.py`

```python
"""Tests for centralized execution constants."""
import pytest
from madspark.config.execution_constants import (
    MultiModalConfig, TimeoutConfig, ConcurrencyConfig,
    RetryConfig, LimitsConfig, ThresholdConfig,
    TemperatureConfig, ContentSafetyConfig
)

class TestMultiModalConfig:
    """Test multi-modal configuration."""

    def test_file_size_limits_doubled(self):
        """Verify file sizes are doubled from original proposal."""
        assert MultiModalConfig.MAX_FILE_SIZE == 20_000_000  # 20MB
        assert MultiModalConfig.MAX_IMAGE_SIZE == 8_000_000  # 8MB
        assert MultiModalConfig.MAX_PDF_SIZE == 40_000_000   # 40MB

    def test_supported_image_formats(self):
        """Verify supported image format set."""
        assert 'png' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'jpg' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'jpeg' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert 'webp' in MultiModalConfig.SUPPORTED_IMAGE_FORMATS
        assert len(MultiModalConfig.SUPPORTED_IMAGE_FORMATS) >= 5

    def test_supported_doc_formats(self):
        """Verify supported document format set."""
        assert 'pdf' in MultiModalConfig.SUPPORTED_DOC_FORMATS
        assert 'txt' in MultiModalConfig.SUPPORTED_DOC_FORMATS
        assert 'md' in MultiModalConfig.SUPPORTED_DOC_FORMATS

class TestTimeoutConfig:
    """Test timeout configuration."""

    def test_workflow_timeouts_defined(self):
        """Verify all workflow step timeouts exist and are positive."""
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
        assert TimeoutConfig.SHORT_TIMEOUT < TimeoutConfig.MEDIUM_TIMEOUT
        assert TimeoutConfig.MEDIUM_TIMEOUT < TimeoutConfig.LONG_TIMEOUT
        assert TimeoutConfig.LONG_TIMEOUT < TimeoutConfig.DEFAULT_REQUEST_TIMEOUT

class TestConcurrencyConfig:
    """Test concurrency configuration."""

    def test_worker_counts(self):
        """Verify all worker counts are positive."""
        assert ConcurrencyConfig.MAX_ASYNC_WORKERS > 0
        assert ConcurrencyConfig.MAX_BATCH_WORKERS > 0
        assert ConcurrencyConfig.BATCH_COORDINATOR_WORKERS > 0
        assert ConcurrencyConfig.MAX_CONCURRENT_CACHE_OPS > 0

class TestRetryConfig:
    """Test retry configuration."""

    def test_default_retry_params(self):
        """Verify default retry parameters are sensible."""
        assert RetryConfig.DEFAULT_MAX_RETRIES >= 1
        assert RetryConfig.DEFAULT_INITIAL_RETRY_DELAY > 0
        assert RetryConfig.DEFAULT_BACKOFF_FACTOR >= 1.0
        assert RetryConfig.DEFAULT_MAX_RETRY_DELAY > RetryConfig.DEFAULT_INITIAL_RETRY_DELAY

    def test_agent_retry_configs(self):
        """Verify all agents have retry configs."""
        assert RetryConfig.IDEA_GENERATOR_MAX_RETRIES > 0
        assert RetryConfig.CRITIC_MAX_RETRIES > 0
        assert RetryConfig.ADVOCATE_MAX_RETRIES > 0
        assert RetryConfig.SKEPTIC_MAX_RETRIES > 0
        assert RetryConfig.IMPROVEMENT_MAX_RETRIES > 0

class TestLimitsConfig:
    """Test limits configuration."""

    def test_size_limits(self):
        """Verify size limits are positive."""
        assert LimitsConfig.MAX_JSON_INPUT_SIZE > 0
        assert LimitsConfig.MAX_CACHE_SIZE_MB > 0
        assert LimitsConfig.MAX_CACHE_KEYS_CHECK > 0

    def test_candidate_limits(self):
        """Verify candidate limits are logical."""
        assert LimitsConfig.MIN_NUM_CANDIDATES >= 1
        assert LimitsConfig.MAX_NUM_CANDIDATES >= LimitsConfig.MIN_NUM_CANDIDATES
        assert LimitsConfig.DEFAULT_NUM_TOP_CANDIDATES >= LimitsConfig.MIN_NUM_CANDIDATES
        assert LimitsConfig.DEFAULT_NUM_TOP_CANDIDATES <= LimitsConfig.MAX_NUM_CANDIDATES

class TestThresholdConfig:
    """Test threshold configuration."""

    def test_similarity_thresholds(self):
        """Verify similarity thresholds are in valid range."""
        assert 0.0 <= ThresholdConfig.EXACT_MATCH_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.HIGH_SIMILARITY_THRESHOLD <= 1.0
        assert 0.0 <= ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD <= 1.0

        # Should be ordered
        assert ThresholdConfig.EXACT_MATCH_THRESHOLD >= ThresholdConfig.HIGH_SIMILARITY_THRESHOLD
        assert ThresholdConfig.HIGH_SIMILARITY_THRESHOLD >= ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD

class TestTemperatureConfig:
    """Test temperature configuration."""

    def test_temperature_ranges(self):
        """Verify temperature values are in valid range."""
        assert 0.0 <= TemperatureConfig.DETERMINISTIC_TEMPERATURE <= 2.0
        assert 0.0 <= TemperatureConfig.STANDARD_BASE_TEMPERATURE <= 2.0
        assert 0.0 <= TemperatureConfig.REASONING_TEMPERATURE <= 2.0

class TestContentSafetyConfig:
    """Test content safety configuration."""

    def test_safety_threshold_value(self):
        """Verify safety threshold is a valid Gemini setting."""
        assert ContentSafetyConfig.SAFETY_THRESHOLD in [
            "BLOCK_NONE", "BLOCK_ONLY_HIGH",
            "BLOCK_MEDIUM_AND_ABOVE", "BLOCK_LOW_AND_ABOVE"
        ]

class TestConstantUsage:
    """Test that constants are actually used in codebase."""

    def test_no_hardcoded_timeouts_in_async_coordinator(self):
        """Verify AsyncCoordinator uses config constants."""
        import madspark.core.async_coordinator as module
        import inspect
        source = inspect.getsource(module)

        # Should not contain hardcoded timeout values
        # (Allow timeout= in function signatures, but not literals)
        import re
        # Look for timeout=<number> pattern
        hardcoded_timeouts = re.findall(r'timeout=\d+\.?\d*(?!\w)', source)
        # Filter out timeout=0 which might be used for "no timeout"
        hardcoded_timeouts = [t for t in hardcoded_timeouts if not t.startswith('timeout=0')]

        assert len(hardcoded_timeouts) == 0, \
            f"Found hardcoded timeouts in async_coordinator: {hardcoded_timeouts}"

    def test_no_hardcoded_max_workers(self):
        """Verify thread pools use config constants."""
        import madspark.core.batch_operations_base as module
        import inspect
        source = inspect.getsource(module)

        # Should not contain max_workers=4
        assert 'max_workers=4' not in source, \
            "Found hardcoded max_workers=4 in batch_operations_base"
```

---

### Step 11: Update Documentation (15 min)

#### Update README.md

Add configuration section after "Quick Start":

```markdown
## Configuration

MadSpark uses centralized configuration for all execution parameters. Configuration is managed through:

- **Environment Variables**: `.env` file for API keys and model selection
- **Execution Constants**: `src/madspark/config/execution_constants.py` for all timeout, limit, and threshold values

### Key Configuration Classes

- **`MultiModalConfig`**: File size limits, supported formats (20MB files, 8MB images, 40MB PDFs)
- **`TimeoutConfig`**: Workflow step timeouts (60-120 seconds)
- **`ConcurrencyConfig`**: Thread pool sizes and concurrency limits
- **`RetryConfig`**: Retry attempts and backoff parameters
- **`ThresholdConfig`**: Similarity and detection thresholds

See `src/madspark/config/execution_constants.py` for complete configuration options.
```

#### Create CONFIGURATION_GUIDE.md

**Create**: `docs/CONFIGURATION_GUIDE.md`

```markdown
# MadSpark Configuration Guide

## Overview

MadSpark's configuration is centralized in `src/madspark/config/execution_constants.py` for easy customization and maintenance.

## Configuration Classes

### MultiModalConfig

Controls multi-modal input handling (URLs, PDFs, images).

```python
MAX_FILE_SIZE = 20_000_000      # 20MB maximum file size
MAX_IMAGE_SIZE = 8_000_000      # 8MB maximum image size
MAX_PDF_SIZE = 40_000_000       # 40MB maximum PDF size
```

**Supported Formats**:
- Images: PNG, JPG, JPEG, WebP, GIF, BMP
- Documents: PDF, TXT, MD, DOC, DOCX

### TimeoutConfig

Controls workflow execution timeouts.

```python
IDEA_GENERATION_TIMEOUT = 60.0      # Idea generation (seconds)
EVALUATION_TIMEOUT = 60.0           # Idea evaluation
ADVOCACY_TIMEOUT = 90.0             # Advocacy analysis
SKEPTICISM_TIMEOUT = 90.0           # Skepticism analysis
IMPROVEMENT_TIMEOUT = 120.0         # Idea improvement
REEVALUATION_TIMEOUT = 60.0         # Re-evaluation
```

**Customization**: Increase timeouts for complex queries or slow networks.

### ConcurrencyConfig

Controls thread pool sizes and parallel execution.

```python
MAX_ASYNC_WORKERS = 4              # Async coordinator threads
MAX_BATCH_WORKERS = 4              # Batch operation threads
BATCH_COORDINATOR_WORKERS = 1      # Batch coordinator threads
```

### RetryConfig

Controls retry behavior for failed API calls.

```python
DEFAULT_MAX_RETRIES = 3            # Maximum retry attempts
DEFAULT_INITIAL_RETRY_DELAY = 1.0  # Initial delay (seconds)
DEFAULT_BACKOFF_FACTOR = 2.0       # Exponential backoff multiplier
```

**Agent-Specific Retries**: Different agents have different retry configurations based on their criticality.

### ThresholdConfig

Controls similarity detection and matching.

```python
EXACT_MATCH_THRESHOLD = 0.95       # Nearly identical content
HIGH_SIMILARITY_THRESHOLD = 0.8    # High similarity (default duplicate detection)
MEDIUM_SIMILARITY_THRESHOLD = 0.6  # Moderate similarity
```

## Customization

To customize configuration:

1. Edit `src/madspark/config/execution_constants.py`
2. Modify the desired class attribute
3. Restart MadSpark for changes to take effect

**Example**: Increase file size limits for large documents:

```python
class MultiModalConfig:
    MAX_FILE_SIZE = 50_000_000      # Increase to 50MB
    MAX_PDF_SIZE = 100_000_000      # Increase to 100MB
```

## Best Practices

- **Timeouts**: Increase for complex queries, decrease for faster feedback
- **File Sizes**: Balance between capability and memory usage
- **Retries**: Higher retries for production, lower for development
- **Thresholds**: Adjust based on desired duplicate sensitivity

## Troubleshooting

**Timeout Errors**: Increase relevant timeout in `TimeoutConfig`
**File Too Large Errors**: Increase limits in `MultiModalConfig`
**Duplicate Detection Too Sensitive**: Lower `HIGH_SIMILARITY_THRESHOLD`
```

#### Update session_handover.md

Add to "Recently Completed" section:

```markdown
- ✅ **Phase 1: Configuration Centralization** (November 10, 2025)
  - Created unified execution_constants.py module
  - Centralized all timeouts, limits, thresholds
  - Doubled file size limits for multi-modal (20MB files, 8MB images, 40MB PDFs)
  - Migrated 40+ hardcoded constants across 15 files
  - Added comprehensive test coverage
  - Ready for Phase 2 multi-modal implementation
```

---

## Migration Checklist

### Core Implementation
- [ ] Create `src/madspark/config/execution_constants.py` with all config classes
- [ ] Remove duplicate `DEFAULT_NOVELTY_THRESHOLD` in `src/madspark/utils/constants.py:185`
- [ ] Add deprecation warning to `src/madspark/config/workflow_constants.py`

### Timeout Migration (8 locations)
- [ ] `src/madspark/core/async_coordinator.py:816` - IDEA_GENERATION_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:856` - EVALUATION_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:872` - MULTI_DIMENSIONAL_EVAL_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:1137` - ADVOCACY_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:1153` - SKEPTICISM_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:1240` - IMPROVEMENT_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:1282` - REEVALUATION_TIMEOUT
- [ ] `src/madspark/core/async_coordinator.py:1294` - MULTI_DIMENSIONAL_EVAL_TIMEOUT

### Thread Pool Migration (3 locations)
- [ ] `src/madspark/core/async_coordinator.py:46` - MAX_ASYNC_WORKERS
- [ ] `src/madspark/core/batch_operations_base.py:37` - MAX_BATCH_WORKERS
- [ ] `src/madspark/core/coordinator_batch.py:88` - BATCH_COORDINATOR_WORKERS

### Retry Migration (5 locations)
- [ ] `src/madspark/utils/agent_retry_wrappers.py:23` - idea_generator
- [ ] `src/madspark/utils/agent_retry_wrappers.py:29` - critic
- [ ] `src/madspark/utils/agent_retry_wrappers.py:35` - advocate
- [ ] `src/madspark/utils/agent_retry_wrappers.py:41` - skeptic
- [ ] `src/madspark/utils/agent_retry_wrappers.py:47` - improve_idea_agent

### Model Name Migration (6 locations)
- [ ] `src/madspark/agents/genai_client.py:66`
- [ ] `src/madspark/core/coordinator.py:74`
- [ ] `src/madspark/agents/structured_idea_generator.py:51`
- [ ] `src/madspark/agents/structured_idea_generator.py:160`
- [ ] `bin/mad_spark_config:44`
- [ ] `bin/mad_spark_config:105`
- [ ] `bin/mad_spark_config:184`

### Threshold Migration (5 locations)
- [ ] `src/madspark/utils/duplicate_detector.py:168-170` (3 thresholds)
- [ ] `src/madspark/core/enhanced_reasoning.py:161`
- [ ] `src/madspark/core/enhanced_reasoning.py:1394`
- [ ] `src/madspark/core/enhanced_reasoning.py:1556`
- [ ] `src/madspark/cli/cli.py:667` (min/max candidates)

### Content Safety Migration (8 locations)
- [ ] `src/madspark/agents/idea_generator.py:47`
- [ ] `src/madspark/agents/idea_generator.py:51`
- [ ] `src/madspark/agents/idea_generator.py:55`
- [ ] `src/madspark/agents/idea_generator.py:59`
- [ ] `src/madspark/agents/content_safety.py:118`
- [ ] `src/madspark/agents/content_safety.py:122`
- [ ] `src/madspark/agents/content_safety.py:126`
- [ ] `src/madspark/agents/content_safety.py:130`

### Temperature Migration (4 locations)
- [ ] `src/madspark/core/enhanced_reasoning.py:793`
- [ ] `src/madspark/core/async_coordinator.py:753`
- [ ] `src/madspark/utils/logical_inference_engine.py:142`
- [ ] `src/madspark/utils/logical_inference_engine.py:230`

### Testing & Documentation
- [ ] Create `tests/test_execution_constants.py` with comprehensive tests
- [ ] Update `README.md` with configuration section
- [ ] Create `docs/CONFIGURATION_GUIDE.md`
- [ ] Update `session_handover.md` with Phase 1 completion

### Verification
- [ ] Run full test suite: `PYTHONPATH=src pytest tests/ -v`
- [ ] Verify no hardcoded constants remain: `grep -r "timeout=30.0\|timeout=45.0\|max_workers=4" src/madspark/core/`
- [ ] Type checking passes: `mypy src/madspark/config/ --ignore-missing-imports`
- [ ] All existing tests still pass

---

## Testing Strategy

### Before Migration
```bash
# Baseline - all tests should pass
PYTHONPATH=src pytest tests/ -v --cov=src
```

### During Migration (After Each Step)
```bash
# Test new constants module
PYTHONPATH=src pytest tests/test_execution_constants.py -v

# Test affected module
PYTHONPATH=src pytest tests/test_async_coordinator.py -v  # After Step 3
PYTHONPATH=src pytest tests/test_batch_operations.py -v   # After Step 4
# ... etc for each step
```

### Final Verification
```bash
# All tests pass
PYTHONPATH=src pytest tests/ -v

# Coverage maintained
PYTHONPATH=src pytest tests/ --cov=src --cov-report=term-missing

# No hardcoded values remain
grep -r "timeout=30.0" src/madspark/core/
grep -r "timeout=45.0" src/madspark/core/
grep -r "max_workers=4" src/madspark/core/
grep -r '"BLOCK_ONLY_HIGH"' src/madspark/agents/
grep -r '"gemini-2.5-flash"' src/madspark/ --exclude-dir=__pycache__

# Type checking passes
mypy src/madspark/config/ --ignore-missing-imports
```

---

## Commit Strategy

Use conventional commit format with TDD approach:

```bash
# Step 1: Create config module
git add src/madspark/config/execution_constants.py
git commit -m "feat: create centralized execution constants module

- Add MultiModalConfig with doubled file size limits (20MB/8MB/40MB)
- Add TimeoutConfig with reconciled workflow timeouts
- Add ConcurrencyConfig for thread pool management
- Add RetryConfig for agent retry parameters
- Add LimitsConfig for size and candidate limits
- Add ThresholdConfig for similarity detection
- Add TemperatureConfig for operation temperatures
- Add ContentSafetyConfig for safety thresholds

Prepares foundation for Phase 2 multi-modal implementation."

# Step 2: Fix critical issues
git add src/madspark/utils/constants.py src/madspark/config/workflow_constants.py
git commit -m "fix: remove duplicate constant and deprecate workflow_constants

- Remove duplicate DEFAULT_NOVELTY_THRESHOLD in constants.py:185
- Add deprecation warning to workflow_constants.py
- Re-export from execution_constants for backward compatibility"

# Step 3-9: Migrate in batches
git add src/madspark/core/async_coordinator.py
git commit -m "refactor: migrate async_coordinator to use TimeoutConfig

- Replace 8 hardcoded timeout values with TimeoutConfig constants
- Increases timeout values to workflow_constants defaults (30-60s → 60-120s)
- Reduces premature timeout errors in async workflows"

git add src/madspark/core/batch_operations_base.py src/madspark/core/coordinator_batch.py
git commit -m "refactor: migrate thread pool configs to ConcurrencyConfig

- Replace hardcoded max_workers with ConcurrencyConfig constants
- Improves configurability of parallel execution"

# ... continue for each migration step

# Step 10-11: Tests and docs
git add tests/test_execution_constants.py
git commit -m "test: add comprehensive tests for execution constants

- 20+ test cases covering all config classes
- Verify no hardcoded constants remain in codebase
- Validate configuration value relationships"

git add README.md docs/CONFIGURATION_GUIDE.md session_handover.md
git commit -m "docs: add configuration documentation and update session handover

- Add configuration section to README
- Create comprehensive CONFIGURATION_GUIDE.md
- Mark Phase 1 complete in session_handover.md"
```

---

## Expected Outcomes

### Configuration Benefits
✅ **Single Source of Truth**: All configuration in one module
✅ **Easy Customization**: Change values in one place
✅ **Type Safety**: Class-based configuration with clear structure
✅ **Documentation**: Self-documenting through class and constant names
✅ **Multi-Modal Ready**: File size limits defined for Phase 2

### Code Quality Improvements
✅ **No Magic Numbers**: All hardcoded values replaced with named constants
✅ **Consistent Timeouts**: Reconciled AsyncCoordinator with workflow_constants
✅ **Maintainability**: Easy to find and update configuration
✅ **Testability**: Configuration can be tested independently

### Preparation for Phase 2
✅ **Multi-Modal Limits Defined**: File sizes, formats, processing limits
✅ **Timeout Infrastructure**: URL fetch timeout ready for web scraping
✅ **Clean Foundation**: No technical debt blocking multi-modal implementation

---

## Time Breakdown

| Step | Task | Estimated Time |
|------|------|----------------|
| 1 | Create execution_constants.py | 45 min |
| 2 | Fix critical issues | 30 min |
| 3 | Migrate AsyncCoordinator timeouts | 45 min |
| 4 | Migrate thread pool configs | 20 min |
| 5 | Migrate retry configs | 30 min |
| 6 | Migrate model name references | 15 min |
| 7 | Migrate threshold configs | 20 min |
| 8 | Migrate content safety threshold | 10 min |
| 9 | Migrate temperature values | 15 min |
| 10 | Add comprehensive tests | 30 min |
| 11 | Update documentation | 15 min |
| **Total** | | **3 hours 35 min** |

**Buffer**: +25 min for debugging/testing = **~4 hours total**

---

## Next Steps (After Phase 1)

Once Phase 1 is complete and all tests pass:

1. **Create PR**: Push branch and create pull request
2. **Review & Merge**: Address any reviewer feedback
3. **Start Phase 2**: Begin multi-modal implementation (12-16 hours)
   - Create MultiModalInput module
   - Add CLI flags (--url, --file, --image)
   - Update agents for multi-modal context
   - Web API file upload endpoints
   - Frontend file upload UI

---

## Document Metadata

**Created**: November 10, 2025 02:00 AM JST
**Type**: Implementation Plan
**Phase**: Phase 1 - Foundation
**Next Phase**: Phase 2 - Multi-Modal Implementation
**Status**: Ready for execution
