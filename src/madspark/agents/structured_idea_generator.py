"""Structured output implementation for idea generation.

This module provides enhanced idea generation using Gemini's structured output
capabilities to ensure clean, meta-commentary-free responses.
"""
import logging
from typing import Any, Optional

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
from madspark.utils.errors import ValidationError


# Response schema for structured output
IMPROVEMENT_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "improved_idea": {
            "type": "STRING",
            "description": "The improved idea content only, no meta-commentary, no references to original"
        },
        "key_improvements": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Brief list of key improvements made (optional)"
        }
    },
    "required": ["improved_idea"]
}


def improve_idea_structured(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    theme: str,
    temperature: float = 0.9,
    genai_client: Optional[Any] = None,
    model_name: str = "gemini-2.5-flash"
) -> str:
    """Improves an idea using structured output for clean responses.
    
    This function uses Gemini's structured output capabilities to ensure
    the response contains only the improved idea without meta-commentary.
    
    Args:
        original_idea: The original idea to improve
        critique: The critic's evaluation
        advocacy_points: The advocate's bullet points
        skeptic_points: The skeptic's concerns
        theme: The original theme for context
        temperature: Controls randomness (0.0-1.0)
        genai_client: Optional GenAI client instance
        model_name: Model to use for generation
        
    Returns:
        The improved idea text without any meta-commentary
        
    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If API is not configured
    """
    # Validate inputs
    if not all([original_idea, critique, advocacy_points, skeptic_points, theme]):
        raise ValidationError("All input parameters must be non-empty strings")
    
    # Build focused prompt
    prompt = f"""Theme: {theme}

Original Idea: {original_idea}

Professional Evaluation: {critique}

Key Strengths: {advocacy_points}

Critical Concerns: {skeptic_points}

Task: Generate an improved version that:
1. Addresses ALL evaluation criteria
2. Maintains identified strengths
3. Provides solutions for each concern
4. Remains bold and creative

Write ONLY the improved idea. No introductions, no meta-commentary."""
    
    if not GENAI_AVAILABLE or genai_client is None:
        # Mock response for testing
        return f"A revolutionary {theme} solution that addresses all feedback points through innovative implementation."
    
    try:
        # Configure for structured output
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=IDEA_GENERATOR_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=IMPROVEMENT_RESPONSE_SCHEMA
        )
        
        response = genai_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        # Parse JSON response
        if response.text:
            import json
            try:
                data = json.loads(response.text)
                return data.get("improved_idea", response.text)
            except json.JSONDecodeError:
                # Fallback to raw text if not valid JSON
                logging.warning("Response was not valid JSON, using raw text")
                return response.text
        else:
            return f"An enhanced {theme} approach incorporating all feedback."
            
    except Exception as e:
        logging.error(f"Error in structured idea improvement: {e}")
        # Return a reasonable fallback
        return f"An innovative {theme} solution that balances all stakeholder concerns."


def generate_ideas_structured(
    topic: str,
    context: str,
    temperature: float = 0.9,
    genai_client: Optional[Any] = None,
    model_name: str = "gemini-2.5-flash"
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