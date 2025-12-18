"""
Google Gemini LLM Provider.

Cloud-based inference using Gemini API.
Fallback provider and PDF/URL processor.
"""

import logging
import os
import threading
import time
import ipaddress
import socket
from typing import Any, Optional, Type, Union
from pathlib import Path
from urllib.parse import urlparse
from pydantic import BaseModel, SecretStr

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import ProviderUnavailableError, SchemaValidationError
from madspark.llm.config import get_config, LLMConfig

# Type alias for time.time() return value
TimeFloat = float

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None  # type: ignore
    types = None  # type: ignore

# Import existing adapters (reuse from Pydantic migration)
try:
    from madspark.schemas.adapters import (
        pydantic_to_genai_schema,
        genai_response_to_pydantic,
    )
except ImportError:
    pydantic_to_genai_schema = None  # type: ignore
    genai_response_to_pydantic = None  # type: ignore

logger = logging.getLogger(__name__)


def _is_private_ip(hostname: str) -> bool:
    """
    Check if hostname resolves to a private/internal IP address.

    Security: Prevents SSRF attacks by blocking access to internal networks.

    Args:
        hostname: DNS hostname or IP address

    Returns:
        True if hostname is private/internal, False otherwise
    """
    try:
        # Resolve hostname to IP
        ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_str)

        # Check for private, loopback, link-local, or reserved addresses
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        )
    except (socket.gaierror, ValueError):
        # If we can't resolve, treat as potentially dangerous
        logger.warning(f"Cannot resolve hostname: {hostname}")
        return True


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Used for:
    - PDF/URL processing (native Gemini support)
    - Fallback when Ollama fails
    - High-quality/fast inference (paid)
    - Developer comparison testing

    Usage:
        provider = GeminiProvider()
        validated, response = provider.generate_structured(
            prompt="Rate this idea",
            schema=MySchema
        )
    """

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None
    ) -> None:
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (default from env)
            model: Model name (default from config)

        Raises:
            ImportError: If google-genai not installed
            ProviderUnavailableError: If API key not set
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Run: uv pip install google-genai"
            )

        config = get_config()
        raw_api_key = api_key or config.gemini_api_key or os.getenv("GOOGLE_API_KEY")
        self._model = model or config.gemini_model
        self._client = None

        if not raw_api_key:
            raise ProviderUnavailableError(
                "GOOGLE_API_KEY not set. Required for Gemini provider."
            )

        # Store API key as SecretStr for memory safety (won't appear in repr/logs)
        self._api_key: SecretStr = SecretStr(raw_api_key)

        # Validate API key is not a placeholder (without modifying shared config)
        # Create temporary config with our API key for validation
        temp_config = LLMConfig(gemini_api_key=raw_api_key)
        if not temp_config.validate_api_key():
            logger.warning(
                "API key may be a placeholder. Gemini calls may fail. "
                "Set a valid GOOGLE_API_KEY in your environment."
            )

        # Health check caching with TTL (60 seconds - longer than Ollama since it costs quota)
        self._last_health_check: Optional[bool] = None
        self._last_health_check_time: TimeFloat = 0.0
        self._health_check_ttl: TimeFloat = 60.0  # seconds (longer than Ollama to save quota)
        self._health_check_lock = threading.Lock()  # Thread-safe health check

    @property
    def client(self):
        """Lazy initialization of Gemini client."""
        if self._client is None:
            # Client uses API key from parameter or environment
            # SecretStr.get_secret_value() retrieves the actual value
            self._client = genai.Client(api_key=self._api_key.get_secret_value())
        return self._client

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "gemini"

    @property
    def model_name(self) -> str:
        """Return model being used."""
        return self._model

    @property
    def supports_multimodal(self) -> bool:
        """Gemini supports full multimodal (PDF, URL, images)."""
        return True

    def health_check(self, force_refresh: bool = False) -> bool:
        """
        Check if Gemini API is accessible.

        Uses TTL-based caching (60 seconds) to avoid repeated API calls that consume quota.
        Thread-safe with lock to prevent race conditions.

        Args:
            force_refresh: If True, bypass cache and check API directly

        Returns:
            True if API is reachable
        """
        # Thread-safe health check with lock
        with self._health_check_lock:
            # Check cache first to avoid expensive API calls (unless force refresh)
            if (
                not force_refresh
                and self._last_health_check is not None
                and (time.time() - self._last_health_check_time) < self._health_check_ttl
            ):
                return self._last_health_check

            try:
                # Quick check - use iterator to avoid loading full list into memory
                result = next(iter(self.client.models.list()), None) is not None
            except Exception as e:
                logger.warning(f"Gemini health check failed: {e}")
                result = False

            # Cache the result
            self._last_health_check = result
            self._last_health_check_time = time.time()
            return result

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
    ) -> LLMResponse:
        """
        Generate unstructured text completion.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            files: Optional file paths (PDFs, images)
            urls: Optional URLs to fetch

        Returns:
            LLMResponse with text and metadata
        """
        config_dict: dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_dict["system_instruction"] = system_instruction
        if max_tokens:
            config_dict["max_output_tokens"] = max_tokens

        config = types.GenerateContentConfig(**config_dict)

        # Build content
        contents: list[Any] = []

        if files:
            for file_path in files:
                # Validate file path exists before API call
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    raise FileNotFoundError(f"File not found: {file_path}")
                if not file_path.is_file():
                    logger.warning(f"Path is not a file: {file_path}")
                    raise ValueError(f"Path is not a file: {file_path}")
                part = types.Part.from_file(str(file_path))
                contents.append(part)

        if urls:
            url_context = "\n".join([f"Reference: {url}" for url in urls])
            prompt = f"{url_context}\n\n{prompt}"

        contents.append(prompt)

        start = time.time()
        response = self.client.models.generate_content(
            model=self._model, contents=contents, config=config
        )
        latency = (time.time() - start) * 1000

        usage = getattr(response, "usage_metadata", None)
        tokens = usage.total_token_count if usage else 0

        return LLMResponse(
            text=response.text,
            provider=self.provider_name,
            model=self._model,
            tokens_used=tokens,
            latency_ms=latency,
            cost=tokens * self.get_cost_per_token(),
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,  # Default 0 for deterministic structured output
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        images: Optional[list[Union[str, Path]]] = None,  # For compatibility
        **kwargs,  # Accept extra args for compatibility
    ) -> tuple[Any, LLMResponse]:
        """
        Generate structured output with optional PDF/URL inputs.

        Args:
            prompt: User prompt
            schema: Pydantic model for validation
            system_instruction: System instruction
            temperature: Sampling temperature
            files: Optional file paths (PDFs, documents)
            urls: Optional URLs to fetch
            images: Optional image paths (for compatibility)
            **kwargs: Additional arguments (ignored)

        Returns:
            tuple: (validated_pydantic_object, response_metadata)

        Raises:
            SchemaValidationError: If output doesn't match schema
            ImportError: If schema adapters not available
        """
        # Log unknown kwargs at warning level to catch potential misconfigurations
        if kwargs:
            logger.warning(
                f"GeminiProvider.generate_structured() received unexpected kwargs: "
                f"{list(kwargs.keys())}. These will be ignored."
            )

        if pydantic_to_genai_schema is None:
            raise ImportError(
                "Schema adapters not available. Ensure madspark.schemas.adapters exists."
            )

        # Convert Pydantic to Gemini's schema format
        genai_schema = pydantic_to_genai_schema(schema)

        config_dict: dict[str, Any] = {
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": genai_schema,
        }
        if system_instruction:
            config_dict["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_dict)

        # Build content with optional files/URLs
        contents: list[Any] = []

        # Handle images (for compatibility with Ollama interface)
        if images:
            for img_path in images:
                path = Path(img_path)
                if not path.exists():
                    logger.warning(f"Image file not found: {path}")
                    raise FileNotFoundError(f"Image file not found: {path}")
                if not path.is_file():
                    logger.warning(f"Image path is not a file: {path}")
                    raise ValueError(f"Image path is not a file: {path}")
                contents.append(types.Part.from_file(str(path)))

        if files:
            for file_path in files:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    raise FileNotFoundError(f"File not found: {file_path}")
                if not file_path.is_file():
                    logger.warning(f"Path is not a file: {file_path}")
                    raise ValueError(f"Path is not a file: {file_path}")
                part = types.Part.from_file(str(file_path))
                contents.append(part)

        if urls:
            # Validate URL format and security before use
            for url in urls:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    raise ValueError(f"Invalid URL format: {url}")
                if parsed.scheme not in ("http", "https"):
                    raise ValueError(f"URL must use http or https scheme: {url}")
                # SSRF protection: block private/internal IP addresses
                if _is_private_ip(parsed.hostname or ""):
                    raise ValueError(
                        f"URL points to private/internal network (SSRF protection): {url}"
                    )
            url_context = "\n".join([f"Analyze this URL: {url}" for url in urls])
            prompt = f"{url_context}\n\n{prompt}"

        contents.append(prompt)

        start = time.time()
        response = self.client.models.generate_content(
            model=self._model, contents=contents, config=config
        )
        latency = (time.time() - start) * 1000

        # Validate with Pydantic
        try:
            validated = genai_response_to_pydantic(response.text, schema)
        except Exception as e:
            raise SchemaValidationError(f"Gemini output validation failed: {e}")

        usage = getattr(response, "usage_metadata", None)
        tokens = usage.total_token_count if usage else 0

        llm_response = LLMResponse(
            text=response.text,
            provider=self.provider_name,
            model=self._model,
            tokens_used=tokens,
            latency_ms=latency,
            cost=tokens * self.get_cost_per_token(),
        )

        logger.info(
            f"Gemini generated structured output in {latency:.0f}ms "
            f"({tokens} tokens, ${llm_response.cost:.6f})"
        )

        return validated, llm_response

    def extract_content_from_files(
        self, files: list[Path], urls: Optional[list[str]] = None
    ) -> str:
        """
        Extract text content from PDFs/URLs for handoff to Ollama.

        Used when user provides --file/--url but we want Ollama for workflow.

        Args:
            files: List of file paths to extract from
            urls: Optional URLs to fetch content from

        Returns:
            Extracted text content as string

        Raises:
            ProviderUnavailableError: If API call fails
        """
        extraction_prompt = (
            "Extract and summarize all text content from the provided documents. "
            "Maintain key information, structure, and important details. "
            "Output as plain text suitable for further analysis."
        )

        config = types.GenerateContentConfig(
            temperature=0.1,  # Low temp for faithful extraction
            system_instruction="You are a content extraction assistant. "
            "Extract text faithfully while preserving structure.",
        )

        contents: list[Any] = []
        for file_path in files:
            contents.append(types.Part.from_file(str(file_path)))

        if urls:
            url_context = "\n".join([f"Fetch content from: {url}" for url in urls])
            extraction_prompt = f"{url_context}\n\n{extraction_prompt}"

        contents.append(extraction_prompt)

        try:
            response = self.client.models.generate_content(
                model=self._model, contents=contents, config=config
            )

            logger.info(f"Extracted {len(response.text)} chars from {len(files)} files")
            return response.text
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            raise ProviderUnavailableError(
                f"Failed to extract content from files: {e}"
            ) from e

    def get_cost_per_token(self) -> float:
        """
        Get cost per token based on model.

        Returns:
            Cost per token in USD (approximate average of input/output)
        """
        # Model-specific pricing (average of input + output costs)
        model_costs = {
            # Gemini 3 Flash: $0.50 input + $3.00 output = $1.75 average per 1M
            "gemini-3-flash-preview": 0.00000175,
            # Gemini 3 Pro: $2.00 input + $12.00 output = $7.00 average per 1M
            "gemini-3-pro-preview": 0.000007,
            # Gemini 2.5 Flash: $0.075 input + $0.30 output = $0.1875 average per 1M
            "gemini-2.5-flash": 0.0000001875,
            # Legacy defaults
            "gemini-1.5-flash": 0.0000001875,
            "gemini-1.5-pro": 0.000003125,
        }
        return model_costs.get(self._model, 0.00000175)  # Default to Gemini 3 Flash
