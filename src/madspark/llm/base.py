"""
Abstract Base Class for LLM Providers.

Defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type, Union
from pathlib import Path
from pydantic import BaseModel

from madspark.llm.response import LLMResponse


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Each provider implementation must:
    - Support structured output generation with Pydantic models
    - Provide health checking capabilities
    - Report cost per token (0 for local providers)
    - Indicate multimodal support capabilities
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate unstructured text completion.

        Args:
            prompt: The user prompt
            system_instruction: System-level instruction
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated text and metadata
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_instruction: str = "",
        temperature: float = 0.0,
        images: Optional[list[Union[str, Path]]] = None,
        files: Optional[list[Path]] = None,
        urls: Optional[list[str]] = None,
        token_budget: Optional[int] = None,
        **kwargs: Any,
    ) -> tuple[Any, LLMResponse]:
        """
        Generate structured output validated against Pydantic model.

        Args:
            prompt: The user prompt
            schema: Pydantic model class for validation
            system_instruction: System-level instruction
            temperature: Sampling temperature (default 0 for determinism)
            images: Optional list of image paths for multimodal input
            files: Optional list of file paths (PDF, documents) for context
            urls: Optional list of URLs to fetch for context
            token_budget: Optional maximum tokens for response
            **kwargs: Additional provider-specific arguments

        Returns:
            tuple: (validated_pydantic_object, response_metadata)

        Raises:
            SchemaValidationError: If output doesn't match schema
            ProviderUnavailableError: If provider is not accessible
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Unique identifier for this provider.

        Examples: 'ollama', 'gemini', 'mock'
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Model being used by this provider.

        Examples: 'gemma3:4b-it-qat', 'gemini-2.5-flash'
        """
        pass

    @property
    @abstractmethod
    def supports_multimodal(self) -> bool:
        """
        Whether provider supports images/PDFs/URLs as input.

        Returns:
            True if provider can process multimodal content
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify provider is available and functioning.

        Returns:
            True if provider is healthy and ready to serve requests
        """
        pass

    def get_cost_per_token(self) -> float:
        """
        Return cost per token in USD.

        Returns:
            Cost per token (0.0 for local providers like Ollama)
        """
        return 0.0

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimate for text.

        Simple heuristic: ~4 characters per token.

        Args:
            text: Input text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    @staticmethod
    def validate_temperature(temperature: float) -> float:
        """
        Validate and clamp temperature to valid range.

        Args:
            temperature: Sampling temperature value

        Returns:
            Validated temperature (clamped to [0.0, 2.0])

        Raises:
            ValueError: If temperature is not a valid number
        """
        if not isinstance(temperature, (int, float)):
            raise ValueError(f"Temperature must be a number, got {type(temperature)}")

        if temperature < 0.0:
            return 0.0
        elif temperature > 2.0:
            return 2.0
        return float(temperature)
