"""Structured output implementation for idea generation.

This module provides enhanced idea generation using Gemini's structured output
capabilities to ensure clean, meta-commentary-free responses.
"""
import json
import logging
from pathlib import Path
from typing import Any, Optional, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..llm.router import LLMRouter

from ..utils.constants import DEFAULT_GOOGLE_GENAI_MODEL
from ..utils.multimodal_input import build_prompt_with_multimodal
from madspark.schemas.generation import ImprovementResponse
from madspark.schemas.adapters import pydantic_to_genai_schema, genai_response_to_pydantic

# Optional import for Google GenAI - graceful fallback for CI/testing
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GENAI_AVAILABLE = False

from madspark.utils.constants import IDEA_GENERATOR_SYSTEM_INSTRUCTION

# Convert Pydantic model to GenAI schema format at module level (cached)
_IMPROVEMENT_RESPONSE_GENAI_SCHEMA = pydantic_to_genai_schema(ImprovementResponse)

# Optional LLM Router import
try:
    from madspark.llm import get_router
    from madspark.llm.exceptions import AllProvidersFailedError
    from madspark.llm.config import get_config as get_llm_config
    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLM_ROUTER_AVAILABLE = False
    get_router = None  # type: ignore
    AllProvidersFailedError = Exception  # type: ignore
    get_llm_config = None  # type: ignore


def _should_use_router() -> bool:
    """
    Check if router should be used based on configuration.

    Returns True if:
    - LLM Router is available
    - User explicitly configured provider via env var (e.g., --provider flag)
    - Provider is not set to 'auto' (which would just use Gemini anyway)
    """
    if not LLM_ROUTER_AVAILABLE or get_llm_config is None:
        return False

    import os
    # Check if user explicitly set provider (indicating they want router control)
    explicit_provider = os.getenv("MADSPARK_LLM_PROVIDER")

    # Also check for other router-related flags
    cache_disabled = os.getenv("MADSPARK_CACHE_ENABLED") == "false"
    fallback_disabled = os.getenv("MADSPARK_FALLBACK_ENABLED") == "false"
    model_tier_set = os.getenv("MADSPARK_MODEL_TIER") is not None

    # Use router if any router-related flag was explicitly set
    return bool(explicit_provider or cache_disabled or fallback_disabled or model_tier_set)


def improve_idea_structured(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    topic: str,
    context: str,
    logical_inference: Optional[str] = None,
    temperature: float = 0.9,
    genai_client: Optional[Any] = None,
    model_name: str = DEFAULT_GOOGLE_GENAI_MODEL,
    multimodal_files: Optional[List[Union[str, Path]]] = None,
    multimodal_urls: Optional[List[str]] = None,
    use_router: bool = True,
    router: Optional["LLMRouter"] = None
) -> str:
    """Improves an idea using structured output for clean responses.

    This function uses Gemini's structured output capabilities to ensure
    the response contains only the improved idea without meta-commentary.

    When use_router=True and LLM Router is available, routes through the
    multi-provider abstraction layer for automatic fallback and caching.

    Args:
        original_idea: The original idea to improve
        critique: The critic's evaluation
        advocacy_points: The advocate's bullet points
        skeptic_points: The skeptic's concerns
        topic: The topic for idea improvement
        context: The original context for improvement
        logical_inference: Optional logical analysis
        temperature: Controls randomness (0.0-1.0)
        genai_client: Optional GenAI client instance (bypasses router)
        model_name: Model to use for generation
        multimodal_files: Optional files for multimodal input
        multimodal_urls: Optional URLs for multimodal input
        use_router: Whether to use LLM Router for provider abstraction
        router: Optional LLMRouter instance for request-scoped routing (Phase 2).
            If provided, uses this router instead of calling get_router().
            Enables thread-safe concurrent operation in backend environments.

    Returns:
        The improved idea text without any meta-commentary

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If API is not configured
    """
    # Import validation helper from idea_generator to maintain DRY principle
    from madspark.agents.idea_generator import _validate_non_empty_string

    # Validate inputs using the same logic as the main module
    _validate_non_empty_string(original_idea, 'original_idea')
    _validate_non_empty_string(critique, 'critique')
    _validate_non_empty_string(advocacy_points, 'advocacy_points')
    _validate_non_empty_string(skeptic_points, 'skeptic_points')
    _validate_non_empty_string(topic, 'topic')
    _validate_non_empty_string(context, 'context')

    # Build focused prompt
    text_prompt = f"""Topic: {topic}
Context: {context}

Original Idea: {original_idea}

Professional Evaluation: {critique}

Key Strengths: {advocacy_points}

Critical Concerns: {skeptic_points}"""

    # Add logical inference if provided
    if logical_inference:
        text_prompt += f"\n\nLogical Analysis: {logical_inference}"

    text_prompt += """

Task: Generate an improved version that:
1. Addresses ALL evaluation criteria
2. Maintains identified strengths
3. Provides solutions for each concern
4. Remains bold and creative

Write ONLY the improved idea. No introductions, no meta-commentary."""

    # Process multi-modal inputs if provided
    contents = build_prompt_with_multimodal(
        text_prompt=text_prompt,
        multimodal_files=multimodal_files,
        multimodal_urls=multimodal_urls
    )

    # Try LLM Router first if available and router is explicitly configured
    # Priority: Respect explicit genai_client (bypasses router), else use router when configured
    # This honors the docstring contract that passing genai_client bypasses the router
    # If router parameter is provided, use it directly (request-scoped routing)
    # Otherwise, check env vars to decide whether to use singleton router
    should_route = use_router and LLM_ROUTER_AVAILABLE and (router is not None or get_router is not None)
    use_provided_or_env_router = router is not None or _should_use_router()
    if should_route and genai_client is None and use_provided_or_env_router:
        try:
            # Use provided router or fall back to singleton (backward compatible)
            router_instance = router if router is not None else get_router()
            # Router generates structured output with automatic provider selection
            validated, response = router_instance.generate_structured(
                prompt=text_prompt,
                schema=ImprovementResponse,
                system_instruction=IDEA_GENERATOR_SYSTEM_INSTRUCTION,
                temperature=temperature,
                # Note: multimodal files/urls require specific provider (Gemini)
                files=[Path(f) for f in multimodal_files] if multimodal_files else None,
                urls=multimodal_urls,
            )

            # Successfully got structured response via router
            logging.info(f"Router generated improvement via {response.provider} ({response.tokens_used} tokens)")
            return f"{validated.improved_title}\n\n{validated.improved_description}"

        except AllProvidersFailedError as e:
            logging.warning(f"LLM Router failed, falling back to direct API: {e}")
            # Fall through to direct API call
        except Exception as e:
            logging.warning(f"Router error, falling back to direct API: {e}")
            # Fall through to direct API call

    if not GENAI_AVAILABLE or genai_client is None:
        # Mock response for testing
        return f"A revolutionary {context} solution that addresses all feedback points through innovative implementation."

    try:
        # Configure for structured output with pre-computed schema
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=IDEA_GENERATOR_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=_IMPROVEMENT_RESPONSE_GENAI_SCHEMA
        )

        response = genai_client.models.generate_content(
            model=model_name,
            contents=contents,
            config=config
        )
        
        # Parse and validate JSON response with Pydantic adapter
        if response.text:
            try:
                improvement = genai_response_to_pydantic(response.text, ImprovementResponse)

                # Combine title and description for backward compatibility
                return f"{improvement.improved_title}\n\n{improvement.improved_description}"

            except (ValueError, json.JSONDecodeError) as e:
                # Fallback to raw text if parsing fails
                logging.warning(f"Response parsing failed, using raw text: {e}")
                return response.text
        else:
            return f"An enhanced {context} approach incorporating all feedback."
            
    except (AttributeError, ValueError, KeyError, json.JSONDecodeError) as e:
        # Handle specific expected errors from API or JSON parsing
        logging.error(f"Error in structured idea improvement: {e}")
        # Return a reasonable fallback
        return f"An innovative {context} solution that balances all stakeholder concerns."
    except Exception as e:
        # Log unexpected errors but still return a fallback for robustness
        # This allows the main improve_idea to decide whether to retry with original implementation
        logging.error(f"Unexpected error in structured improvement: {e}")
        return f"An enhanced {context} solution addressing the provided feedback."


def generate_ideas_structured(
    topic: str,
    context: str,
    temperature: float = 0.9,
    genai_client: Optional[Any] = None,
    model_name: str = DEFAULT_GOOGLE_GENAI_MODEL
) -> str:
    """Generate ideas using structured output for cleaner responses.
    
    Args:
        topic: The topic for idea generation
        context: Additional context or constraints
        temperature: Controls creativity (0.0-1.0)
        genai_client: Optional GenAI client instance
        model_name: Model to use for generation
        
    Returns:
        Generated ideas as clean text, one per line
    """
    prompt = f"""Topic: {topic}
Context: {context}

Generate 5-7 diverse and creative ideas. Write ONLY the ideas, one per line, numbered."""
    
    if not GENAI_AVAILABLE or genai_client is None:
        return "1. Mock idea for testing\n2. Another mock idea\n3. Third mock idea"
    
    try:
        # For idea generation, we can use regular text output
        # but with improved system instruction
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=IDEA_GENERATOR_SYSTEM_INSTRUCTION
        )
        
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        return response.text if response.text else ""
        
    except Exception as e:
        logging.error(f"Error in structured idea generation: {e}")
        return ""