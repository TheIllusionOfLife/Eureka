"""Structured response schemas for agent outputs using Google Gemini's structured output feature.

These schemas ensure consistent, parseable responses from all agents.
"""
from typing import Dict, Any


# Schema for Idea Generator Agent
IDEA_GENERATOR_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "idea_number": {
                "type": "INTEGER",
                "description": "Sequential number for the idea (1, 2, 3, etc.)"
            },
            "title": {
                "type": "STRING",
                "description": "Concise, descriptive title for the idea"
            },
            "description": {
                "type": "STRING",
                "description": "Detailed description of the idea and how it works"
            },
            "key_features": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "List of main features or components"
            },
            "category": {
                "type": "STRING",
                "description": "Category or domain of the idea",
                "nullable": True
            }
        },
        "required": ["idea_number", "title", "description"]
    }
}

# Example valid response for Idea Generator:
# [
#   {
#     "idea_number": 1,
#     "title": "AI Health Assistant",
#     "description": "A personalized health monitoring system that uses AI to track vital signs and provide health recommendations",
#     "key_features": ["Real-time monitoring", "AI predictions", "Doctor integration"],
#     "category": "Healthcare"
#   },
#   {
#     "idea_number": 2,
#     "title": "Smart Urban Garden",
#     "description": "An IoT-enabled urban gardening system that optimizes plant growth in small spaces",
#     "key_features": ["Automated watering", "Light optimization", "Mobile app control"]
#   }
# ]


# Schema for Evaluator Agent
EVALUATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "score": {
            "type": "NUMBER",
            "description": "Numerical score from 0 to 10"
        },
        "critique": {
            "type": "STRING",
            "description": "Overall critical assessment of the idea"
        },
        "strengths": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of positive aspects"
        },
        "weaknesses": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of concerns or limitations"
        }
    },
    "required": ["score", "critique"]
}

# Example valid response for Evaluator:
# {
#   "score": 8.5,
#   "critique": "This AI Health Assistant addresses a significant market need with innovative features. The real-time monitoring and AI predictions show strong technical merit.",
#   "strengths": ["Addresses real healthcare needs", "Strong technical foundation", "Clear monetization path"],
#   "weaknesses": ["Regulatory compliance challenges", "High initial development costs"]
# }

# Critic evaluates multiple ideas, so returns an array
CRITIC_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "score": {
                "type": "NUMBER",
                "description": "Numerical score from 0 to 10"
            },
            "comment": {
                "type": "STRING",
                "description": "Overall critical assessment of the idea"
            },
            "strengths": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "List of positive aspects"
            },
            "weaknesses": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "List of concerns or limitations"
            }
        },
        "required": ["score", "comment"]
    }
}

# Schema for Advocacy Agent
ADVOCACY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "strengths": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Strength category title"
                    },
                    "description": {
                        "type": "STRING",
                        "description": "Detailed explanation of the strength"
                    }
                },
                "required": ["title", "description"]
            },
            "description": "List of strengths with titles and descriptions"
        },
        "opportunities": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Opportunity title"
                    },
                    "description": {
                        "type": "STRING",
                        "description": "Detailed explanation of the opportunity"
                    }
                },
                "required": ["title", "description"]
            },
            "description": "List of opportunities with titles and descriptions"
        },
        "addressing_concerns": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concern": {
                        "type": "STRING",
                        "description": "The concern being addressed"
                    },
                    "response": {
                        "type": "STRING",
                        "description": "How to address or mitigate the concern"
                    }
                },
                "required": ["concern", "response"]
            },
            "description": "List of concerns and how to address them"
        }
    },
    "required": ["strengths", "opportunities", "addressing_concerns"]
}

# Example valid response for Advocacy:
# {
#   "strengths": [
#     {"title": "Market Demand", "description": "Healthcare monitoring addresses a $200B market with growing demand"},
#     {"title": "Technical Innovation", "description": "AI-powered predictions provide unique value proposition"}
#   ],
#   "opportunities": [
#     {"title": "Partnership Potential", "description": "Major healthcare providers seeking digital health solutions"},
#     {"title": "Expansion Markets", "description": "Easily adaptable to elder care and fitness markets"}
#   ],
#   "addressing_concerns": [
#     {"concern": "Regulatory hurdles", "response": "Partner with FDA consultants early in development"},
#     {"concern": "High costs", "response": "Phase rollout starting with basic features"}
#   ]
# }


# Schema for Skepticism Agent
SKEPTICISM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "critical_flaws": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Flaw title"
                    },
                    "description": {
                        "type": "STRING",
                        "description": "Detailed explanation of the flaw"
                    }
                },
                "required": ["title", "description"]
            },
            "description": "List of critical flaws or fundamental issues"
        },
        "risks_and_challenges": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {
                        "type": "STRING",
                        "description": "Risk or challenge title"
                    },
                    "description": {
                        "type": "STRING",
                        "description": "Detailed explanation and potential impact"
                    }
                },
                "required": ["title", "description"]
            },
            "description": "List of risks and implementation challenges"
        },
        "questionable_assumptions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "assumption": {
                        "type": "STRING",
                        "description": "The assumption being questioned"
                    },
                    "concern": {
                        "type": "STRING",
                        "description": "Why this assumption might be wrong"
                    }
                },
                "required": ["assumption", "concern"]
            },
            "description": "List of assumptions that may not hold true"
        },
        "missing_considerations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "aspect": {
                        "type": "STRING",
                        "description": "What aspect is missing"
                    },
                    "importance": {
                        "type": "STRING",
                        "description": "Why this aspect is important to consider"
                    }
                },
                "required": ["aspect", "importance"]
            },
            "description": "Important factors not addressed in the idea"
        }
    },
    "required": ["critical_flaws", "risks_and_challenges", "questionable_assumptions", "missing_considerations"]
}


# Schema for Improver Agent
IMPROVER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "improved_title": {
            "type": "STRING",
            "description": "Enhanced title for the improved idea"
        },
        "improved_description": {
            "type": "STRING",
            "description": "Comprehensive description of the improved concept"
        },
        "key_improvements": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "List of specific improvements made"
        },
        "implementation_steps": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Step-by-step implementation plan"
        },
        "differentiators": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "What makes this improved version unique",
            "nullable": True
        }
    },
    "required": ["improved_title", "improved_description", "key_improvements"]
}


# Multi-dimensional Evaluation Schema (for enhanced reasoning)
MULTI_DIMENSIONAL_EVAL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "feasibility": {
            "type": "NUMBER",
            "description": "Score 0-10 for technical and practical feasibility"
        },
        "innovation": {
            "type": "NUMBER",
            "description": "Score 0-10 for novelty and creativity"
        },
        "impact": {
            "type": "NUMBER",
            "description": "Score 0-10 for potential positive impact"
        },
        "cost_effectiveness": {
            "type": "NUMBER",
            "description": "Score 0-10 for value relative to cost"
        },
        "scalability": {
            "type": "NUMBER",
            "description": "Score 0-10 for growth potential"
        },
        "risk_level": {
            "type": "NUMBER",
            "description": "Score 0-10 where 0 is highest risk, 10 is lowest risk"
        },
        "timeline": {
            "type": "NUMBER",
            "description": "Score 0-10 for realistic timeline expectations"
        },
        "rationale": {
            "type": "OBJECT",
            "properties": {
                "feasibility": {"type": "STRING"},
                "innovation": {"type": "STRING"},
                "impact": {"type": "STRING"},
                "cost_effectiveness": {"type": "STRING"},
                "scalability": {"type": "STRING"},
                "risk_level": {"type": "STRING"},
                "timeline": {"type": "STRING"}
            },
            "description": "Brief explanation for each score"
        }
    },
    "required": ["feasibility", "innovation", "impact", "cost_effectiveness", 
                "scalability", "risk_level", "timeline"]
}


def validate_response_against_schema(response: Any, schema: Dict[str, Any]) -> bool:
    """Validate that a response matches the expected schema structure.
    
    This is a simplified validator for testing. In production, the Google GenAI
    SDK handles validation automatically.
    
    Args:
        response: The response data to validate
        schema: The schema to validate against
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if schema["type"] == "ARRAY":
            if not isinstance(response, list):
                return False
            item_schema = schema.get("items", {})
            for item in response:
                if not _validate_object(item, item_schema):
                    return False
            return True
        elif schema["type"] == "OBJECT":
            return _validate_object(response, schema)
        else:
            return False
    except Exception:
        return False


def _validate_object(obj: Any, schema: Dict[str, Any]) -> bool:
    """Validate an object against a schema."""
    if not isinstance(obj, dict):
        return False
    
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in obj:
            return False
    
    # Check property types
    properties = schema.get("properties", {})
    for key, value in obj.items():
        if key in properties:
            prop_schema = properties[key]
            if not _validate_property(value, prop_schema):
                return False
    
    return True


def _validate_property(value: Any, prop_schema: Dict[str, Any]) -> bool:
    """Validate a single property against its schema."""
    prop_type = prop_schema.get("type")
    
    # Handle nullable
    if prop_schema.get("nullable", False) and value is None:
        return True
    
    if prop_type == "STRING":
        return isinstance(value, str)
    elif prop_type == "NUMBER":
        return isinstance(value, (int, float))
    elif prop_type == "INTEGER":
        return isinstance(value, int)
    elif prop_type == "ARRAY":
        if not isinstance(value, list):
            return False
        # Validate array items if schema provided
        item_schema = prop_schema.get("items")
        if item_schema:
            for item in value:
                if not _validate_property(item, item_schema):
                    return False
        return True
    elif prop_type == "OBJECT":
        return _validate_object(value, prop_schema)
    
    return False


# Convert risk_assessment to safety_score in responses
def convert_risk_to_safety_score(dimension_scores: Dict[str, float]) -> Dict[str, float]:
    """Convert risk_assessment (lower is better) to safety_score (higher is better).
    
    Args:
        dimension_scores: Dictionary containing dimension scores
        
    Returns:
        New dictionary with safety_score instead of risk_assessment
    """
    # Create a copy to avoid mutating the input
    result = dimension_scores.copy()
    
    if "risk_assessment" in result:
        # Invert the risk score to create safety score
        risk_score = result.pop("risk_assessment")
        result["safety_score"] = 10.0 - risk_score
    
    return result


# Aliases for consistency with agent imports
ADVOCATE_SCHEMA = ADVOCACY_SCHEMA
SKEPTIC_SCHEMA = SKEPTICISM_SCHEMA