# Ollama Multi-LLM Provider Migration Plan

**Project**: MadSpark Multi-Agent System
**Goal**: Add Ollama (gemma3) support as primary LLM provider with Gemini fallback
**Created**: 2025-11-16
**Estimated Duration**: 2-3 days (20-25 hours total)

---

## Executive Summary

This plan migrates MadSpark from Gemini-only to a multi-provider architecture where:
- **Ollama (gemma3)** is the primary provider (free, local inference)
- **Gemini** serves as fallback and handles PDFs/URLs (paid cloud API)
- **Pydantic schemas** serve as the single source of truth for both providers
- **Response caching** reduces redundant LLM calls by 50%+

### Key Benefits
- **Cost Reduction**: $0 for most operations vs ~$0.001/request
- **No API Dependency**: Local inference, no rate limits or quotas
- **Privacy**: Data stays on local machine
- **Testing**: Real LLM tests without mocks (Ollama replaces mock mode)

### Performance Expectations (M2 Pro Mac mini, 32GB)

| Model | Use Case | Avg Latency | Quality |
|-------|----------|-------------|---------|
| gemma3:4b-it-qat | Fast iteration | 3-8 sec/request | Good |
| gemma3:12b-it-qat | Production quality | 25-90 sec/request | Excellent |
| gemini-2.5-flash | Best quality | 0.5-1.5 sec/request | Best |

**Expected Workflow Times** (5 ideas, 3 evaluations):
- Fast mode (4B): ~2-3 minutes
- Quality mode (12B): ~5-8 minutes
- Gemini mode: ~30-60 seconds

---

## Validated Technical Findings

### Test Results (November 16, 2025)

```bash
# Schema Support ✅
- Nested objects: Works with $defs references
- Arrays: Works with items schema
- Field constraints (min/max): Enforced correctly
- Pydantic validation: 100% compatible

# Image Support ✅
- Base64 image input: Supported
- Color detection: Accurate
- Latency: ~8-9 seconds with 4B model

# Performance Characteristics
- Token limits (num_predict) = 10-25x speedup
- 4B vs 12B = 3-5x speedup
- Sequential processing only (no concurrency)
```

### Critical Code Pattern

```python
# Ollama uses standard JSON Schema (Pydantic native)
schema = MyPydanticModel.model_json_schema()
response = ollama.chat(
    model='gemma3:4b-it-qat',
    messages=[...],
    format=schema,  # Native schema enforcement
    options={'temperature': 0, 'num_predict': 500}
)
validated = MyPydanticModel.model_validate_json(response.message.content)

# Gemini uses custom schema format
from madspark.schemas.adapters import pydantic_to_genai_schema
genai_schema = pydantic_to_genai_schema(MyPydanticModel)
```

---

## Phase 0: Prerequisites (~15 minutes)

### 0.1 Add Dependencies

**File**: `pyproject.toml`

```toml
[project]
dependencies = [
    # ... existing deps ...
    "ollama>=0.6.0",
    "diskcache>=5.6.0",  # For response caching
]
```

**Commands**:
```bash
uv pip install ollama diskcache
uv pip freeze > requirements.lock
```

### 0.2 Update .env Template

**File**: `.env.example`

```bash
# LLM Provider Configuration
MADSPARK_LLM_PROVIDER=auto          # auto, ollama, gemini
MADSPARK_MODEL_TIER=fast            # fast (4B), balanced (12B), quality (gemini)
MADSPARK_FALLBACK_ENABLED=true      # Enable Ollama → Gemini fallback

# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FAST=gemma3:4b-it-qat
OLLAMA_MODEL_BALANCED=gemma3:12b-it-qat

# Gemini Settings (existing)
GOOGLE_API_KEY=your_key_here
GOOGLE_GENAI_MODEL=gemini-2.5-flash

# Cache Settings
MADSPARK_CACHE_ENABLED=true
MADSPARK_CACHE_TTL=86400            # 24 hours in seconds
MADSPARK_CACHE_DIR=.cache/llm
```

### 0.3 Verify Ollama Installation

**Checklist**:
- [ ] Ollama installed: `brew install ollama`
- [ ] Server running: `ollama serve` (or via macOS app)
- [ ] Models pulled:
  ```bash
  ollama pull gemma3:4b-it-qat
  ollama pull gemma3:12b-it-qat
  ```
- [ ] Verify: `ollama list | grep gemma3`

---

## Phase 1: Foundation (~4 hours)

**PR Milestone**: Create PR after Phase 1 completion with package structure, base classes, and unit tests.

### 1.1 Create Package Structure

```bash
mkdir -p src/madspark/llm/providers
touch src/madspark/llm/__init__.py
touch src/madspark/llm/providers/__init__.py
```

**Files to Create**:
```
src/madspark/llm/
├── __init__.py              # Package exports
├── base.py                  # Abstract LLMProvider interface
├── response.py              # Unified LLMResponse dataclass
├── exceptions.py            # Provider-specific exceptions
├── config.py                # Configuration and model tiers
├── providers/
│   ├── __init__.py          # Provider exports
│   ├── ollama.py            # Ollama implementation
│   ├── gemini.py            # Gemini implementation
│   └── mock.py              # Mock provider for testing
└── cache.py                 # Response caching layer
```

### 1.2 Core Interfaces

**File**: `src/madspark/llm/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel

class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> "LLMResponse":
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,
        images: Optional[list[Union[str, Path]]] = None
    ) -> tuple[Any, "LLMResponse"]:
        """
        Generate structured output validated against Pydantic model.

        Returns:
            tuple: (validated_pydantic_object, response_metadata)
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier (e.g., 'ollama', 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model being used (e.g., 'gemma3:4b-it-qat')."""
        pass

    @property
    @abstractmethod
    def supports_multimodal(self) -> bool:
        """Whether provider supports images/PDFs/URLs."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify provider is available."""
        pass

    def get_cost_per_token(self) -> float:
        """Return cost per token (0 for local)."""
        return 0.0

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars = 1 token)."""
        return len(text) // 4
```

**File**: `src/madspark/llm/response.py`

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class LLMResponse:
    """Unified response metadata from any LLM provider."""

    text: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cost: float = 0.0
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "cached": self.cached,
            "timestamp": self.timestamp.isoformat()
        }
```

**File**: `src/madspark/llm/exceptions.py`

```python
class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass

class ProviderUnavailableError(LLMProviderError):
    """Provider is not available (server down, no API key, etc.)."""
    pass

class AllProvidersFailedError(LLMProviderError):
    """All providers failed after retries."""
    pass

class SchemaValidationError(LLMProviderError):
    """LLM output doesn't match expected schema."""
    pass

class RateLimitError(LLMProviderError):
    """API rate limit exceeded."""
    pass

class AuthorizationError(LLMProviderError):
    """User not authorized for this feature (future: premium)."""
    pass
```

### 1.3 Configuration Layer

**File**: `src/madspark/llm/config.py`

```python
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class ModelTier(Enum):
    """Model quality/speed tiers."""
    FAST = "fast"           # 4B - quick iterations
    BALANCED = "balanced"   # 12B - better quality
    QUALITY = "quality"     # Gemini - best quality, fastest, paid

@dataclass
class LLMConfig:
    """Complete LLM configuration."""

    # Provider selection
    default_provider: str = "auto"  # auto, ollama, gemini
    model_tier: ModelTier = ModelTier.FAST
    fallback_enabled: bool = True

    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_model_fast: str = "gemma3:4b-it-qat"
    ollama_model_balanced: str = "gemma3:12b-it-qat"

    # Gemini settings
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"

    # Performance tuning
    max_retries: int = 2
    retry_delay_ms: int = 500
    default_temperature: float = 0.7

    # Token budgets (critical for Ollama performance)
    token_budgets: dict = field(default_factory=lambda: {
        "simple_score": 150,
        "evaluation": 500,
        "multi_evaluation": 1000,
        "idea_generation": 600,
        "advocacy": 800,
        "skepticism": 800,
        "logical_inference": 1000,
    })

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 86400  # 24 hours
    cache_dir: str = ".cache/llm"

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load configuration from environment variables."""
        tier_str = os.getenv("MADSPARK_MODEL_TIER", "fast").lower()
        try:
            tier = ModelTier(tier_str)
        except ValueError:
            tier = ModelTier.FAST

        return cls(
            default_provider=os.getenv("MADSPARK_LLM_PROVIDER", "auto"),
            model_tier=tier,
            fallback_enabled=os.getenv("MADSPARK_FALLBACK_ENABLED", "true").lower() == "true",
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model_fast=os.getenv("OLLAMA_MODEL_FAST", "gemma3:4b-it-qat"),
            ollama_model_balanced=os.getenv("OLLAMA_MODEL_BALANCED", "gemma3:12b-it-qat"),
            gemini_api_key=os.getenv("GOOGLE_API_KEY"),
            gemini_model=os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
            cache_enabled=os.getenv("MADSPARK_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("MADSPARK_CACHE_TTL", "86400")),
            cache_dir=os.getenv("MADSPARK_CACHE_DIR", ".cache/llm"),
        )

    def get_ollama_model(self) -> str:
        """Get Ollama model based on tier."""
        if self.model_tier == ModelTier.FAST:
            return self.ollama_model_fast
        return self.ollama_model_balanced

    def get_token_budget(self, request_type: str) -> int:
        """Get token budget for request type."""
        return self.token_budgets.get(request_type, 500)


# Singleton config instance
_config_instance: Optional[LLMConfig] = None

def get_config() -> LLMConfig:
    """Get singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = LLMConfig.from_env()
    return _config_instance

def reset_config():
    """Reset config (for testing)."""
    global _config_instance
    _config_instance = None
```

**One-line model change**:
```python
# In config.py or .env
model_tier: ModelTier = ModelTier.FAST  # Change to BALANCED or QUALITY
```

### 1.4 Ollama Provider Implementation

**File**: `src/madspark/llm/providers/ollama.py`

```python
import logging
import time
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel, ValidationError

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import (
    ProviderUnavailableError,
    SchemaValidationError
)
from madspark.llm.config import get_config

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None  # type: ignore

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama-based LLM provider using local models.

    Primary provider for cost-effective inference.
    Supports text and image inputs (gemma3 multimodal).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        host: Optional[str] = None
    ):
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "ollama package not installed. Run: uv pip install ollama"
            )

        config = get_config()
        self._model = model or config.get_ollama_model()
        self._host = host or config.ollama_host
        self._client = None
        self._config = config

    @property
    def client(self):
        """Lazy initialization of Ollama client."""
        if self._client is None:
            self._client = ollama.Client(host=self._host)
        return self._client

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def supports_multimodal(self) -> bool:
        # gemma3 supports images, but not PDFs/URLs
        return "gemma3" in self._model

    def health_check(self) -> bool:
        """Check if Ollama server is running and model is available."""
        try:
            models = self.client.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            # Check if model is available (exact match or partial)
            return any(self._model in name or name in self._model
                      for name in model_names)
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        images: Optional[list[Union[str, Path]]] = None
    ) -> LLMResponse:
        """Generate unstructured text completion."""

        if not self.health_check():
            raise ProviderUnavailableError(
                f"Ollama not available. Is 'ollama serve' running? "
                f"Is model '{self._model}' pulled?"
            )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        user_message = {"role": "user", "content": prompt}
        if images:
            # Convert paths to strings, Ollama handles base64 or file paths
            user_message["images"] = [str(img) for img in images]
        messages.append(user_message)

        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        start = time.time()
        response = self.client.chat(
            model=self._model,
            messages=messages,
            options=options
        )
        latency = (time.time() - start) * 1000

        return LLMResponse(
            text=response.message.content,
            provider=self.provider_name,
            model=self._model,
            tokens_used=response.get("eval_count", 0),
            latency_ms=latency,
            cost=0.0  # Free!
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,  # Default 0 for structured output
        images: Optional[list[Union[str, Path]]] = None,
        token_budget: Optional[int] = None
    ) -> tuple[Any, LLMResponse]:
        """
        Generate structured output validated against Pydantic model.

        Uses Ollama's native JSON schema enforcement.
        """

        if not self.health_check():
            raise ProviderUnavailableError(
                f"Ollama not available. Model: {self._model}"
            )

        # Get JSON schema from Pydantic model
        json_schema = schema.model_json_schema()

        # Determine token budget
        if token_budget is None:
            # Estimate based on schema complexity
            token_budget = self._estimate_token_budget(json_schema)

        # Best practice: Include schema in prompt for grounding
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond with valid JSON matching this schema. "
            f"Keep each field concise and focused on key points."
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        user_message = {"role": "user", "content": enhanced_prompt}
        if images:
            user_message["images"] = [str(img) for img in images]
        messages.append(user_message)

        start = time.time()
        try:
            response = self.client.chat(
                model=self._model,
                messages=messages,
                format=json_schema,  # Ollama's native schema enforcement
                options={
                    "temperature": temperature,
                    "num_predict": token_budget
                }
            )
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise ProviderUnavailableError(f"Ollama call failed: {e}")

        latency = (time.time() - start) * 1000

        # Validate with Pydantic
        try:
            validated = schema.model_validate_json(response.message.content)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(
                f"Ollama output doesn't match schema: {e}"
            )

        llm_response = LLMResponse(
            text=response.message.content,
            provider=self.provider_name,
            model=self._model,
            tokens_used=response.get("eval_count", 0),
            latency_ms=latency,
            cost=0.0
        )

        logger.info(
            f"Ollama generated structured output in {latency:.0f}ms "
            f"({response.get('eval_count', 0)} tokens)"
        )

        return validated, llm_response

    def _estimate_token_budget(self, schema: dict) -> int:
        """Estimate token budget based on schema complexity."""
        # Count required fields recursively
        def count_fields(s: dict) -> int:
            count = 0
            props = s.get("properties", {})
            count += len(props)

            # Check for nested objects
            for prop_schema in props.values():
                if prop_schema.get("type") == "object":
                    count += count_fields(prop_schema) * 2
                elif prop_schema.get("type") == "array":
                    items = prop_schema.get("items", {})
                    if items.get("type") == "object":
                        count += count_fields(items) * 3

            # Check for $defs (nested models)
            defs = s.get("$defs", {})
            for def_schema in defs.values():
                count += count_fields(def_schema)

            return count

        field_count = count_fields(schema)

        # Base budget + per-field allocation
        # Each field needs ~50-100 tokens for content
        budget = 100 + (field_count * 80)

        # Cap at reasonable maximum
        return min(budget, 2000)

    def get_cost_per_token(self) -> float:
        """Local inference is free."""
        return 0.0
```

### 1.5 Gemini Provider (Adapt Existing)

**File**: `src/madspark/llm/providers/gemini.py`

```python
import logging
import os
import time
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import (
    ProviderUnavailableError,
    SchemaValidationError
)
from madspark.llm.config import get_config

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore
    types = None  # type: ignore

# Import existing adapter (reuse!)
try:
    from madspark.schemas.adapters import (
        pydantic_to_genai_schema,
        genai_response_to_pydantic
    )
except ImportError:
    # Will be available after migration
    pydantic_to_genai_schema = None  # type: ignore
    genai_response_to_pydantic = None  # type: ignore

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Used for:
    - PDF/URL processing (native Gemini support)
    - Fallback when Ollama fails
    - High-quality/fast inference (paid)
    - Developer comparison testing
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Run: uv pip install google-genai"
            )

        config = get_config()
        self._api_key = api_key or config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
        self._model = model or config.gemini_model
        self._client = None

        if not self._api_key:
            raise ProviderUnavailableError(
                "GOOGLE_API_KEY not set. Required for Gemini provider."
            )

    @property
    def client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None:
            # Client uses GOOGLE_API_KEY from environment by default
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def supports_multimodal(self) -> bool:
        return True  # Full PDF, URL, image support

    def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            # Quick check - just verify client works
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None
    ) -> LLMResponse:
        """Generate unstructured text completion."""

        config_dict = {"temperature": temperature}
        if system_instruction:
            config_dict["system_instruction"] = system_instruction
        if max_tokens:
            config_dict["max_output_tokens"] = max_tokens

        config = types.GenerateContentConfig(**config_dict)

        # Build content
        contents = []

        if files:
            for file_path in files:
                part = types.Part.from_file(str(file_path))
                contents.append(part)

        if urls:
            url_context = "\n".join([f"Reference: {url}" for url in urls])
            prompt = f"{url_context}\n\n{prompt}"

        contents.append(prompt)

        start = time.time()
        response = self.client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config
        )
        latency = (time.time() - start) * 1000

        usage = getattr(response, 'usage_metadata', None)
        tokens = usage.total_token_count if usage else 0

        return LLMResponse(
            text=response.text,
            provider=self.provider_name,
            model=self._model,
            tokens_used=tokens,
            latency_ms=latency,
            cost=tokens * self.get_cost_per_token()
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.7,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        **kwargs  # Accept extra args for compatibility
    ) -> tuple[Any, LLMResponse]:
        """Generate structured output with optional PDF/URL inputs."""

        if pydantic_to_genai_schema is None:
            raise ImportError("Schema adapters not available")

        # Convert Pydantic to Gemini's schema format
        genai_schema = pydantic_to_genai_schema(schema)

        config_dict = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": genai_schema,
        }
        if system_instruction:
            config_dict["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_dict)

        # Build content with optional files/URLs
        contents = []

        if files:
            for file_path in files:
                part = types.Part.from_file(str(file_path))
                contents.append(part)

        if urls:
            url_context = "\n".join([f"Analyze this URL: {url}" for url in urls])
            prompt = f"{url_context}\n\n{prompt}"

        contents.append(prompt)

        start = time.time()
        response = self.client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config
        )
        latency = (time.time() - start) * 1000

        # Validate with Pydantic
        try:
            validated = genai_response_to_pydantic(response.text, schema)
        except Exception as e:
            raise SchemaValidationError(
                f"Gemini output validation failed: {e}"
            )

        usage = getattr(response, 'usage_metadata', None)
        tokens = usage.total_token_count if usage else 0

        llm_response = LLMResponse(
            text=response.text,
            provider=self.provider_name,
            model=self._model,
            tokens_used=tokens,
            latency_ms=latency,
            cost=tokens * self.get_cost_per_token()
        )

        logger.info(
            f"Gemini generated structured output in {latency:.0f}ms "
            f"({tokens} tokens, ${llm_response.cost:.6f})"
        )

        return validated, llm_response

    def extract_content_from_files(
        self,
        files: list[Path],
        urls: Optional[list[str]] = None
    ) -> str:
        """
        Extract text content from PDFs/URLs for handoff to Ollama.

        Used when user provides --file/--url but we want Ollama for workflow.
        """
        extraction_prompt = (
            "Extract and summarize all text content from the provided documents. "
            "Maintain key information, structure, and important details. "
            "Output as plain text suitable for further analysis."
        )

        config = types.GenerateContentConfig(
            temperature=0.1,  # Low temp for faithful extraction
            system_instruction="You are a content extraction assistant. "
                             "Extract text faithfully while preserving structure."
        )

        contents = []
        for file_path in files:
            contents.append(types.Part.from_file(str(file_path)))

        if urls:
            url_context = "\n".join([f"Fetch content from: {url}" for url in urls])
            extraction_prompt = f"{url_context}\n\n{extraction_prompt}"

        contents.append(extraction_prompt)

        response = self.client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config
        )

        logger.info(f"Extracted {len(response.text)} chars from {len(files)} files")
        return response.text

    def get_cost_per_token(self) -> float:
        """Gemini 2.5 Flash approximate pricing."""
        # ~$0.075 per million input tokens + $0.30 per million output tokens
        # Simplified average
        return 0.0000002  # $0.20 per million tokens average
```

### 1.6 Unit Tests for Phase 1

**File**: `tests/test_llm_providers.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field

from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE
from madspark.llm.providers.gemini import GeminiProvider
from madspark.llm.response import LLMResponse
from madspark.llm.config import LLMConfig, ModelTier, get_config, reset_config
from madspark.llm.exceptions import ProviderUnavailableError


class SimpleSchema(BaseModel):
    score: float = Field(ge=0, le=10)
    comment: str


@pytest.fixture
def reset_config_fixture():
    """Reset config singleton after each test."""
    yield
    reset_config()


class TestLLMConfig:
    def test_default_config(self, reset_config_fixture):
        config = LLMConfig()
        assert config.model_tier == ModelTier.FAST
        assert config.fallback_enabled is True
        assert config.cache_enabled is True

    def test_get_ollama_model_fast(self, reset_config_fixture):
        config = LLMConfig(model_tier=ModelTier.FAST)
        assert config.get_ollama_model() == "gemma3:4b-it-qat"

    def test_get_ollama_model_balanced(self, reset_config_fixture):
        config = LLMConfig(model_tier=ModelTier.BALANCED)
        assert config.get_ollama_model() == "gemma3:12b-it-qat"

    def test_token_budget(self, reset_config_fixture):
        config = LLMConfig()
        assert config.get_token_budget("simple_score") == 150
        assert config.get_token_budget("evaluation") == 500
        assert config.get_token_budget("unknown") == 500  # Default


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not installed")
class TestOllamaProvider:
    @patch('madspark.llm.providers.ollama.ollama')
    def test_init(self, mock_ollama):
        provider = OllamaProvider(model="test-model", host="http://test:11434")
        assert provider.provider_name == "ollama"
        assert provider.model_name == "test-model"
        assert provider.supports_multimodal is False  # Not gemma3

    @patch('madspark.llm.providers.ollama.ollama')
    def test_gemma3_supports_multimodal(self, mock_ollama):
        provider = OllamaProvider(model="gemma3:4b-it-qat")
        assert provider.supports_multimodal is True

    @patch('madspark.llm.providers.ollama.ollama')
    def test_health_check_success(self, mock_ollama):
        mock_client = Mock()
        mock_client.list.return_value = {
            "models": [{"name": "gemma3:4b-it-qat"}]
        }

        provider = OllamaProvider(model="gemma3:4b-it-qat")
        provider._client = mock_client

        assert provider.health_check() is True

    @patch('madspark.llm.providers.ollama.ollama')
    def test_health_check_failure(self, mock_ollama):
        mock_client = Mock()
        mock_client.list.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        provider._client = mock_client

        assert provider.health_check() is False

    @patch('madspark.llm.providers.ollama.ollama')
    def test_generate_structured(self, mock_ollama):
        mock_response = Mock()
        mock_response.message.content = '{"score": 8.5, "comment": "Great idea"}'
        mock_response.get.return_value = 50

        mock_client = Mock()
        mock_client.chat.return_value = mock_response
        mock_client.list.return_value = {"models": [{"name": "gemma3:4b"}]}

        provider = OllamaProvider(model="gemma3:4b")
        provider._client = mock_client

        validated, response = provider.generate_structured(
            prompt="Rate this idea",
            schema=SimpleSchema
        )

        assert validated.score == 8.5
        assert validated.comment == "Great idea"
        assert response.provider == "ollama"
        assert response.cost == 0.0

    def test_cost_is_zero(self):
        with patch('madspark.llm.providers.ollama.ollama'):
            provider = OllamaProvider()
            assert provider.get_cost_per_token() == 0.0


class TestLLMResponse:
    def test_response_creation(self):
        response = LLMResponse(
            text="test",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=5000
        )
        assert response.text == "test"
        assert response.provider == "ollama"
        assert response.cost == 0.0
        assert response.cached is False

    def test_to_dict(self):
        response = LLMResponse(
            text="test",
            provider="gemini",
            model="gemini-2.5-flash",
            tokens_used=100,
            latency_ms=500,
            cost=0.00002
        )
        d = response.to_dict()
        assert d["provider"] == "gemini"
        assert d["cost"] == 0.00002
        assert "timestamp" in d
```

### 1.7 Phase 1 Verification Checklist

- [ ] Package structure created
- [ ] All base classes implemented
- [ ] OllamaProvider passes unit tests
- [ ] GeminiProvider passes unit tests
- [ ] Config singleton works
- [ ] Health checks functional
- [ ] Structured output generation works with mocks

---

## Phase 2: Response Caching (~3 hours)

**PR Milestone**: Create PR after Phase 2 with cache implementation and integration tests.

### 2.1 Cache Implementation

**File**: `src/madspark/llm/cache.py`

```python
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional, Type
from pydantic import BaseModel

try:
    from diskcache import Cache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False
    Cache = None  # type: ignore

from madspark.llm.config import get_config
from madspark.llm.response import LLMResponse

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Disk-based cache for LLM responses.

    Benefits:
    - Avoid redundant API calls (~50% reduction)
    - Instant responses for repeated queries
    - Persistent across sessions
    - TTL-based expiration
    """

    _instance = None

    def __init__(self, cache_dir: Optional[str] = None, ttl: Optional[int] = None):
        if not DISKCACHE_AVAILABLE:
            raise ImportError(
                "diskcache not installed. Run: uv pip install diskcache"
            )

        config = get_config()
        self._cache_dir = cache_dir or config.cache_dir
        self._ttl = ttl or config.cache_ttl_seconds
        self._enabled = config.cache_enabled

        # Create cache directory
        Path(self._cache_dir).mkdir(parents=True, exist_ok=True)

        # Initialize disk cache
        self._cache = Cache(self._cache_dir)

        logger.info(f"LLM cache initialized: {self._cache_dir} (TTL: {self._ttl}s)")

    @classmethod
    def get_instance(cls) -> "LLMCache":
        """Get singleton cache instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset cache (for testing)."""
        if cls._instance is not None:
            cls._instance.clear()
        cls._instance = None

    def _generate_key(
        self,
        prompt: str,
        schema: Type[BaseModel],
        provider: str,
        model: str,
        temperature: float,
        system_instruction: str = ""
    ) -> str:
        """Generate cache key from request parameters."""
        # Create deterministic hash
        key_data = {
            "prompt": prompt,
            "schema": schema.__name__,
            "schema_hash": hashlib.md5(
                json.dumps(schema.model_json_schema(), sort_keys=True).encode()
            ).hexdigest(),
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "system_instruction": system_instruction
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        schema: Type[BaseModel],
        provider: str,
        model: str,
        temperature: float = 0.0,
        system_instruction: str = ""
    ) -> Optional[tuple[Any, LLMResponse]]:
        """
        Get cached response if available.

        Returns:
            tuple of (validated_data, response) if cached, None otherwise
        """
        if not self._enabled:
            return None

        key = self._generate_key(
            prompt, schema, provider, model, temperature, system_instruction
        )

        cached = self._cache.get(key)
        if cached is None:
            return None

        try:
            # Reconstruct objects
            validated = schema.model_validate(cached["data"])
            response = LLMResponse(
                text=cached["response"]["text"],
                provider=cached["response"]["provider"],
                model=cached["response"]["model"],
                tokens_used=cached["response"]["tokens_used"],
                latency_ms=0.0,  # Instant from cache
                cost=0.0,  # No cost from cache
                cached=True  # Mark as cached
            )

            logger.debug(f"Cache hit for {schema.__name__}")
            return validated, response

        except Exception as e:
            logger.warning(f"Cache deserialization failed: {e}")
            # Remove corrupted entry
            self._cache.delete(key)
            return None

    def set(
        self,
        prompt: str,
        schema: Type[BaseModel],
        provider: str,
        model: str,
        temperature: float,
        system_instruction: str,
        validated_data: Any,
        response: LLMResponse
    ):
        """Cache a response."""
        if not self._enabled:
            return

        key = self._generate_key(
            prompt, schema, provider, model, temperature, system_instruction
        )

        cache_data = {
            "data": validated_data.model_dump() if hasattr(validated_data, 'model_dump') else validated_data,
            "response": {
                "text": response.text,
                "provider": response.provider,
                "model": response.model,
                "tokens_used": response.tokens_used,
            }
        }

        self._cache.set(key, cache_data, expire=self._ttl)
        logger.debug(f"Cached response for {schema.__name__}")

    def clear(self):
        """Clear all cached responses."""
        self._cache.clear()
        logger.info("LLM cache cleared")

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "volume_bytes": self._cache.volume(),
            "directory": self._cache_dir,
            "ttl_seconds": self._ttl,
            "enabled": self._enabled
        }


def get_cache() -> LLMCache:
    """Get singleton cache instance."""
    return LLMCache.get_instance()
```

### 2.2 Cache Integration in Router

```python
# In router.py, wrap generate_structured with cache layer

def generate_structured_with_cache(
    self,
    prompt: str,
    schema: Type[BaseModel],
    system_instruction: str = "",
    temperature: float = 0.0,
    **kwargs
) -> tuple[Any, LLMResponse, str]:
    """Generate with cache check."""

    # Check cache first
    if self.config.cache_enabled:
        cache = get_cache()
        cached_result = cache.get(
            prompt=prompt,
            schema=schema,
            provider="auto",  # Will try to match any provider
            model="any",
            temperature=temperature,
            system_instruction=system_instruction
        )

        if cached_result:
            validated, response = cached_result
            logger.info("Using cached response")
            return validated, response, response.provider

    # Generate new response
    validated, response, provider_used = self.generate_structured(
        prompt=prompt,
        schema=schema,
        system_instruction=system_instruction,
        temperature=temperature,
        **kwargs
    )

    # Cache the result
    if self.config.cache_enabled:
        cache.set(
            prompt=prompt,
            schema=schema,
            provider=provider_used,
            model=response.model,
            temperature=temperature,
            system_instruction=system_instruction,
            validated_data=validated,
            response=response
        )

    return validated, response, provider_used
```

### 2.3 Cache Tests

**File**: `tests/test_llm_cache.py`

```python
import pytest
from pathlib import Path
from pydantic import BaseModel, Field
from madspark.llm.cache import LLMCache, get_cache
from madspark.llm.response import LLMResponse


class TestSchema(BaseModel):
    score: float = Field(ge=0, le=10)
    comment: str


@pytest.fixture
def temp_cache(tmp_path):
    """Create temporary cache for testing."""
    cache = LLMCache(cache_dir=str(tmp_path / "cache"), ttl=3600)
    yield cache
    cache.clear()


class TestLLMCache:
    def test_cache_miss(self, temp_cache):
        result = temp_cache.get(
            prompt="test",
            schema=TestSchema,
            provider="ollama",
            model="gemma3:4b"
        )
        assert result is None

    def test_cache_hit(self, temp_cache):
        # Store
        validated = TestSchema(score=8.0, comment="Good")
        response = LLMResponse(
            text='{"score": 8.0, "comment": "Good"}',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=50,
            latency_ms=5000
        )

        temp_cache.set(
            prompt="test",
            schema=TestSchema,
            provider="ollama",
            model="gemma3:4b",
            temperature=0.0,
            system_instruction="",
            validated_data=validated,
            response=response
        )

        # Retrieve
        result = temp_cache.get(
            prompt="test",
            schema=TestSchema,
            provider="ollama",
            model="gemma3:4b"
        )

        assert result is not None
        cached_data, cached_response = result
        assert cached_data.score == 8.0
        assert cached_response.cached is True
        assert cached_response.latency_ms == 0.0

    def test_cache_stats(self, temp_cache):
        stats = temp_cache.stats()
        assert "size" in stats
        assert "volume_bytes" in stats
        assert stats["enabled"] is True
```

### 2.4 Phase 2 Verification Checklist

- [ ] Cache implementation complete
- [ ] Cache integrates with router
- [ ] Cache hit/miss works correctly
- [ ] TTL expiration functional
- [ ] Cache can be disabled via config
- [ ] Cache stats available
- [ ] Unit tests pass

---

## Phase 3: Router & Fallback Logic (~3 hours)

**PR Milestone**: Create PR after Phase 3 with complete router, fallback mechanism, and metrics.

### 3.1 Complete Router Implementation

**File**: `src/madspark/llm/router.py`

```python
import logging
from typing import Optional, Type, Any, Union
from pathlib import Path
from pydantic import BaseModel

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.providers.ollama import OllamaProvider, OLLAMA_AVAILABLE
from madspark.llm.providers.gemini import GeminiProvider, GENAI_AVAILABLE
from madspark.llm.cache import get_cache, DISKCACHE_AVAILABLE
from madspark.llm.config import get_config, ModelTier, LLMConfig
from madspark.llm.exceptions import (
    AllProvidersFailedError,
    ProviderUnavailableError
)

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Intelligent routing between LLM providers with automatic fallback.

    Priority: Ollama (free) → Gemini (paid fallback)
    """

    _instance = None

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_config()
        self._providers: dict[str, LLMProvider] = {}
        self._metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "ollama_requests": 0,
            "gemini_requests": 0,
            "fallback_count": 0,
            "total_failures": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "total_latency_ms": 0.0
        }

        self._initialize_providers()

    @classmethod
    def get_instance(cls, config: Optional[LLMConfig] = None) -> "LLMRouter":
        """Get singleton router instance."""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    def _initialize_providers(self):
        """Initialize available providers based on config."""

        # Try Ollama first (primary)
        if OLLAMA_AVAILABLE:
            try:
                ollama_provider = OllamaProvider(
                    model=self.config.get_ollama_model(),
                    host=self.config.ollama_host
                )
                if ollama_provider.health_check():
                    self._providers["ollama"] = ollama_provider
                    logger.info(
                        f"Ollama provider ready: {self.config.get_ollama_model()}"
                    )
                else:
                    logger.warning(
                        "Ollama server not running or model not available. "
                        "Run: ollama serve"
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama: {e}")
        else:
            logger.info("Ollama package not installed")

        # Try Gemini (fallback + PDF/URL)
        if GENAI_AVAILABLE and self.config.gemini_api_key:
            try:
                gemini_provider = GeminiProvider(
                    api_key=self.config.gemini_api_key,
                    model=self.config.gemini_model
                )
                self._providers["gemini"] = gemini_provider
                logger.info(f"Gemini provider ready: {self.config.gemini_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
        elif not self.config.gemini_api_key:
            logger.info("Gemini API key not set (GOOGLE_API_KEY)")

        if not self._providers:
            logger.error(
                "No LLM providers available! "
                "Ensure Ollama is running or GOOGLE_API_KEY is set."
            )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,
        force_provider: Optional[str] = None,
        images: Optional[list[Union[str, Path]]] = None,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        request_type: str = "evaluation",
        use_cache: bool = True
    ) -> tuple[Any, LLMResponse, str]:
        """
        Generate structured output with intelligent routing and fallback.

        Args:
            prompt: The prompt text
            schema: Pydantic model for structured output
            system_instruction: System prompt
            temperature: Generation temperature
            force_provider: Force specific provider (developer only)
            images: Image inputs (Ollama can handle)
            files: PDF/document files (Gemini only)
            urls: URLs to fetch (Gemini only)
            request_type: Type for token budget estimation
            use_cache: Whether to use response cache

        Returns:
            tuple: (validated_data, response_metadata, provider_used)
        """
        self._metrics["total_requests"] += 1

        # Step 1: Check cache
        if use_cache and self.config.cache_enabled and DISKCACHE_AVAILABLE:
            cached = self._check_cache(
                prompt, schema, temperature, system_instruction
            )
            if cached:
                self._metrics["cache_hits"] += 1
                return cached

        # Step 2: Handle PDF/URL extraction (Gemini only)
        if files or urls:
            prompt = self._extract_file_content(prompt, files, urls)

        # Step 3: Determine provider order
        providers_to_try = self._get_provider_order(force_provider, bool(files or urls))

        # Step 4: Try providers with fallback
        validated, response, provider_used = self._try_providers(
            providers_to_try=providers_to_try,
            prompt=prompt,
            schema=schema,
            system_instruction=system_instruction,
            temperature=temperature,
            images=images,
            request_type=request_type
        )

        # Step 5: Cache result
        if use_cache and self.config.cache_enabled and DISKCACHE_AVAILABLE:
            self._cache_result(
                prompt, schema, temperature, system_instruction,
                validated, response, provider_used
            )

        # Step 6: Update metrics
        self._update_metrics(response, provider_used)

        return validated, response, provider_used

    def _check_cache(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float,
        system_instruction: str
    ) -> Optional[tuple[Any, LLMResponse, str]]:
        """Check cache for existing response."""
        cache = get_cache()

        # Try to find cached result from any provider
        for provider_name in self._providers:
            model = self._providers[provider_name].model_name
            cached = cache.get(
                prompt=prompt,
                schema=schema,
                provider=provider_name,
                model=model,
                temperature=temperature,
                system_instruction=system_instruction
            )
            if cached:
                logger.info(f"Cache hit (from {provider_name})")
                validated, response = cached
                return validated, response, provider_name

        return None

    def _extract_file_content(
        self,
        prompt: str,
        files: Optional[list[Path]],
        urls: Optional[list[str]]
    ) -> str:
        """Extract content from PDFs/URLs using Gemini."""
        if "gemini" not in self._providers:
            raise ProviderUnavailableError(
                "PDF/URL processing requires Gemini API. "
                "Set GOOGLE_API_KEY environment variable."
            )

        logger.info("Extracting content from files/URLs via Gemini...")
        extracted = self._providers["gemini"].extract_content_from_files(
            files or [], urls or []
        )

        return f"Context from provided documents:\n{extracted}\n\n{prompt}"

    def _get_provider_order(
        self,
        force_provider: Optional[str],
        needs_gemini_features: bool
    ) -> list[str]:
        """Determine provider attempt order."""

        if force_provider:
            if force_provider not in self._providers:
                raise ProviderUnavailableError(f"Provider not available: {force_provider}")
            return [force_provider]

        # Default: Ollama first (cost savings), Gemini as fallback
        if self.config.model_tier == ModelTier.QUALITY:
            # User wants quality, use Gemini
            order = ["gemini", "ollama"]
        else:
            # Default: local first
            order = ["ollama", "gemini"]

        if not self.config.fallback_enabled:
            # Only use first available
            order = [order[0]] if order else []

        # Filter to available providers
        return [p for p in order if p in self._providers]

    def _try_providers(
        self,
        providers_to_try: list[str],
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str,
        temperature: float,
        images: Optional[list],
        request_type: str
    ) -> tuple[Any, LLMResponse, str]:
        """Try providers in order with fallback."""

        if not providers_to_try:
            raise ProviderUnavailableError("No providers available")

        errors = []

        for idx, provider_name in enumerate(providers_to_try):
            provider = self._providers[provider_name]

            for attempt in range(self.config.max_retries):
                try:
                    logger.info(
                        f"Trying {provider_name} (attempt {attempt + 1}/{self.config.max_retries})"
                    )

                    # Prepare kwargs based on provider capabilities
                    kwargs = {
                        "prompt": prompt,
                        "schema": schema,
                        "system_instruction": system_instruction,
                        "temperature": temperature,
                    }

                    if provider_name == "ollama":
                        if images:
                            kwargs["images"] = images
                        # Add token budget for Ollama
                        kwargs["token_budget"] = self.config.get_token_budget(request_type)

                    validated, response = provider.generate_structured(**kwargs)

                    logger.info(
                        f"Success with {provider_name} in {response.latency_ms:.0f}ms "
                        f"({response.tokens_used} tokens)"
                    )

                    return validated, response, provider_name

                except Exception as e:
                    errors.append((provider_name, attempt + 1, str(e)))
                    logger.warning(
                        f"{provider_name} attempt {attempt + 1} failed: {e}"
                    )

            # Provider exhausted retries, try next
            if idx < len(providers_to_try) - 1:
                self._metrics["fallback_count"] += 1
                logger.info(f"Falling back from {provider_name}")

        # All providers failed
        self._metrics["total_failures"] += 1
        raise AllProvidersFailedError(
            f"All providers failed after attempts: {errors}"
        )

    def _cache_result(
        self,
        prompt: str,
        schema: Type[BaseModel],
        temperature: float,
        system_instruction: str,
        validated: Any,
        response: LLMResponse,
        provider_used: str
    ):
        """Cache successful result."""
        cache = get_cache()
        cache.set(
            prompt=prompt,
            schema=schema,
            provider=provider_used,
            model=response.model,
            temperature=temperature,
            system_instruction=system_instruction,
            validated_data=validated,
            response=response
        )

    def _update_metrics(self, response: LLMResponse, provider_used: str):
        """Update internal metrics."""
        self._metrics[f"{provider_used}_requests"] += 1
        self._metrics["total_tokens"] += response.tokens_used
        self._metrics["total_latency_ms"] += response.latency_ms
        self._metrics["estimated_cost"] += response.cost

    def get_metrics(self) -> dict:
        """Get routing metrics for monitoring."""
        metrics = self._metrics.copy()

        # Add computed metrics
        if metrics["total_requests"] > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / metrics["total_requests"]
            metrics["avg_latency_ms"] = metrics["total_latency_ms"] / metrics["total_requests"]
            metrics["fallback_rate"] = metrics["fallback_count"] / metrics["total_requests"]

        return metrics

    def get_available_providers(self) -> list[str]:
        """List available providers."""
        return list(self._providers.keys())

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get specific provider instance."""
        return self._providers.get(name)


# Convenience functions
def get_router() -> LLMRouter:
    """Get singleton router instance."""
    return LLMRouter.get_instance()

def reset_router():
    """Reset router (for testing)."""
    LLMRouter.reset_instance()
```

### 3.2 Router Tests

**File**: `tests/test_llm_router.py`

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field

from madspark.llm.router import LLMRouter, get_router, reset_router
from madspark.llm.config import LLMConfig, ModelTier, reset_config
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import AllProvidersFailedError


class TestSchema(BaseModel):
    score: float = Field(ge=0, le=10)
    comment: str


@pytest.fixture
def reset_singletons():
    """Reset all singletons after test."""
    yield
    reset_router()
    reset_config()


@pytest.fixture
def mock_router(reset_singletons):
    """Create router with mock providers."""
    config = LLMConfig(
        fallback_enabled=True,
        cache_enabled=False  # Disable cache for unit tests
    )

    with patch('madspark.llm.router.OllamaProvider') as mock_ollama_cls, \
         patch('madspark.llm.router.GeminiProvider') as mock_gemini_cls, \
         patch('madspark.llm.router.OLLAMA_AVAILABLE', True), \
         patch('madspark.llm.router.GENAI_AVAILABLE', True):

        # Mock Ollama provider
        mock_ollama = Mock()
        mock_ollama.provider_name = "ollama"
        mock_ollama.model_name = "gemma3:4b-it-qat"
        mock_ollama.health_check.return_value = True
        mock_ollama.get_cost_per_token.return_value = 0.0
        mock_ollama_cls.return_value = mock_ollama

        # Mock Gemini provider
        mock_gemini = Mock()
        mock_gemini.provider_name = "gemini"
        mock_gemini.model_name = "gemini-2.5-flash"
        mock_gemini.health_check.return_value = True
        mock_gemini.get_cost_per_token.return_value = 0.0000002
        mock_gemini_cls.return_value = mock_gemini

        router = LLMRouter(config)
        router._providers = {
            "ollama": mock_ollama,
            "gemini": mock_gemini
        }

        yield router, mock_ollama, mock_gemini


class TestLLMRouter:
    def test_ollama_primary(self, mock_router):
        router, mock_ollama, mock_gemini = mock_router

        # Setup Ollama success
        validated = TestSchema(score=8.0, comment="Good")
        response = LLMResponse(
            text="{}",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=5000
        )
        mock_ollama.generate_structured.return_value = (validated, response)

        result_data, result_response, provider_used = router.generate_structured(
            prompt="test",
            schema=TestSchema
        )

        assert provider_used == "ollama"
        assert result_data.score == 8.0
        mock_ollama.generate_structured.assert_called_once()
        mock_gemini.generate_structured.assert_not_called()

    def test_fallback_to_gemini(self, mock_router):
        router, mock_ollama, mock_gemini = mock_router

        # Setup Ollama failure
        mock_ollama.generate_structured.side_effect = Exception("Ollama error")

        # Setup Gemini success
        validated = TestSchema(score=7.0, comment="Fallback")
        response = LLMResponse(
            text="{}",
            provider="gemini",
            model="gemini-2.5-flash",
            tokens_used=50,
            latency_ms=500
        )
        mock_gemini.generate_structured.return_value = (validated, response)

        result_data, result_response, provider_used = router.generate_structured(
            prompt="test",
            schema=TestSchema
        )

        assert provider_used == "gemini"
        assert result_data.score == 7.0
        assert router._metrics["fallback_count"] == 1

    def test_all_providers_fail(self, mock_router):
        router, mock_ollama, mock_gemini = mock_router

        mock_ollama.generate_structured.side_effect = Exception("Ollama error")
        mock_gemini.generate_structured.side_effect = Exception("Gemini error")

        with pytest.raises(AllProvidersFailedError):
            router.generate_structured(prompt="test", schema=TestSchema)

    def test_force_provider(self, mock_router):
        router, mock_ollama, mock_gemini = mock_router

        validated = TestSchema(score=9.0, comment="Forced")
        response = LLMResponse(
            text="{}",
            provider="gemini",
            model="gemini-2.5-flash",
            tokens_used=50,
            latency_ms=500
        )
        mock_gemini.generate_structured.return_value = (validated, response)

        _, _, provider_used = router.generate_structured(
            prompt="test",
            schema=TestSchema,
            force_provider="gemini"
        )

        assert provider_used == "gemini"
        mock_ollama.generate_structured.assert_not_called()

    def test_metrics_tracking(self, mock_router):
        router, mock_ollama, _ = mock_router

        validated = TestSchema(score=8.0, comment="Good")
        response = LLMResponse(
            text="{}",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=5000
        )
        mock_ollama.generate_structured.return_value = (validated, response)

        router.generate_structured(prompt="test", schema=TestSchema)

        metrics = router.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["ollama_requests"] == 1
        assert metrics["total_tokens"] == 100
```

### 3.3 Phase 3 Verification Checklist

- [ ] Router singleton works
- [ ] Provider initialization successful
- [ ] Ollama → Gemini fallback works
- [ ] Force provider option works
- [ ] Metrics collection accurate
- [ ] PDF/URL extraction via Gemini works
- [ ] Cache integration functional
- [ ] All router tests pass

---

## Phase 4: CLI Integration (~3 hours)

**PR Milestone**: Create PR after Phase 4 with CLI flags and developer tools integrated.

### 4.1 Hidden Developer Flags

**File**: `src/madspark/cli/cli.py` (modify existing)

```python
def create_argument_parser():
    parser = argparse.ArgumentParser(...)

    # ... existing arguments ...

    # Hidden developer flags (not shown in --help)
    dev_group = parser.add_argument_group('Developer Options')

    dev_group.add_argument(
        '--provider',
        type=str,
        choices=['auto', 'ollama', 'gemini'],
        default='auto',
        help=argparse.SUPPRESS  # Hidden
    )

    dev_group.add_argument(
        '--model-tier',
        type=str,
        choices=['fast', 'balanced', 'quality'],
        default=None,
        help=argparse.SUPPRESS  # Hidden
    )

    dev_group.add_argument(
        '--no-fallback',
        action='store_true',
        help=argparse.SUPPRESS  # Hidden
    )

    dev_group.add_argument(
        '--no-cache',
        action='store_true',
        help=argparse.SUPPRESS  # Hidden
    )

    dev_group.add_argument(
        '--compare-providers',
        action='store_true',
        help=argparse.SUPPRESS  # Compare same request on both providers
    )

    dev_group.add_argument(
        '--show-metrics',
        action='store_true',
        help=argparse.SUPPRESS  # Show provider metrics at end
    )

    dev_group.add_argument(
        '--clear-cache',
        action='store_true',
        help=argparse.SUPPRESS  # Clear LLM response cache
    )

    return parser
```

### 4.2 CLI Router Integration

```python
# In cli.py main function

def main():
    args = parse_arguments()

    # Handle cache clearing
    if getattr(args, 'clear_cache', False):
        from madspark.llm.cache import get_cache
        cache = get_cache()
        cache.clear()
        print("LLM cache cleared")
        return

    # Configure router based on CLI flags
    from madspark.llm.config import get_config, ModelTier, reset_config
    from madspark.llm.router import get_router

    # Override config if developer flags provided
    config = get_config()

    if getattr(args, 'model_tier', None):
        tier_map = {
            'fast': ModelTier.FAST,
            'balanced': ModelTier.BALANCED,
            'quality': ModelTier.QUALITY
        }
        config.model_tier = tier_map[args.model_tier]

    if getattr(args, 'no_fallback', False):
        config.fallback_enabled = False

    if getattr(args, 'no_cache', False):
        config.cache_enabled = False

    # Get router
    router = get_router()

    # Provider comparison mode (developer only)
    if getattr(args, 'compare_providers', False):
        compare_providers_mode(args, router)
        return

    # Normal execution
    # ... existing logic, but use router for LLM calls ...

    # Show metrics if requested
    if getattr(args, 'show_metrics', False):
        display_metrics(router.get_metrics())

def display_metrics(metrics: dict):
    """Display provider metrics for developer analysis."""
    print("\n=== LLM Provider Metrics ===")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Cache Hits: {metrics['cache_hits']} ({metrics.get('cache_hit_rate', 0):.1%})")
    print(f"Ollama Requests: {metrics['ollama_requests']}")
    print(f"Gemini Requests: {metrics['gemini_requests']}")
    print(f"Fallbacks: {metrics['fallback_count']}")
    print(f"Total Tokens: {metrics['total_tokens']}")
    print(f"Total Latency: {metrics['total_latency_ms']:.0f}ms")
    print(f"Estimated Cost: ${metrics['estimated_cost']:.6f}")

def compare_providers_mode(args, router):
    """Run same request on both providers for comparison."""
    print("=== Provider Comparison Mode ===\n")

    # This would run the same evaluation on both providers
    # and show side-by-side results
    # Implementation details depend on specific use case
    pass
```

### 4.3 CLI Usage Examples (Developer Only)

```bash
# Default: auto (Ollama primary with Gemini fallback)
ms "AI recycling" "environmental sustainability"

# Force Ollama only
ms "AI recycling" "sustainability" --provider ollama

# Force Gemini (paid)
ms "AI recycling" "sustainability" --provider gemini

# Use 12B model (balanced tier)
ms "AI recycling" "sustainability" --model-tier balanced

# Use Gemini for best quality
ms "AI recycling" "sustainability" --model-tier quality

# Disable fallback (fail if primary fails)
ms "AI recycling" "sustainability" --no-fallback

# Disable cache (always run fresh)
ms "AI recycling" "sustainability" --no-cache

# Show metrics at end
ms "AI recycling" "sustainability" --show-metrics

# Clear cache
ms --clear-cache

# Compare providers (A/B testing)
ms "AI recycling" "sustainability" --compare-providers
```

### 4.4 Phase 4 Verification Checklist

- [ ] CLI argument parser updated
- [ ] Hidden flags don't show in `--help`
- [ ] `--provider` flag works
- [ ] `--model-tier` flag works
- [ ] `--show-metrics` displays data
- [ ] `--clear-cache` clears cache
- [ ] Router integration with coordinator
- [ ] PDF/URL inputs route to Gemini

---

## Phase 5: Agent Migration (~6-8 hours)

**PR Milestone**: Create PR after Phase 5 with all agents migrated and tests updated.

### 5.1 Migration Strategy

**Approach**: Create backward-compatible wrapper first, then migrate agents incrementally.

**Migration Order** (by complexity):
1. Critic (simple evaluation schema)
2. Advocate (strengths/opportunities)
3. Skeptic (flaws/risks)
4. IdeaGenerator (generation schema)
5. LogicalInferenceEngine
6. StructuredIdeaGenerator
7. EnhancedReasoning
8. MultiDimensionalEvaluator

### 5.2 Backward Compatibility Wrapper

**File**: `src/madspark/llm/compat.py`

```python
"""
Backward compatibility layer for gradual agent migration.

Allows existing agents to use new router without code changes.
"""
import warnings
from madspark.llm.router import get_router

# Deprecated function - redirects to router
def get_genai_client():
    """
    DEPRECATED: Use get_router() instead.

    This function exists for backward compatibility during migration.
    """
    warnings.warn(
        "get_genai_client() is deprecated. "
        "Use madspark.llm.router.get_router() for provider-agnostic LLM access.",
        DeprecationWarning,
        stacklevel=2
    )

    router = get_router()

    # Return Gemini provider if available (for legacy compatibility)
    if "gemini" in router.get_available_providers():
        return router.get_provider("gemini").client

    # If only Ollama available, return None (triggers mock mode in legacy code)
    return None

def get_model_name():
    """DEPRECATED: Use router configuration instead."""
    warnings.warn(
        "get_model_name() is deprecated. Use get_router().get_provider(name).model_name",
        DeprecationWarning,
        stacklevel=2
    )
    router = get_router()
    # Return first available provider's model
    providers = router.get_available_providers()
    if providers:
        return router.get_provider(providers[0]).model_name
    return "mock"
```

### 5.3 Example Agent Migration: Critic

**Before** (tightly coupled):
```python
# src/madspark/agents/critic.py
from google import genai
from google.genai import types
from madspark.agents.genai_client import get_genai_client, get_model_name
from madspark.schemas.adapters import pydantic_to_genai_schema

critic_client = get_genai_client()
model_name = get_model_name()
_CRITIC_GENAI_SCHEMA = pydantic_to_genai_schema(CriticEvaluations)

def evaluate_ideas(ideas, topic, context, temperature=0.7):
    if critic_client is None:
        return mock_critic_response(ideas)

    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=_CRITIC_GENAI_SCHEMA,
        system_instruction=CRITIC_SYSTEM_INSTRUCTION
    )

    prompt = build_critic_prompt(ideas, topic, context)
    response = critic_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config
    )

    return response.text
```

**After** (provider-agnostic):
```python
# src/madspark/agents/critic.py
from madspark.llm.router import get_router
from madspark.schemas.evaluation import CriticEvaluations

def evaluate_ideas(
    ideas: list,
    topic: str,
    context: str,
    temperature: float = 0.0,
    provider_override: str = None
) -> tuple[list, dict]:
    """
    Evaluate ideas using multi-provider LLM system.

    Args:
        ideas: List of ideas to evaluate
        topic: Topic/theme of evaluation
        context: Additional context
        temperature: Generation temperature
        provider_override: Force specific provider (developer only)

    Returns:
        tuple: (list of CriticEvaluation objects, response metadata)
    """
    router = get_router()

    prompt = build_critic_prompt(ideas, topic, context)

    validated_evaluations, response, provider_used = router.generate_structured(
        prompt=prompt,
        schema=CriticEvaluations,
        system_instruction=CRITIC_SYSTEM_INSTRUCTION,
        temperature=temperature,
        force_provider=provider_override,
        request_type="evaluation"
    )

    # Return validated Pydantic objects
    return validated_evaluations.root, {
        "provider": provider_used,
        "model": response.model,
        "tokens": response.tokens_used,
        "latency_ms": response.latency_ms,
        "cost": response.cost,
        "cached": response.cached
    }
```

### 5.4 Migration Checklist per Agent

For each agent:
- [ ] Import `get_router()` instead of `get_genai_client()`
- [ ] Remove direct `google.genai` imports
- [ ] Use router's `generate_structured()` method
- [ ] Remove mock mode checks (router handles this)
- [ ] Add `provider_override` parameter
- [ ] Add `request_type` for token budgeting
- [ ] Return response metadata
- [ ] Update unit tests to mock router
- [ ] Test with Ollama locally
- [ ] Verify Gemini fallback works

### 5.5 Testing Strategy Changes

**Old** (mock everything):
```python
@patch('madspark.agents.critic.critic_client')
def test_evaluate_ideas(mock_client):
    mock_client.models.generate_content.return_value = ...
```

**New** (use Ollama):
```python
# Integration test with real Ollama
def test_evaluate_ideas_integration():
    router = get_router()
    if "ollama" not in router.get_available_providers():
        pytest.skip("Ollama not available")

    result, metadata = evaluate_ideas(
        ideas=test_ideas,
        topic="test",
        context="test",
        provider_override="ollama"  # Force Ollama
    )

    assert len(result) == len(test_ideas)
    assert metadata["provider"] == "ollama"

# Unit test with mock router
@patch('madspark.agents.critic.get_router')
def test_evaluate_ideas_unit(mock_get_router):
    mock_router = Mock()
    mock_router.generate_structured.return_value = (
        CriticEvaluations(...),
        LLMResponse(...),
        "ollama"
    )
    mock_get_router.return_value = mock_router

    result, metadata = evaluate_ideas(...)
    assert ...
```

### 5.6 Phase 5 Verification Checklist

- [ ] Backward compatibility wrapper works
- [ ] Critic agent migrated and tested
- [ ] Advocate agent migrated and tested
- [ ] Skeptic agent migrated and tested
- [ ] IdeaGenerator migrated and tested
- [ ] LogicalInferenceEngine migrated and tested
- [ ] StructuredIdeaGenerator migrated and tested
- [ ] EnhancedReasoning migrated and tested
- [ ] All agents work with Ollama
- [ ] Fallback to Gemini works
- [ ] Deprecated `genai_client.py` marked
- [ ] CI tests updated
- [ ] Documentation updated

---

## Phase 6: Integration Testing & Benchmarking (~2-3 hours)

**PR Milestone**: Final PR with integration tests, benchmarks, and documentation updates.

### 6.1 End-to-End Tests

```python
# tests/test_ollama_integration.py

@pytest.mark.integration
@pytest.mark.skipif(not ollama_available(), reason="Ollama not running")
class TestOllamaIntegration:
    def test_full_workflow_with_ollama(self):
        """Run complete MadSpark workflow with Ollama."""
        from madspark.core.coordinator import Coordinator

        coordinator = Coordinator(
            topic="Sustainable urban farming",
            context="Focus on vertical farming in cities",
            num_candidates=3
        )

        # Force Ollama
        results = coordinator.run_workflow(provider_override="ollama")

        assert len(results["ideas"]) >= 3
        assert "evaluations" in results
        assert results["metadata"]["provider"] == "ollama"

    def test_pdf_input_uses_gemini(self):
        """PDF input should use Gemini for extraction."""
        # This would require a test PDF
        pass

    def test_fallback_on_ollama_failure(self):
        """Test Gemini fallback when Ollama fails."""
        # Mock Ollama failure
        pass
```

### 6.2 Performance Benchmarking

**File**: `tools/benchmark/benchmark_providers.py`

```python
import time
from madspark.llm.router import get_router
from madspark.schemas.evaluation import CriticEvaluations

def benchmark_providers():
    """Compare provider performance."""
    router = get_router()

    test_prompt = "Evaluate: AI-powered recycling sorting system"

    results = {}

    for provider_name in router.get_available_providers():
        times = []
        tokens = []

        for i in range(5):
            start = time.time()
            _, response, _ = router.generate_structured(
                prompt=test_prompt,
                schema=CriticEvaluations,
                force_provider=provider_name,
                use_cache=False  # Don't cache for benchmark
            )
            times.append((time.time() - start) * 1000)
            tokens.append(response.tokens_used)

        results[provider_name] = {
            "avg_latency_ms": sum(times) / len(times),
            "avg_tokens": sum(tokens) / len(tokens),
            "cost_per_request": sum(tokens) * router.get_provider(provider_name).get_cost_per_token() / len(tokens)
        }

    print("=== Provider Benchmark Results ===")
    for provider, data in results.items():
        print(f"\n{provider}:")
        print(f"  Avg Latency: {data['avg_latency_ms']:.0f}ms")
        print(f"  Avg Tokens: {data['avg_tokens']:.0f}")
        print(f"  Cost/Request: ${data['cost_per_request']:.6f}")

if __name__ == "__main__":
    benchmark_providers()
```

### 6.3 Phase 6 Verification Checklist

- [ ] Full workflow works with Ollama
- [ ] Full workflow works with Gemini
- [ ] Fallback scenarios tested
- [ ] Cache effectiveness measured
- [ ] Performance benchmarks documented
- [ ] Memory usage acceptable
- [ ] No regressions in existing functionality

---

## Phase 7: Web API Integration (~2-3 hours)

**PR Milestone**: Create PR with web backend integration, Docker Ollama service, and API tests.

### 7.1 Backend Configuration Update

The web backend automatically uses the new router through core module imports. No code changes needed for basic functionality.

**File**: `web/backend/.env.example` (update)

```bash
# LLM Provider Configuration
MADSPARK_LLM_PROVIDER=auto
MADSPARK_MODEL_TIER=fast
MADSPARK_FALLBACK_ENABLED=true
MADSPARK_CACHE_ENABLED=true
MADSPARK_CACHE_DIR=/app/.cache/llm

# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_FAST=gemma3:4b-it-qat
OLLAMA_MODEL_BALANCED=gemma3:12b-it-qat

# Gemini Settings (for fallback and PDF/URL)
GOOGLE_API_KEY=your_key_here
GOOGLE_GENAI_MODEL=gemini-2.5-flash
```

### 7.2 Docker Compose with Ollama Service (Optional)

**File**: `web/docker-compose.yml` (add Ollama service)

```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      - MADSPARK_LLM_PROVIDER=auto
      - MADSPARK_MODEL_TIER=fast
      - OLLAMA_HOST=http://ollama:11434
      - MADSPARK_CACHE_DIR=/app/.cache/llm
    volumes:
      - cache_data:/app/.cache
    depends_on:
      - ollama

  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # Pull models on startup (optional)
    # command: >
    #   sh -c "ollama serve &
    #          sleep 5 &&
    #          ollama pull gemma3:4b-it-qat &&
    #          wait"

volumes:
  ollama_data:
  cache_data:
```

**Note**: For local development, you can run Ollama on host machine and set `OLLAMA_HOST=http://host.docker.internal:11434`.

### 7.3 Admin Metrics Endpoint (Optional)

**File**: `web/backend/routes/admin.py` (new)

```python
from fastapi import APIRouter, HTTPException, Depends
from madspark.llm.router import get_router
from madspark.llm.cache import get_cache, DISKCACHE_AVAILABLE

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/llm/metrics")
async def get_llm_metrics():
    """
    Get LLM provider usage metrics.

    Developer/admin only endpoint for monitoring.
    """
    llm_router = get_router()
    return llm_router.get_metrics()

@router.get("/llm/providers")
async def get_available_providers():
    """Get list of available LLM providers."""
    llm_router = get_router()
    return {
        "providers": llm_router.get_available_providers(),
        "primary": "ollama" if "ollama" in llm_router.get_available_providers() else "gemini"
    }

@router.post("/cache/clear")
async def clear_llm_cache():
    """Clear LLM response cache."""
    if not DISKCACHE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cache not available")

    cache = get_cache()
    cache.clear()
    return {"status": "cleared", "message": "LLM cache cleared successfully"}

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    if not DISKCACHE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cache not available")

    cache = get_cache()
    return cache.stats()
```

**Register in main.py**:
```python
from routes.admin import router as admin_router
app.include_router(admin_router)
```

### 7.4 Web API Tests

**File**: `web/backend/tests/test_llm_integration.py`

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from main import app

client = TestClient(app)


class TestWebAPIWithLLMRouter:
    """Test web API endpoints with new LLM router."""

    @patch('madspark.llm.router.get_router')
    def test_brainstorm_uses_router(self, mock_get_router):
        """Brainstorm endpoint should use LLM router."""
        mock_router = Mock()
        mock_get_router.return_value = mock_router

        # The actual endpoint implementation will use the router
        # through coordinator which uses agents
        response = client.post("/api/brainstorm", json={
            "topic": "AI recycling",
            "context": "environmental sustainability"
        })

        # Router should be called through coordinator
        assert response.status_code in [200, 503]  # 503 if Ollama not available

    def test_admin_metrics_endpoint(self):
        """Admin metrics endpoint should return LLM stats."""
        response = client.get("/api/admin/llm/metrics")

        if response.status_code == 200:
            data = response.json()
            assert "total_requests" in data
            assert "cache_hits" in data

    def test_admin_providers_endpoint(self):
        """Providers endpoint should list available providers."""
        response = client.get("/api/admin/llm/providers")

        if response.status_code == 200:
            data = response.json()
            assert "providers" in data
            assert isinstance(data["providers"], list)

    def test_cache_stats_endpoint(self):
        """Cache stats endpoint should return cache info."""
        response = client.get("/api/admin/cache/stats")

        if response.status_code == 200:
            data = response.json()
            assert "size" in data
            assert "enabled" in data


@pytest.mark.integration
class TestWebAPIIntegration:
    """Integration tests with actual Ollama (requires running server)."""

    @pytest.mark.skipif(
        not _ollama_available(),
        reason="Ollama not running"
    )
    def test_full_brainstorm_workflow(self):
        """Test complete brainstorm workflow through web API."""
        response = client.post("/api/brainstorm", json={
            "topic": "Sustainable packaging",
            "context": "reduce plastic waste",
            "num_ideas": 3
        })

        assert response.status_code == 200
        data = response.json()
        assert "ideas" in data
        assert len(data["ideas"]) >= 3


def _ollama_available():
    """Check if Ollama is running."""
    try:
        import ollama
        ollama.Client().list()
        return True
    except Exception:
        return False
```

### 7.5 Frontend Considerations

**No frontend code changes required**. The frontend continues to:
- Call same REST API endpoints
- Receive same response format (Pydantic models unchanged)
- Display results identically

**What changes (transparent to frontend)**:
- Response latency may increase (3-8s with Ollama vs 0.5-1.5s with Gemini)
- Cost reduced to $0 for most requests
- PDF/URL uploads still work (routed to Gemini automatically)

**Optional frontend enhancements (future)**:
- Show provider info in response metadata
- Display cache hit indicator
- Admin dashboard for metrics

### 7.6 Testing Web Interface Manually

```bash
# Option 1: Local Ollama + Docker backend
ollama serve  # Terminal 1
cd web && docker compose up  # Terminal 2
# Frontend at http://localhost:3000

# Option 2: Full Docker stack (with Ollama container)
cd web && docker compose up
# Note: First startup pulls models, may take time

# Option 3: Local development (no Docker)
ollama serve  # Terminal 1
cd web/backend && uvicorn main:app --reload  # Terminal 2
cd web/frontend && npm start  # Terminal 3
```

**Test scenarios**:
1. Text-only brainstorm → Uses Ollama
2. File upload (PDF) → Uses Gemini for extraction, Ollama for workflow
3. URL input → Uses Gemini for fetching, Ollama for workflow
4. Check admin metrics endpoint → `/api/admin/llm/metrics`
5. Verify cache behavior → Same request twice should be faster

### 7.7 Phase 7 Verification Checklist

- [ ] Backend environment variables configured
- [ ] Docker compose updated with Ollama service (optional)
- [ ] Admin metrics endpoint functional
- [ ] Cache stats endpoint functional
- [ ] Web API tests pass
- [ ] Brainstorm endpoint uses Ollama by default
- [ ] PDF/URL uploads route to Gemini correctly
- [ ] Frontend displays results correctly (no changes needed)
- [ ] Manual testing of web interface complete
- [ ] Documentation for web deployment updated

---

## Post-Migration Tasks

### Documentation Updates
- [ ] Update README with Ollama setup instructions
- [ ] Add troubleshooting guide for Ollama
- [ ] Document hidden developer flags
- [ ] Update architecture diagrams
- [ ] Add cache management guide

### Cleanup
- [ ] Remove deprecated `genai_client.py` (or keep with deprecation warnings)
- [ ] Clean up old mock mode code where appropriate
- [ ] Update `.gitignore` to exclude cache directory
- [ ] Update CI to install Ollama (optional, for integration tests)

### Future Enhancements
- [ ] Add more providers (Claude, OpenAI) using same pattern
- [ ] Implement provider-specific prompt optimization
- [ ] Add cost tracking dashboard
- [ ] Implement request queuing for batch operations
- [ ] Add premium user authorization hooks

---

## Risk Mitigation

### Risk 1: Ollama Server Not Running
**Mitigation**: Clear error messages, automatic Gemini fallback

### Risk 2: Model Not Pulled
**Mitigation**: Health check includes model availability verification

### Risk 3: Slow Ollama Performance
**Mitigation**: Token budgets, 4B as default, quality tier option

### Risk 4: Schema Incompatibility
**Mitigation**: Thorough testing with all existing Pydantic schemas

### Risk 5: Cache Corruption
**Mitigation**: Graceful degradation, automatic cache invalidation

---

## Success Criteria

1. **Functional**: All agents work with Ollama primary provider
2. **Performance**: Workflow completes in <5 minutes (4B tier)
3. **Cost**: 90%+ reduction in API costs for development
4. **Reliability**: Automatic fallback to Gemini on failure
5. **Compatibility**: All existing tests pass
6. **Developer Experience**: Easy model tier switching

---

## Quick Reference: One-Line Configuration Changes

```python
# In config.py or .env

# Change default model tier (affects all Ollama calls)
MADSPARK_MODEL_TIER=balanced  # fast -> balanced -> quality

# Force Gemini for everything (paid, fastest)
MADSPARK_LLM_PROVIDER=gemini

# Disable fallback (fail if primary fails)
MADSPARK_FALLBACK_ENABLED=false

# Disable caching
MADSPARK_CACHE_ENABLED=false

# Change Ollama model directly
OLLAMA_MODEL_FAST=gemma3:4b-it-qat
OLLAMA_MODEL_BALANCED=gemma3:12b-it-qat
```

---

## PR Milestone Summary

| Phase | Duration | PR Scope |
|-------|----------|----------|
| Phase 0 | ~15 min | No PR (prerequisites) |
| Phase 1 | ~4 hours | Package structure, base classes, provider implementations, unit tests |
| Phase 2 | ~3 hours | Cache layer, integration with router |
| Phase 3 | ~3 hours | Complete router, fallback mechanism, metrics |
| Phase 4 | ~3 hours | CLI integration, developer flags |
| Phase 5 | ~6-8 hours | All agents migrated, test updates |
| Phase 6 | ~2-3 hours | Integration tests, benchmarks, documentation |
| Phase 7 | ~2-3 hours | Web API integration, Docker Ollama, admin endpoints |

**Total: 7 PRs over 2-3 days (~20-25 hours of work)**

---

## Next Steps

1. Review this plan thoroughly
2. Set up development branch: `git checkout -b feature/ollama-multi-llm`
3. Start Phase 0 (prerequisites)
4. Execute phases sequentially
5. Create PR after each phase completion (see milestone summary above)
6. Merge after CI passes and verification checklist complete

**Estimated Total Duration**: 2-3 days (20-25 hours of focused work)
