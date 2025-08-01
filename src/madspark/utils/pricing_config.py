"""Pricing configuration for various AI models.

This module contains pricing information for different AI models used in the system.
Prices are per 1K tokens unless otherwise specified.
"""

from typing import Dict

# Token costs configuration (per 1K tokens)
# These values should be updated based on actual model pricing
TOKEN_COSTS: Dict[str, Dict[str, float]] = {
    "gemini-1.5-pro": {
        "input": 0.00125,   # $1.25 per 1M input tokens
        "output": 0.005     # $5.00 per 1M output tokens
    },
    "gemini-1.5-flash": {
        "input": 0.000075,  # $0.075 per 1M input tokens
        "output": 0.0003    # $0.30 per 1M output tokens
    },
    # Add more models as needed
    "gpt-4": {
        "input": 0.03,      # $30 per 1M input tokens
        "output": 0.06      # $60 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.0005,    # $0.50 per 1M input tokens
        "output": 0.0015    # $1.50 per 1M output tokens
    }
}

# Default model for cost estimation when actual model is unknown
DEFAULT_PRICING_MODEL = "gemini-1.5-pro"

# Estimated output token ratio (output tokens as percentage of input tokens)
DEFAULT_OUTPUT_RATIO = 0.3  # 30% output tokens

def get_token_cost(model: str, token_type: str = "input") -> float:
    """Get the cost per 1K tokens for a specific model and token type.
    
    Args:
        model: The model name
        token_type: Either "input" or "output"
        
    Returns:
        Cost per 1K tokens, or default model cost if model not found
    """
    if model in TOKEN_COSTS and token_type in TOKEN_COSTS[model]:
        return TOKEN_COSTS[model][token_type]
    
    # Fall back to default model pricing
    return TOKEN_COSTS[DEFAULT_PRICING_MODEL][token_type]

def estimate_cost(model: str, input_tokens: int, output_tokens: int = None) -> float:
    """Estimate the total cost for a given number of tokens.
    
    Args:
        model: The model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (if None, estimates based on ratio)
        
    Returns:
        Estimated total cost in USD
    """
    if output_tokens is None:
        output_tokens = int(input_tokens * DEFAULT_OUTPUT_RATIO)
    
    input_cost = get_token_cost(model, "input") * (input_tokens / 1000)
    output_cost = get_token_cost(model, "output") * (output_tokens / 1000)
    
    return input_cost + output_cost