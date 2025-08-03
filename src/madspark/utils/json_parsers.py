"""Shared JSON parsing utilities to avoid code duplication."""
import json
from typing import List, Dict, Any


def parse_idea_generator_response(ideas_text: str) -> List[str]:
    """Parse idea generator response from JSON or text format.
    
    Args:
        ideas_text: Raw response from idea generator (JSON or text)
        
    Returns:
        List of formatted idea strings
    """
    try:
        # Try to parse as JSON first (structured output)
        ideas_json = json.loads(ideas_text)
        
        # Extract ideas from structured format
        parsed_ideas = []
        for idea_obj in ideas_json:
            # Build a formatted idea string from the structured data
            idea_number = idea_obj.get('idea_number')
            title = idea_obj.get('title', 'Untitled')
            description = idea_obj.get('description', 'No description provided')
            
            # Format based on whether we have an idea number
            if idea_number:
                idea_text = f"{idea_number}. {title}: {description}"
            else:
                idea_text = f"{title}: {description}"
                
            if 'key_features' in idea_obj and idea_obj['key_features']:
                # Add key features as a formatted list
                features = " Key features: " + ", ".join(idea_obj['key_features'])
                idea_text += features
            parsed_ideas.append(idea_text.strip())
            
        return parsed_ideas
        
    except (json.JSONDecodeError, TypeError):
        # Fall back to text parsing for backward compatibility
        return [idea.strip() for idea in ideas_text.split('\n') if idea.strip()]


def parse_evaluation_response(evaluation_output: str, expected_count: int) -> List[Dict[str, Any]]:
    """Parse evaluation response with fallback logic.
    
    Args:
        evaluation_output: Raw evaluation response
        expected_count: Expected number of evaluations
        
    Returns:
        List of evaluation dictionaries with score and comment
    """
    from madspark.utils.utils import parse_json_with_fallback
    
    # Use existing utility function
    evaluation_results = parse_json_with_fallback(
        evaluation_output,
        expected_count=expected_count
    )
    
    # Ensure each result has required fields
    parsed_results = []
    for eval_data in evaluation_results:
        parsed_results.append({
            "score": eval_data.get("score", 0),
            "comment": eval_data.get("comment", eval_data.get("critique", "No critique available"))
        })
    
    return parsed_results