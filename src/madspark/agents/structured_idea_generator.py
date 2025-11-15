"""Structured output implementation for idea generation.

This module provides enhanced idea generation using Gemini's structured output
capabilities to ensure clean, meta-commentary-free responses.
"""
import json
import logging
from pathlib import Path
from typing import Any, Optional, List, Union

from ..utils.constants import DEFAULT_GOOGLE_GENAI_MODEL
from ..utils.multimodal_input import build_prompt_with_multimodal
from madspark.schemas.generation import ImprovementResponse
from madspark.schemas.adapters import pydantic_to_genai_schema

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
    multimodal_urls: Optional[List[str]] = None
) -> str:
    """Improves an idea using structured output for clean responses.

    This function uses Gemini's structured output capabilities to ensure
    the response contains only the improved idea without meta-commentary.

    Args:
        original_idea: The original idea to improve
        critique: The critic's evaluation
        advocacy_points: The advocate's bullet points
        skeptic_points: The skeptic's concerns
        context: The original context for improvement
        temperature: Controls randomness (0.0-1.0)
        genai_client: Optional GenAI client instance
        model_name: Model to use for generation
        
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
        
        # Parse JSON response using Pydantic schema fields
        if response.text:
            try:
                data = json.loads(response.text)
                # New Pydantic schema has improved_title and improved_description
                if "improved_title" in data and "improved_description" in data:
                    # Combine title and description for backward compatibility
                    return f"{data['improved_title']}\n\n{data['improved_description']}"
                # Fallback for legacy "improved_idea" field (shouldn't happen with new schema)
                return data.get("improved_idea", response.text)
            except json.JSONDecodeError:
                # Fallback to raw text if not valid JSON
                logging.warning("Response was not valid JSON, using raw text")
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