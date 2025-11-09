# MadSpark Configuration Guide

This guide explains how to configure and customize MadSpark's behavior through centralized configuration constants.

## Overview

All configuration is centralized in `src/madspark/config/execution_constants.py`, providing a single source of truth for:
- Timeout values
- Thread pool sizes
- Retry behavior
- File size limits
- Similarity thresholds
- Temperature settings
- Content safety levels

## Configuration Classes

### MultiModalConfig

Controls file size limits and supported formats for multi-modal inputs.

```python
from madspark.config.execution_constants import MultiModalConfig

# File size limits (bytes)
MultiModalConfig.MAX_FILE_SIZE = 20_000_000      # 20MB total file size
MultiModalConfig.MAX_IMAGE_SIZE = 8_000_000      # 8MB for images
MultiModalConfig.MAX_PDF_SIZE = 40_000_000       # 40MB for PDFs

# Supported formats
MultiModalConfig.SUPPORTED_IMAGE_FORMATS  # {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
MultiModalConfig.SUPPORTED_DOC_FORMATS    # {'pdf', 'txt', 'md', 'doc', 'docx'}

# Processing limits
MultiModalConfig.MAX_PDF_PAGES = 100             # Maximum PDF pages
MultiModalConfig.IMAGE_MAX_DIMENSION = 4096      # Max image dimension
MultiModalConfig.MAX_URL_CONTENT_LENGTH = 5_000_000  # 5MB URL content
```

**Use Cases:**
- Adjust limits based on available memory
- Restrict file types for security
- Control processing load

### TimeoutConfig

Defines timeout values for all workflow operations.

```python
from madspark.config.execution_constants import TimeoutConfig

# General timeouts (seconds)
TimeoutConfig.DEFAULT_REQUEST_TIMEOUT = 1200.0   # 20 minutes
TimeoutConfig.SHORT_TIMEOUT = 30.0
TimeoutConfig.MEDIUM_TIMEOUT = 60.0
TimeoutConfig.LONG_TIMEOUT = 120.0

# Workflow step timeouts
TimeoutConfig.IDEA_GENERATION_TIMEOUT = 60.0     # Idea generation
TimeoutConfig.EVALUATION_TIMEOUT = 60.0          # Idea evaluation
TimeoutConfig.ADVOCACY_TIMEOUT = 90.0            # Advocacy analysis
TimeoutConfig.SKEPTICISM_TIMEOUT = 90.0          # Skeptical analysis
TimeoutConfig.IMPROVEMENT_TIMEOUT = 120.0        # Idea improvement
TimeoutConfig.REEVALUATION_TIMEOUT = 60.0        # Re-evaluation
TimeoutConfig.MULTI_DIMENSIONAL_EVAL_TIMEOUT = 120.0  # Multi-dim eval
TimeoutConfig.LOGICAL_INFERENCE_TIMEOUT = 90.0   # Logical inference

# Network timeouts
TimeoutConfig.URL_FETCH_TIMEOUT = 30.0           # URL fetching
```

**Use Cases:**
- Increase timeouts for slow networks
- Reduce timeouts for faster feedback
- Adjust per-operation timeouts for optimization

### ConcurrencyConfig

Controls parallelization and thread pool sizes.

```python
from madspark.config.execution_constants import ConcurrencyConfig

# Thread pool sizes
ConcurrencyConfig.MAX_ASYNC_WORKERS = 4          # AsyncCoordinator workers
ConcurrencyConfig.MAX_BATCH_WORKERS = 4          # Batch operation workers
ConcurrencyConfig.BATCH_COORDINATOR_WORKERS = 1  # Batch coordinator workers

# Concurrency limits
ConcurrencyConfig.MAX_CONCURRENT_CACHE_OPS = 5   # Concurrent cache operations
```

**Use Cases:**
- Increase workers for faster processing (if CPU/memory allows)
- Reduce workers to lower resource usage
- Tune for specific hardware configurations

### RetryConfig

Defines retry behavior for all agents and operations.

```python
from madspark.config.execution_constants import RetryConfig

# Default retry parameters
RetryConfig.DEFAULT_MAX_RETRIES = 3
RetryConfig.DEFAULT_INITIAL_RETRY_DELAY = 1.0    # seconds
RetryConfig.DEFAULT_BACKOFF_FACTOR = 2.0         # exponential backoff
RetryConfig.DEFAULT_MAX_RETRY_DELAY = 60.0       # max delay between retries

# Agent-specific retry configurations
RetryConfig.IDEA_GENERATOR_MAX_RETRIES = 3
RetryConfig.IDEA_GENERATOR_INITIAL_DELAY = 2.0
RetryConfig.CRITIC_MAX_RETRIES = 3
RetryConfig.CRITIC_INITIAL_DELAY = 2.0
RetryConfig.ADVOCATE_MAX_RETRIES = 2
RetryConfig.ADVOCATE_INITIAL_DELAY = 1.0
RetryConfig.SKEPTIC_MAX_RETRIES = 2
RetryConfig.SKEPTIC_INITIAL_DELAY = 1.0
RetryConfig.IMPROVEMENT_MAX_RETRIES = 3
RetryConfig.IMPROVEMENT_INITIAL_DELAY = 2.0
RetryConfig.CONTENT_SAFETY_MAX_RETRIES = 3
```

**Use Cases:**
- Increase retries for unreliable networks
- Adjust backoff for rate limit compliance
- Fine-tune per-agent reliability

### LimitsConfig

Size limits and operational constraints.

```python
from madspark.config.execution_constants import LimitsConfig

# JSON parsing limits
LimitsConfig.MAX_JSON_INPUT_SIZE = 1_000_000     # 1MB

# Cache configuration
LimitsConfig.MAX_CACHE_SIZE_MB = 100
LimitsConfig.MAX_CACHE_KEYS_CHECK = 1000
LimitsConfig.DEFAULT_CACHE_TTL = 3600            # 1 hour (seconds)

# Batch processing
LimitsConfig.CACHE_BATCH_SIZE = 10
LimitsConfig.DEFAULT_BATCH_SIZE = 5

# Candidate limits
LimitsConfig.MIN_NUM_CANDIDATES = 1
LimitsConfig.MAX_NUM_CANDIDATES = 5
LimitsConfig.DEFAULT_NUM_TOP_CANDIDATES = 3
```

**Use Cases:**
- Adjust cache size for available memory
- Control batch sizes for performance
- Set candidate limits based on use case

### ThresholdConfig

Similarity and detection thresholds.

```python
from madspark.config.execution_constants import ThresholdConfig

# Duplicate detection thresholds (0.0-1.0)
ThresholdConfig.EXACT_MATCH_THRESHOLD = 0.95
ThresholdConfig.HIGH_SIMILARITY_THRESHOLD = 0.8
ThresholdConfig.MEDIUM_SIMILARITY_THRESHOLD = 0.6

# Improvement detection
ThresholdConfig.MEANINGFUL_IMPROVEMENT_SIMILARITY_THRESHOLD = 0.9
ThresholdConfig.MEANINGFUL_IMPROVEMENT_SCORE_DELTA = 0.3

# Context search thresholds
ThresholdConfig.CONTEXT_SIMILARITY_THRESHOLD = 0.5
ThresholdConfig.RELEVANT_CONTEXT_THRESHOLD = 0.3
ThresholdConfig.LOOSE_CONTEXT_THRESHOLD = 0.2

# Score highlighting
ThresholdConfig.HIGH_SCORE_THRESHOLD = 7
```

**Use Cases:**
- Adjust duplicate detection sensitivity
- Tune improvement detection
- Control context matching strictness

### TemperatureConfig

LLM temperature values for different operations.

```python
from madspark.config.execution_constants import TemperatureConfig

# Temperature controls randomness in LLM responses:
# - 0.0 = deterministic (same output each time)
# - 0.7 = balanced creativity and consistency
# - 2.0 = maximum creativity/randomness

TemperatureConfig.DETERMINISTIC_TEMPERATURE = 0.0
TemperatureConfig.STANDARD_BASE_TEMPERATURE = 0.7
TemperatureConfig.REASONING_TEMPERATURE = 0.7
```

**Use Cases:**
- Set to 0.0 for reproducible outputs
- Increase for more creative responses
- Adjust per-operation for optimal results

### ContentSafetyConfig

Gemini API content safety settings.

```python
from madspark.config.execution_constants import ContentSafetyConfig

# Gemini safety threshold setting
# Options: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE, BLOCK_LOW_AND_ABOVE
ContentSafetyConfig.SAFETY_THRESHOLD = "BLOCK_ONLY_HIGH"
```

**Use Cases:**
- Adjust filtering aggressiveness
- Balance safety vs. functionality
- Comply with organizational policies

## Migration from Legacy Constants

MadSpark previously had constants scattered across multiple files. They've been consolidated into `execution_constants.py`.

### Deprecated Modules

- `madspark.config.workflow_constants` - Use `TimeoutConfig` instead
- Individual timeout values in source files - Use centralized config

### Backward Compatibility

Legacy imports still work but emit deprecation warnings:

```python
# Old way (deprecated)
from madspark.config.workflow_constants import IDEA_GENERATION_TIMEOUT

# New way (recommended)
from madspark.config.execution_constants import TimeoutConfig
timeout = TimeoutConfig.IDEA_GENERATION_TIMEOUT
```

## Best Practices

### 1. Import from execution_constants

Always import from the centralized module:

```python
# Good ✅
from madspark.config.execution_constants import TimeoutConfig, RetryConfig

# Avoid ❌
from madspark.config.workflow_constants import IDEA_GENERATION_TIMEOUT
```

### 2. Don't Hardcode Values

Use configuration classes instead of magic numbers:

```python
# Good ✅
timeout = TimeoutConfig.IDEA_GENERATION_TIMEOUT

# Avoid ❌
timeout = 60.0
```

### 3. Document Custom Configurations

If you modify defaults for your deployment, document why:

```python
# Increased for slow network environments
TimeoutConfig.DEFAULT_REQUEST_TIMEOUT = 1800.0  # 30 minutes instead of 20
```

### 4. Test After Changes

Always run tests after modifying configuration:

```bash
PYTHONPATH=src pytest tests/test_execution_constants.py -v
```

## Environment-Specific Configuration

For different environments (development, staging, production), you can:

### Option 1: Environment Variables

```python
import os
from madspark.config.execution_constants import TimeoutConfig

if os.getenv('ENVIRONMENT') == 'production':
    TimeoutConfig.DEFAULT_REQUEST_TIMEOUT = 1800.0
elif os.getenv('ENVIRONMENT') == 'development':
    TimeoutConfig.DEFAULT_REQUEST_TIMEOUT = 300.0
```

### Option 2: Configuration Files

```python
import json
from madspark.config.execution_constants import TimeoutConfig

with open('config.json') as f:
    config = json.load(f)
    TimeoutConfig.DEFAULT_REQUEST_TIMEOUT = config['timeout']
```

### Option 3: Class Inheritance

```python
from madspark.config.execution_constants import TimeoutConfig

class ProductionTimeoutConfig(TimeoutConfig):
    DEFAULT_REQUEST_TIMEOUT = 1800.0
    IDEA_GENERATION_TIMEOUT = 120.0
```

## Troubleshooting

### Timeouts Too Short

**Symptom:** Operations frequently time out
**Solution:** Increase relevant timeout values in `TimeoutConfig`

### High Memory Usage

**Symptom:** Out of memory errors
**Solution:**
- Reduce `ConcurrencyConfig.MAX_ASYNC_WORKERS`
- Reduce `MultiModalConfig.MAX_FILE_SIZE`
- Reduce `LimitsConfig.MAX_CACHE_SIZE_MB`

### Too Many Duplicate Detections

**Symptom:** Unique ideas marked as duplicates
**Solution:** Lower `ThresholdConfig.EXACT_MATCH_THRESHOLD`

### Not Enough Retries

**Symptom:** Transient errors cause failures
**Solution:** Increase agent-specific `MAX_RETRIES` in `RetryConfig`

## See Also

- [README.md](../README.md) - Quick configuration examples
- [execution_constants.py](../src/madspark/config/execution_constants.py) - Source code
- [test_execution_constants.py](../tests/test_execution_constants.py) - Configuration tests
