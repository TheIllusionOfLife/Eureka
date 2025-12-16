"""
Ollama LLM Provider.

Local inference using Ollama with Gemma3 models.
Primary provider for cost-effective inference.
"""

import logging
import threading
import time
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel, ValidationError

from madspark.llm.base import LLMProvider
from madspark.llm.response import LLMResponse
from madspark.llm.exceptions import ProviderUnavailableError, SchemaValidationError
from madspark.llm.config import get_config

try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None  # type: ignore

logger = logging.getLogger(__name__)


def _simplify_schema_for_ollama(schema: dict) -> dict:
    """
    Simplify a Pydantic JSON schema for Ollama compatibility.

    Ollama's schema parser can't handle complex Pydantic metadata like:
    - $defs (nested model definitions)
    - description, title, examples fields
    - anyOf/oneOf for optional fields

    This function flattens and simplifies the schema.
    """

    def simplify_property(prop: dict) -> dict:
        """Recursively simplify a property definition."""
        result = {}

        # Handle anyOf (optional fields) - take the first non-null type
        if "anyOf" in prop:
            for option in prop["anyOf"]:
                if option.get("type") != "null":
                    return simplify_property(option)
            return {"type": "string"}  # fallback

        # Copy basic type info
        if "type" in prop:
            result["type"] = prop["type"]

        # Handle arrays
        if prop.get("type") == "array" and "items" in prop:
            result["items"] = simplify_property(prop["items"])

        # Handle nested objects
        if prop.get("type") == "object" and "properties" in prop:
            result["properties"] = {
                k: simplify_property(v) for k, v in prop["properties"].items()
            }
            if "required" in prop:
                result["required"] = prop["required"]

        # Handle $ref - resolve from $defs
        if "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            return {"$ref": f"#/$defs/{ref_name}"}

        return result

    def resolve_refs(obj: dict, defs: dict) -> dict:
        """Resolve $ref references to their definitions."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_name = obj["$ref"].split("/")[-1]
                if ref_name in defs:
                    return resolve_refs(defs[ref_name], defs)
                return obj
            return {k: resolve_refs(v, defs) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item, defs) for item in obj]
        return obj

    # Extract $defs for reference resolution
    defs = {}
    if "$defs" in schema:
        for name, definition in schema["$defs"].items():
            simplified_def = {}
            if "type" in definition:
                simplified_def["type"] = definition["type"]
            if "properties" in definition:
                simplified_def["properties"] = {
                    k: simplify_property(v)
                    for k, v in definition["properties"].items()
                }
            if "required" in definition:
                simplified_def["required"] = definition["required"]
            defs[name] = simplified_def

    # Build simplified schema
    result = {}

    if "type" in schema:
        result["type"] = schema["type"]

    if "items" in schema:
        result["items"] = simplify_property(schema["items"])

    if "properties" in schema:
        result["properties"] = {
            k: simplify_property(v) for k, v in schema["properties"].items()
        }

    if "required" in schema:
        result["required"] = schema["required"]

    # Include simplified $defs if needed
    if defs:
        result["$defs"] = defs

    # Resolve all refs
    result = resolve_refs(result, defs)

    # Remove $defs after resolution (Ollama doesn't need them)
    if "$defs" in result:
        del result["$defs"]

    return result


class OllamaProvider(LLMProvider):
    """
    Ollama-based LLM provider using local models.

    Primary provider for cost-effective inference.
    Supports text and image inputs (gemma3 multimodal).

    Usage:
        provider = OllamaProvider()
        validated, response = provider.generate_structured(
            prompt="Rate this idea",
            schema=MySchema
        )
    """

    def __init__(
        self, model: Optional[str] = None, host: Optional[str] = None
    ) -> None:
        """
        Initialize Ollama provider.

        Args:
            model: Model to use (default from config)
            host: Ollama server host (default from config)

        Raises:
            ImportError: If ollama package not installed
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "ollama package not installed. Run: uv pip install ollama"
            )

        config = get_config()
        self._model = model or config.get_ollama_model()
        self._host = host or config.ollama_host
        self._client = None

        # Health check caching with TTL (30 seconds)
        self._last_health_check: Optional[bool] = None
        self._last_health_check_time: float = 0.0
        self._health_check_ttl: float = 30.0  # seconds
        self._health_check_lock = threading.Lock()  # Thread-safe health check

    @property
    def client(self):
        """Lazy initialization of Ollama client."""
        if self._client is None:
            self._client = ollama.Client(host=self._host)
        return self._client

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "ollama"

    @property
    def model_name(self) -> str:
        """Return model being used."""
        return self._model

    @property
    def supports_multimodal(self) -> bool:
        """Check if model supports images."""
        # gemma3 models support images
        return "gemma3" in self._model

    def health_check(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama server is running and model is available.

        Uses TTL-based caching (30 seconds) to avoid repeated network calls.
        Thread-safe with lock to prevent race conditions.

        Args:
            force_refresh: If True, bypass cache and check server directly

        Returns:
            True if server is up and model is pulled
        """
        # Thread-safe health check with lock
        with self._health_check_lock:
            # Check cache first (unless force refresh requested)
            if (
                not force_refresh
                and self._last_health_check is not None
                and (time.time() - self._last_health_check_time) < self._health_check_ttl
            ):
                return self._last_health_check

            try:
                models = self.client.list()
                # Handle both dict and Model object responses
                # Support both "model" and "name" keys (HTTP API uses "name", some responses use "model")
                model_names = [
                    (m.get("model") or m.get("name", "")) if isinstance(m, dict) else getattr(m, "model", "")
                    for m in models.get("models", [])
                ]
                # Check if model is available
                # Strict matching: exact match or model matches without tag
                # e.g., "gemma3:4b" matches "gemma3:4b" or "gemma3"
                result = False
                for name in model_names:
                    # Exact match (highest priority)
                    if name == self._model:
                        result = True
                        break
                    # Precise prefix matching: pulled model must start with requested model
                    # followed by a delimiter (-, :, or end of string)
                    # e.g., requested "gemma3:4b" matches pulled "gemma3:4b"
                    # but "gemma3:4b" does NOT match "gemma3:12b" or "gemma3:4bx"
                    if name.startswith(f"{self._model}") and (
                        len(name) == len(self._model)
                        or name[len(self._model)] in ("-", ":", "_")
                    ):
                        result = True
                        break

                # Cache the result
                self._last_health_check = result
                self._last_health_check_time = time.time()
                return result
            except Exception as e:
                logger.warning(f"Ollama health check failed: {e}")
                # Cache failure for a short time to avoid hammering
                self._last_health_check = False
                self._last_health_check_time = time.time()
                return False

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        images: Optional[list[Union[str, Path]]] = None,
    ) -> LLMResponse:
        """
        Generate unstructured text completion.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            images: Optional image paths for multimodal

        Returns:
            LLMResponse with text and metadata

        Raises:
            ProviderUnavailableError: If Ollama not available
        """
        if not self.health_check():
            raise ProviderUnavailableError(
                f"Ollama not available. Is 'ollama serve' running? "
                f"Is model '{self._model}' pulled?"
            )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        user_message: dict[str, Any] = {"role": "user", "content": prompt}
        if images:
            # Validate image paths exist before API call
            validated_images = []
            for img in images:
                img_path = Path(img)
                if not img_path.exists():
                    logger.warning(f"Image file not found: {img_path}")
                    raise FileNotFoundError(f"Image file not found: {img_path}")
                if not img_path.is_file():
                    logger.warning(f"Image path is not a file: {img_path}")
                    raise ValueError(f"Image path is not a file: {img_path}")
                validated_images.append(str(img_path))
            user_message["images"] = validated_images
        messages.append(user_message)

        options: dict[str, Any] = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        start = time.time()
        response = self.client.chat(model=self._model, messages=messages, options=options)
        latency = (time.time() - start) * 1000

        return LLMResponse(
            text=response.message.content,
            provider=self.provider_name,
            model=self._model,
            tokens_used=getattr(response, "eval_count", 0),
            latency_ms=latency,
            cost=0.0,  # Free!
        )

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,  # Default 0 for structured output
        images: Optional[list[Union[str, Path]]] = None,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        token_budget: Optional[int] = None,
    ) -> tuple[Any, LLMResponse]:
        """
        Generate structured output validated against Pydantic model.

        Uses Ollama's native JSON schema enforcement.

        Args:
            prompt: User prompt
            schema: Pydantic model for validation
            system_instruction: System instruction
            temperature: Sampling temperature (default 0 for determinism)
            images: Optional image paths
            files: Optional file paths (not supported by Ollama, ignored)
            urls: Optional URLs (not supported by Ollama, ignored)
            token_budget: Max tokens to generate

        Returns:
            tuple: (validated_pydantic_object, response_metadata)

        Raises:
            ProviderUnavailableError: If Ollama not available
            SchemaValidationError: If output doesn't match schema
        """
        # Note: files and urls are not supported by Ollama, included for interface compatibility
        if files or urls:
            logger.warning(
                "Ollama does not support files/urls parameters. "
                "Consider using Gemini provider for PDF/URL processing. "
                f"Ignoring: files={files}, urls={urls}"
            )
        if not self.health_check():
            raise ProviderUnavailableError(f"Ollama not available. Model: {self._model}")

        # Get JSON schema from Pydantic model and simplify for Ollama
        raw_schema = schema.model_json_schema()
        json_schema = _simplify_schema_for_ollama(raw_schema)
        logger.debug(f"Simplified schema for Ollama: {json_schema}")

        # Determine token budget
        if token_budget is None:
            # Estimate based on schema complexity
            token_budget = self._estimate_token_budget(json_schema)

        # Best practice: Include schema hint in prompt for grounding
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Respond with valid JSON matching the schema. "
            f"Keep each field concise and focused on key points."
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        user_message: dict[str, Any] = {"role": "user", "content": enhanced_prompt}
        if images:
            # Validate image paths exist before API call
            validated_images = []
            for img in images:
                img_path = Path(img)
                if not img_path.exists():
                    logger.warning(f"Image file not found: {img_path}")
                    raise FileNotFoundError(f"Image file not found: {img_path}")
                if not img_path.is_file():
                    logger.warning(f"Image path is not a file: {img_path}")
                    raise ValueError(f"Image path is not a file: {img_path}")
                validated_images.append(str(img_path))
            user_message["images"] = validated_images
        messages.append(user_message)

        start = time.time()
        try:
            response = self.client.chat(
                model=self._model,
                messages=messages,
                format=json_schema,  # Ollama's native schema enforcement
                options={"temperature": temperature, "num_predict": token_budget},
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
            raise SchemaValidationError(f"Ollama output doesn't match schema: {e}")

        tokens_used = getattr(response, "eval_count", None)
        if tokens_used is None:
            logger.warning("Ollama response missing eval_count, defaulting to 0")
            tokens_used = 0

        llm_response = LLMResponse(
            text=response.message.content,
            provider=self.provider_name,
            model=self._model,
            tokens_used=tokens_used,
            latency_ms=latency,
            cost=0.0,
        )

        logger.info(
            f"Ollama generated structured output in {latency:.0f}ms "
            f"({tokens_used} tokens)"
        )

        return validated, llm_response

    def _estimate_token_budget(self, schema: dict) -> int:
        """
        Estimate token budget based on schema complexity.

        Args:
            schema: JSON schema dict

        Returns:
            Recommended max tokens
        """

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
                        count += count_fields(items) * 5  # Increased for array items

            return count

        # Check if this is an array schema (like GeneratedIdeas, AdvocacyBatchResponse)
        is_array = schema.get("type") == "array"

        if is_array:
            # For array schemas (RootModel), count fields in the items schema
            items_schema = schema.get("items", {})
            field_count = count_fields(items_schema)

            # Derive multiplier from schema constraints with sane defaults
            # maxItems is more reliable as it indicates expected array size
            max_items = schema.get("maxItems")
            min_items = schema.get("minItems")

            if max_items is not None:
                # Use maxItems as upper bound, capped at 10 for safety
                array_multiplier = min(max_items, 10)
            elif min_items is not None:
                # Assume typical response is 2x minItems, capped at 10
                array_multiplier = min(min_items * 2, 10)
            else:
                # Default for batch operations (typically 3-5 items)
                array_multiplier = 5
        else:
            field_count = count_fields(schema)
            array_multiplier = 1

        # Base budget + per-field allocation
        # Each field needs ~200-400 tokens for content (generous for Japanese)
        # Batch responses with lists of strings need more tokens per field
        budget = 1000 + (field_count * 400 * array_multiplier)

        # Cap at gemma3 context-appropriate maximum (8k conservative for output)
        # This prevents excessive cache usage and stays within Ollama limits
        # For very large batches, rely on pagination or direct API
        return min(budget, 8000)

    def get_cost_per_token(self) -> float:
        """Local inference is free."""
        return 0.0
