"""
OpenAPI Documentation Enhancements for MadSpark API
Provides detailed schemas, examples, and descriptions for API documentation
"""

from typing import Dict, Any, List

# API Examples for request/response models
API_EXAMPLES = {
    "idea_generation_request": {
        "simple": {
            "summary": "Simple idea generation",
            "description": "Basic request with minimal parameters",
            "value": {
                "theme": "sustainable urban transportation",
                "constraints": "budget-friendly, implementable within 2 years",
                "num_top_candidates": 3
            }
        },
        "advanced": {
            "summary": "Advanced idea generation",
            "description": "Request with all enhanced features enabled",
            "value": {
                "theme": "sustainable urban transportation",
                "constraints": "budget-friendly, implementable within 2 years, focus on reducing carbon emissions",
                "num_top_candidates": 5,
                "enable_novelty_filter": True,
                "novelty_threshold": 0.8,
                "temperature_preset": "creative",
                "enhanced_reasoning": True,
                "multi_dimensional_eval": True,
                "logical_inference": True,
                "verbose": False,
                "show_detailed_results": True
            }
        },
        "bookmark_remix": {
            "summary": "Bookmark-based generation",
            "description": "Generate new ideas based on existing bookmarks",
            "value": {
                "theme": "sustainable urban transportation",
                "bookmark_ids": ["bookmark_123", "bookmark_456"],
                "num_top_candidates": 3,
                "temperature_preset": "balanced"
            }
        }
    },
    "idea_generation_response": {
        "summary": "Successful idea generation response",
        "value": {
            "status": "success",
            "message": "Ideas generated successfully",
            "results": [
                {
                    "idea": "Implement a city-wide e-bike sharing program with solar-powered charging stations",
                    "initial_score": 7.5,
                    "initial_critique": "Good environmental impact but requires significant infrastructure investment",
                    "improved_idea": "Launch a phased e-bike sharing program starting in high-traffic areas, partnering with local businesses for charging station placement",
                    "improved_score": 8.5,
                    "improved_critique": "Phased approach reduces initial costs while maintaining environmental benefits",
                    "advocacy": "This solution addresses multiple urban challenges including traffic congestion and air pollution",
                    "skepticism": "User adoption rates and maintenance costs need careful consideration",
                    "multi_dimensional_evaluation": {
                        "dimension_scores": {
                            "feasibility": 8.0,
                            "innovation": 7.5,
                            "potential_impact": 9.0,
                            "cost_effectiveness": 7.0,
                            "sustainability": 9.5
                        },
                        "overall_weighted_score": 8.2,
                        "rationale": "Strong environmental impact with reasonable implementation costs"
                    }
                }
            ],
            "processing_time": 12.5,
            "timestamp": "2024-01-15T10:30:45Z"
        }
    },
    "bookmark_request": {
        "simple": {
            "summary": "Simple bookmark creation",
            "description": "Bookmark an idea with basic information",
            "value": {
                "idea": "Implement a city-wide e-bike sharing program",
                "theme": "sustainable urban transportation",
                "constraints": "budget-friendly",
                "initial_score": 7.5,
                "initial_critique": "Good idea but needs refinement"
            }
        },
        "complete": {
            "summary": "Complete bookmark with all fields",
            "description": "Bookmark with improved idea and full evaluation",
            "value": {
                "idea": "Implement a city-wide e-bike sharing program",
                "improved_idea": "Launch a phased e-bike sharing program with business partnerships",
                "theme": "sustainable urban transportation",
                "constraints": "budget-friendly, 2-year timeline",
                "initial_score": 7.5,
                "improved_score": 8.5,
                "initial_critique": "Good environmental impact but high initial costs",
                "improved_critique": "Phased approach makes it more feasible",
                "advocacy": "Addresses traffic and pollution issues",
                "skepticism": "Maintenance costs need consideration",
                "tags": ["transportation", "sustainability", "urban-planning"]
            }
        }
    },
    "duplicate_check": {
        "request": {
            "summary": "Check for duplicate ideas",
            "value": {
                "idea": "Create a network of electric vehicle charging stations powered by renewable energy",
                "theme": "sustainable transportation",
                "similarity_threshold": 0.8
            }
        },
        "response_no_duplicates": {
            "summary": "No duplicates found",
            "value": {
                "status": "success",
                "has_duplicates": False,
                "similar_count": 0,
                "recommendation": "allow",
                "similarity_threshold": 0.8,
                "similar_bookmarks": [],
                "message": "No similar bookmarks found. Safe to save."
            }
        },
        "response_with_duplicates": {
            "summary": "Similar bookmarks found",
            "value": {
                "status": "success",
                "has_duplicates": True,
                "similar_count": 2,
                "recommendation": "warn",
                "similarity_threshold": 0.8,
                "similar_bookmarks": [
                    {
                        "id": "bookmark_123",
                        "text": "Build solar-powered EV charging stations across the city",
                        "theme": "sustainable transportation",
                        "similarity_score": 0.85,
                        "match_type": "high",
                        "matched_features": ["electric vehicle", "charging stations", "renewable energy"]
                    }
                ],
                "message": "Found 2 similar bookmarks. Consider reviewing existing ideas."
            }
        }
    }
}

# API Tags with descriptions
API_TAGS = [
    {
        "name": "idea-generation",
        "description": "Endpoints for generating creative ideas using the MadSpark multi-agent system"
    },
    {
        "name": "bookmarks",
        "description": "Manage saved ideas including creation, retrieval, and duplicate detection"
    },
    {
        "name": "configuration",
        "description": "System configuration endpoints for temperature presets and settings"
    },
    {
        "name": "health",
        "description": "Health check and system status endpoints"
    }
]

# Enhanced endpoint descriptions
ENDPOINT_DESCRIPTIONS = {
    "generate_ideas": """
Generate creative ideas using the MadSpark multi-agent system.

The system uses multiple AI agents with different roles:
- **Idea Generator**: Creates initial creative ideas
- **Evaluator**: Scores ideas on multiple dimensions
- **Improver**: Enhances and refines the best ideas
- **Advocate**: Highlights strengths and potential
- **Skeptic**: Identifies challenges and risks

### Features:
- **Enhanced Reasoning**: Enable context-aware agents that reference conversation history
- **Multi-dimensional Evaluation**: Score ideas on feasibility, innovation, impact, etc.
- **Logical Inference**: Apply formal reasoning chains with confidence scoring
- **Novelty Filter**: Remove duplicate or overly similar ideas
- **Temperature Control**: Adjust creativity levels using presets or custom values
- **Bookmark Integration**: Generate new ideas based on previously saved bookmarks

### Temperature Presets:
- `conservative`: Low creativity, focused on practical ideas
- `balanced`: Moderate creativity (default)
- `creative`: High creativity, more innovative ideas
- `wild`: Maximum creativity, experimental ideas
""",
    "check_duplicates": """
Check if an idea is similar to existing bookmarks.

Uses advanced similarity detection:
- **Semantic Similarity**: Meaning-based comparison using embeddings
- **Content Hashing**: Fast exact match detection
- **Feature Extraction**: Identifies key concepts and themes

### Recommendations:
- `block`: Very high similarity (>90%) - likely duplicate
- `warn`: High similarity (80-90%) - review recommended
- `notice`: Moderate similarity (70-80%) - potentially related
- `allow`: Low similarity (<70%) - safe to save
""",
    "get_temperature_presets": """
Retrieve available temperature presets for idea generation.

Temperature controls the creativity and randomness of generated ideas:
- **idea_generation**: Controls initial idea creativity
- **evaluation**: Affects scoring consistency
- **advocacy**: Influences enthusiasm level
- **skepticism**: Adjusts criticism intensity

Each preset provides balanced settings for all components.
"""
}

def get_openapi_customization() -> Dict[str, Any]:
    """
    Get OpenAPI schema customizations for FastAPI
    """
    return {
        "info": {
            "title": "MadSpark Multi-Agent Idea Generation API",
            "description": """
## Overview

The MadSpark API provides access to an advanced multi-agent AI system for creative idea generation and evaluation. 
The system uses multiple specialized agents working together to generate, evaluate, improve, and analyze ideas.

## Key Features

- 🚀 **Multi-Agent Architecture**: Specialized agents for different aspects of ideation
- 🧠 **Enhanced Reasoning**: Context-aware agents with conversation memory
- 📊 **Multi-dimensional Evaluation**: Comprehensive scoring across multiple criteria
- 🔍 **Duplicate Detection**: Advanced similarity checking to avoid redundant ideas
- 🎨 **Creativity Control**: Fine-tune output creativity with temperature presets
- 💾 **Bookmark System**: Save and remix your best ideas
- ⚡ **Real-time Progress**: WebSocket support for progress updates

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Rate Limiting

- General endpoints: 60 requests per minute
- Idea generation: 5 requests per minute per IP

## WebSocket Support

Connect to `/ws/progress` for real-time progress updates during idea generation.

## Error Handling

All endpoints return consistent error responses:
```json
{
  "detail": "Error description",
  "status": "error",
  "timestamp": "2024-01-15T10:30:45Z"
}
```

## Terminology Note

For backward compatibility:
- API uses "theme" = Internal "topic"
- API uses "constraints" = Internal "context"
""",
            "version": "2.2.0",
            "contact": {
                "name": "MadSpark Development Team",
                "email": "support@madspark.ai"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Local development server"
            },
            {
                "url": "https://api.madspark.ai",
                "description": "Production server (future)"
            }
        ],
        "tags": API_TAGS,
        "components": {
            "securitySchemes": {
                "future_auth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT authentication (planned for future versions)"
                }
            },
            "responses": {
                "ValidationError": {
                    "description": "Validation Error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "loc": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                },
                                                "msg": {"type": "string"},
                                                "type": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "RateLimitError": {
                    "description": "Rate limit exceeded",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "detail": {"type": "string", "example": "Rate limit exceeded: 5 per 1 minute"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }