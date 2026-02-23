"""
FastAPI Backend for MadSpark Multi-Agent System - Phase 2.2

This module provides a web API interface for the MadSpark system,
enabling web-based access to all core functionality including
idea generation, enhanced reasoning, and multi-dimensional evaluation.
"""
import asyncio
import json
import logging
import os
import random
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from contextlib import asynccontextmanager

if TYPE_CHECKING:
    from madspark.llm.router import LLMRouter

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, validator, ValidationError as PydanticValidationError
from typing import Literal
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import html
from anyio import open_file

# Import OpenAPI enhancements
try:
    from openapi_enhancements import (
        API_EXAMPLES, API_TAGS, ENDPOINT_DESCRIPTIONS, 
        get_openapi_customization
    )
except ImportError:
    API_EXAMPLES = {}
    API_TAGS = []
    ENDPOINT_DESCRIPTIONS = {}
    def get_openapi_customization():
        return {}

# Import MadSpark modules
# Add the parent directory to the path for imports with security validation
def validate_and_add_path():
    """Securely validate and add MadSpark path to sys.path"""
    madspark_path = os.environ.get('MADSPARK_PATH', '/madspark')
    
    # Security: Validate path to prevent directory traversal
    if madspark_path:
        # Normalize path to resolve any ../ or ./ components
        normalized_path = os.path.normpath(madspark_path)
        
        # Security check: Reject paths with traversal attempts
        if '..' in normalized_path or not os.path.isabs(normalized_path):
            logging.warning(f"Rejected potentially unsafe MADSPARK_PATH: {madspark_path}")
            madspark_path = None
        else:
            madspark_path = normalized_path
    
    src_path = os.path.join(madspark_path, 'src') if madspark_path else None

    if src_path and os.path.exists(src_path):
        sys.path.insert(0, src_path)
        logging.info(f"Added to Python path: {src_path}")
    elif madspark_path and os.path.exists(madspark_path):
        sys.path.insert(0, madspark_path)
        logging.info(f"Added to Python path: {madspark_path}")
    else:
        # Fallback for local development - point to the src directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        src_dir = os.path.join(parent_dir, 'src')
        if os.path.exists(src_dir):
            sys.path.insert(0, src_dir)
            logging.info(f"Added fallback path: {src_dir}")

validate_and_add_path()

def sanitize_for_logging(text: str, max_length: int = 50) -> str:
    """Sanitize text for secure logging by redacting sensitive information"""
    if not text:
        return "[EMPTY]"
    
    # Remove any potential sensitive patterns
    import re
    # Remove potential API keys, emails, phone numbers, etc.
    sensitive_patterns = [
        r'[A-Za-z0-9]{32,}',  # Long alphanumeric strings (potential tokens)
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # Email addresses
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
        r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number pattern
    ]
    
    sanitized = text
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        return f"[TRUNCATED:{len(text)} chars]"
    
    return sanitized

try:
    from madspark.core.async_coordinator import AsyncCoordinator
    from madspark.utils.temperature_control import TemperatureManager
    from madspark.core.enhanced_reasoning import ReasoningEngine
    from madspark.utils.constants import (
        DIMENSION_SCORES_KEY,
        FEASIBILITY_KEY,
        INNOVATION_KEY,
        IMPACT_KEY,
        COST_EFFECTIVENESS_KEY,
        SCALABILITY_KEY,
        RISK_ASSESSMENT_KEY,
        TIMELINE_KEY
    )
    from madspark.config.execution_constants import TimeoutConfig
    from madspark.utils.bookmark_system import BookmarkManager
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
    from madspark.utils.structured_output_check import is_structured_output_available
    # LLM Router imports (optional - may not be available in all environments)
    try:
        from madspark.llm import get_router
        from madspark.llm.cache import reset_cache as reset_llm_cache
        LLM_ROUTER_AVAILABLE = True
        logging.info("LLM Router available")
    except ImportError:
        LLM_ROUTER_AVAILABLE = False
        get_router = None  # type: ignore
        reset_llm_cache = None  # type: ignore
        logging.info("LLM Router not available")
except ImportError as e:
    logging.error(f"Failed to import MadSpark modules: {e}")
    # Try alternative paths for different deployment scenarios
    try:
        from src.madspark.core.async_coordinator import AsyncCoordinator
        from src.madspark.utils.temperature_control import TemperatureManager
        from src.madspark.core.enhanced_reasoning import ReasoningEngine
        from src.madspark.utils.constants import (
            DIMENSION_SCORES_KEY,
            FEASIBILITY_KEY,
            INNOVATION_KEY,
            IMPACT_KEY,
            COST_EFFECTIVENESS_KEY,
            SCALABILITY_KEY,
            RISK_ASSESSMENT_KEY,
            TIMELINE_KEY
        )
        from src.madspark.config.execution_constants import TimeoutConfig
        from src.madspark.utils.bookmark_system import BookmarkManager
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig
        from src.madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
        # Try to import router in fallback path
        try:
            from src.madspark.llm.router import get_router
            from src.madspark.llm.cache import reset_cache as reset_llm_cache
            LLM_ROUTER_AVAILABLE = True
        except ImportError:
            LLM_ROUTER_AVAILABLE = False
            get_router = None  # type: ignore
            reset_llm_cache = None  # type: ignore
            logging.info("LLM Router not available in fallback path")
    except ImportError as e2:
        logging.error(f"Failed to import MadSpark modules with fallback paths: {e2}")
        raise e

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG', 'false').lower() == 'true' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/madspark_backend.log', mode='a') if os.path.exists('logs') else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for file handling
CHUNK_SIZE = 1024 * 1024  # 1MB chunk size for streaming uploads

# Note: Thread-safety is now achieved through request-scoped router instances
# No global lock needed - each request creates its own independent router

# Enhanced error tracking
class ErrorTracker:
    def __init__(self):
        self.errors = []
        self.max_errors = 100
    
    def track_error(self, error_type: str, error_message: str, context: dict = None, session_id: str = None):
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'context': context or {},
            'session_id': session_id or 'unknown'
        }
        self.errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
            
        # Log the error
        logger.error(f"[{error_type}] {error_message}", extra={'context': context})
    
    def get_error_stats(self):
        error_types = {}
        for error in self.errors:
            error_types[error['type']] = error_types.get(error['type'], 0) + 1

        return {
            'total_errors': len(self.errors),
            'recent_errors': self.errors[-10:] if self.errors else [],
            'error_types': error_types
        }

error_tracker = ErrorTracker()


def _is_mock_mode() -> bool:
    """Return True when runtime configuration indicates mock mode should be used."""
    google_api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    madspark_mode = os.getenv("MADSPARK_MODE", "").lower()
    environment = os.getenv("ENVIRONMENT", "").lower()
    return (
        madspark_mode == "mock"
        or not google_api_key
        or google_api_key == "your-api-key-here"
        or google_api_key.startswith("mock-")
        or google_api_key.startswith("test-")
        or environment in ["test", "ci", "mock"]
    )


def create_request_router(idea_request: "IdeaGenerationRequest") -> Optional["LLMRouter"]:
    """Create a request-scoped LLMRouter from the request model.

    Args:
        idea_request: The IdeaGenerationRequest containing LLM configuration.

    Returns:
        LLMRouter instance if LLM_ROUTER_AVAILABLE, None otherwise.
    """
    if not LLM_ROUTER_AVAILABLE:
        return None

    from madspark.llm import LLMRouter
    from madspark.llm.config import LLMConfig, ModelTier

    # Map string tier to ModelTier enum
    tier_map = {
        "fast": ModelTier.FAST,
        "balanced": ModelTier.BALANCED,
        "quality": ModelTier.QUALITY,
    }
    model_tier = tier_map.get(idea_request.model_tier, ModelTier.FAST)

    # Create custom config with request-specific tier
    config = LLMConfig(
        default_provider=idea_request.llm_provider or "auto",
        model_tier=model_tier,
        fallback_enabled=not getattr(idea_request, 'no_fallback', False),
        cache_enabled=idea_request.use_llm_cache if idea_request.use_llm_cache is not None else True,
    )

    router = LLMRouter(config=config)
    logger.info(
        f"Request-scoped LLM Router created: provider={router._primary_provider}, "
        f"tier={model_tier}, cache={router._cache_enabled}"
    )
    return router


def generate_mock_results(topic: str, num_ideas: int, logical_inference: bool = False) -> List[Dict[str, Any]]:
    """Generate mock results for testing without API keys."""
    mock_ideas = {
        "urban farming": [
            "Vertical hydroponic towers with automated nutrient delivery for apartment balconies",
            "Window-mounted herb gardens with IoT sensors for optimal growth monitoring",
            "Stackable mushroom cultivation boxes using coffee grounds as substrate"
        ],
        "sustainable transportation": [
            "Electric bike-sharing stations powered by solar canopies at bus stops",
            "Autonomous electric shuttles for last-mile connectivity in suburbs",
            "Cargo bike delivery networks replacing trucks in city centers"
        ],
        "renewable energy": [
            "Building-integrated photovoltaic windows that generate electricity while providing shade",
            "Micro wind turbines designed for urban rooftops with noise reduction technology",
            "Piezoelectric floor tiles in high-traffic areas converting footsteps to electricity"
        ]
    }
    
    # Find matching theme or use default
    theme_key = None
    for key in mock_ideas.keys():
        if key.lower() in topic.lower() or topic.lower() in key.lower():
            theme_key = key
            break
    
    if not theme_key:
        # Generate generic ideas if no theme match
        base_ideas = [
            f"Innovative solution for {topic} using advanced technology",
            f"Sustainable approach to {topic} with community involvement",
            f"Cost-effective method for implementing {topic} at scale"
        ]
    else:
        base_ideas = mock_ideas[theme_key]
    
    results = []
    for i in range(min(num_ideas, len(base_ideas))):
        base_score = 6.5 + (i * 0.5)
        improved_score = base_score + 1.5 + (random.random() * 0.8)  # nosec B311
        
        result = {
            "idea": base_ideas[i],
            "initial_score": round(base_score, 1),
            "initial_critique": "Interesting concept but needs more detail on implementation and feasibility",
            "advocacy": f"This solution addresses key challenges in {topic} with innovative thinking",
            "skepticism": "Implementation costs and technical complexity may be barriers",
            "improved_idea": f"{base_ideas[i]}. Enhanced with AI-driven optimization, real-time monitoring, and adaptive learning capabilities for maximum efficiency",
            "improved_score": round(improved_score, 1),
            "improved_critique": "Comprehensive solution with clear benefits and implementation pathway",
            "score_delta": round(improved_score - base_score, 1),
            "multi_dimensional_evaluation": {
                "dimension_scores": {
                    "feasibility": round(7 + random.random() * 2, 1),  # nosec B311
                    "innovation": round(8 + random.random() * 1.5, 1),  # nosec B311
                    "impact": round(7.5 + random.random() * 2, 1),  # nosec B311
                    "cost_effectiveness": round(6.5 + random.random() * 2, 1),  # nosec B311
                    "scalability": round(7 + random.random() * 2.5, 1),  # nosec B311
                    "risk_assessment": round(6 + random.random() * 2, 1),  # nosec B311
                    "timeline": round(7 + random.random() * 1.5, 1)  # nosec B311
                },
                "overall_score": round(base_score + 0.5, 1),
                "confidence_interval": {
                    "lower": round(base_score - 0.5, 1),
                    "upper": round(base_score + 1.5, 1)
                }
            }
        }
        
        # Add logical inference data if enabled
        if logical_inference:
            result["logical_inference"] = {
                "inference_chain": [
                    f"Urban environments have limited horizontal space for {topic}",
                    f"Vertical solutions maximize space efficiency for {topic} implementation",
                    "Technology integration enables automation and monitoring",
                    "Community adoption drives scalability and sustainability"
                ],
                "conclusion": f"Integrated vertical approach optimizes {topic} implementation in urban settings",
                "confidence": round(0.75 + random.random() * 0.2, 2),  # nosec B311
                "improvements": f"Consider IoT sensors and AI-driven optimization for enhanced {topic} efficiency",
                "causal_chain": [
                    f"Limited space drives vertical {topic} solutions",
                    f"Vertical solutions enable scalable {topic} systems",
                    f"Scalable systems improve urban {topic} accessibility"
                ],
                "implications": [
                    f"Reduced space requirements for {topic} projects",
                    f"Increased {topic} productivity per square meter",
                    f"Enhanced urban sustainability through {topic} integration"
                ],
                "constraint_satisfaction": {
                    "space_efficiency": round(0.85 + random.random() * 0.1, 2),  # nosec B311
                    "cost_effectiveness": round(0.65 + random.random() * 0.2, 2),  # nosec B311
                    "technical_feasibility": round(0.75 + random.random() * 0.15, 2),  # nosec B311
                    "community_acceptance": round(0.7 + random.random() * 0.2, 2)  # nosec B311
                },
                "overall_satisfaction": round(0.75 + random.random() * 0.15, 2)  # nosec B311
            }
        
        results.append(result)
    
    return results


def detect_structured_output_usage(results: List[Dict[str, Any]]) -> bool:
    """Detect if structured output was used based on result content.
    
    Args:
        results: List of results from coordinator
        
    Returns:
        True if structured output appears to have been used, False otherwise
    """
    try:
        # Try to get genai client from idea generator
        from madspark.agents.idea_generator import GENAI_AVAILABLE, idea_generator_client
        if GENAI_AVAILABLE and idea_generator_client and is_structured_output_available(idea_generator_client):
            # Check if the improved ideas look like they came from structured output
            # (no meta-commentary patterns)
            if results and any(result.get('improved_idea') for result in results):
                first_improved = next((r.get('improved_idea', '') for r in results if r.get('improved_idea')), '')
                # Simple heuristic: structured output won't have common meta-commentary patterns
                meta_patterns = ['Here is', 'Here\'s', 'I\'ve improved', 'The improved version', 'Based on the feedback']
                structured_output_detected = not any(pattern.lower() in first_improved.lower() for pattern in meta_patterns)
                
                # Log the detection result
                logger.info(f"Structured output detection: {structured_output_detected} (meta-commentary found: {not structured_output_detected})")
                return structured_output_detected
    except ImportError:
        # If imports fail, assume no structured output
        logger.debug("ImportError while detecting structured output - assuming not available")
        pass
    
    return False



def format_results_for_frontend(results: List[Dict[str, Any]], structured_output_used: bool = False) -> List[Dict[str, Any]]:
    """Format results to match frontend expectations, especially multi-dimensional evaluation.
    
    Args:
        results: Raw results from the coordinator
        structured_output_used: Whether structured output was used for idea generation
    
    Returns:
        Formatted results with cleaning applied (unless structured output was used)
    """
    # Apply cleaning to all results before formatting (consistent with CLI)
    # Skip cleaning if structured output was used
    if structured_output_used:
        cleaned_results = results
    else:
        cleaned_results = clean_improved_ideas_in_results(results)
    
    formatted_results = []
    for result in cleaned_results:
        formatted_result = dict(result)
        
        # Transform multi_dimensional_evaluation if present
        if 'multi_dimensional_evaluation' in formatted_result and formatted_result['multi_dimensional_evaluation']:
            multi_eval = formatted_result['multi_dimensional_evaluation']
            
            # Extract dimension scores
            dimension_scores = multi_eval.get(DIMENSION_SCORES_KEY, {})
            
            # Format for frontend
            formatted_result['multi_dimensional_evaluation'] = {
                DIMENSION_SCORES_KEY: {
                    FEASIBILITY_KEY: dimension_scores.get(FEASIBILITY_KEY, 5),
                    INNOVATION_KEY: dimension_scores.get(INNOVATION_KEY, 5),
                    IMPACT_KEY: dimension_scores.get(IMPACT_KEY, 5),
                    COST_EFFECTIVENESS_KEY: dimension_scores.get(COST_EFFECTIVENESS_KEY, 5),
                    SCALABILITY_KEY: dimension_scores.get(SCALABILITY_KEY, 5),
                    RISK_ASSESSMENT_KEY: dimension_scores.get(RISK_ASSESSMENT_KEY, 5),
                    TIMELINE_KEY: dimension_scores.get(TIMELINE_KEY, 5)
                },
                'overall_score': multi_eval.get('weighted_score', 5),
                'confidence_interval': multi_eval.get('confidence_interval', {
                    'lower': multi_eval.get('weighted_score', 5) - 1,
                    'upper': multi_eval.get('weighted_score', 5) + 1
                })
            }
            
            # Generate improved multi-dimensional evaluation based on score improvement
            # This is a temporary solution until the backend properly evaluates improved ideas
            if 'improved_score' in formatted_result and 'initial_score' in formatted_result:
                improvement_factor = formatted_result['improved_score'] / max(formatted_result['initial_score'], 0.1)
                improvement_factor = min(improvement_factor, 1.4)  # Cap at 40% improvement
                
                original_scores = formatted_result['multi_dimensional_evaluation'][DIMENSION_SCORES_KEY]
                improved_scores = {}
                
                for dimension, score in original_scores.items():
                    # Apply improvement factor with some randomness and realistic constraints
                    base_improvement = (improvement_factor - 1) * score
                    # Add some variance to make it more realistic
                    variance = 0.1 * score  # 10% variance
                    random_factor = random.uniform(-0.5, 0.5)  # Random between -0.5 and +0.5  # nosec B311
                    improved_score = score + base_improvement + random_factor * variance  # Random between -variance/2 and +variance/2
                    # Ensure we don't exceed 10 or go below original
                    improved_score_value = min(10, max(score, improved_score))
                    # Round to 1 decimal place
                    improved_scores[dimension] = round(improved_score_value, 1)
                
                improved_overall = sum(improved_scores.values()) / len(improved_scores)
                # Round overall score to 1 decimal place
                improved_overall = round(improved_overall, 1)
                
                formatted_result['improved_multi_dimensional_evaluation'] = {
                    DIMENSION_SCORES_KEY: improved_scores,
                    'overall_score': improved_overall,
                    'confidence_interval': {
                        'lower': round(max(0, improved_overall - 0.8), 1),
                        'upper': round(min(10, improved_overall + 0.8), 1)
                    }
                }
        
        formatted_results.append(formatted_result)
    
    return formatted_results


# Global variables for MadSpark components
temp_manager: Optional[TemperatureManager] = None
reasoning_engine: Optional[ReasoningEngine] = None
bookmark_system: Optional[BookmarkManager] = None
cache_manager: Optional[CacheManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup MadSpark components."""
    global temp_manager, reasoning_engine, bookmark_system, cache_manager

    # Startup
    logger.info("Initializing MadSpark backend services...")

    # Log timeout configuration (configurable via environment variables)
    logger.info(f"Timeout configuration: DEFAULT={TimeoutConfig.DEFAULT_REQUEST_TIMEOUT}s "
                f"(override via MADSPARK_DEFAULT_TIMEOUT env var)")
    
    # Store application start time for uptime calculation
    app.state.start_time = datetime.now()
    
    try:
        temp_manager = TemperatureManager()
        
        # Initialize reasoning engine with genai_client if available
        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            reasoning_engine = ReasoningEngine(genai_client=genai_client)
            logger.info(f"ReasoningEngine initialized with genai_client: {genai_client is not None}")
        except Exception as e:
            logger.warning(f"Failed to initialize ReasoningEngine with genai_client: {e}")
            reasoning_engine = ReasoningEngine()
        
        bookmark_system = BookmarkManager()
        
        # Initialize cache manager
        cache_config = CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            ttl_seconds=int(os.getenv("CACHE_TTL", "3600")),
            max_cache_size_mb=int(os.getenv("CACHE_MAX_SIZE_MB", "100"))
        )
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize()
        
        logger.info("✅ MadSpark backend initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize MadSpark backend: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down MadSpark backend services...")
    if cache_manager:
        await cache_manager.close()


# Initialize FastAPI app

# Helper function for test initialization
def initialize_components_for_testing():
    """Initialize components for testing without running lifespan."""
    global temp_manager, reasoning_engine, bookmark_system, cache_manager
    
    if temp_manager is None:
        temp_manager = TemperatureManager()
    if reasoning_engine is None:
        # Initialize reasoning engine with genai_client if available
        try:
            from madspark.agents.genai_client import get_genai_client
            genai_client = get_genai_client()
            reasoning_engine = ReasoningEngine(genai_client=genai_client)
            logger.info(f"ReasoningEngine re-initialized with genai_client: {genai_client is not None}")
        except Exception as e:
            logger.warning(f"Failed to re-initialize ReasoningEngine with genai_client: {e}")
            reasoning_engine = ReasoningEngine()
    if bookmark_system is None:
        bookmark_system = BookmarkManager()
    
    # Set app start time for uptime calculation
    if not hasattr(app.state, 'start_time'):
        app.state.start_time = datetime.now()
    
    return {
        "temp_manager": temp_manager,
        "reasoning_engine": reasoning_engine,
        "bookmark_system": bookmark_system,
        "cache_manager": cache_manager
    }


app = FastAPI(
    title="MadSpark API",
    description="Web API for the MadSpark Multi-Agent Idea Generation System",
    version="2.2.0",
    lifespan=lifespan
)

# Initialize rate limiter (disabled in test/mock mode)
if os.getenv("MADSPARK_MODE") != "mock":
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
else:
    # Mock mode: create a no-op limiter for testing
    # Create a limiter with very high limits that effectively doesn't limit
    limiter = Limiter(key_func=get_remote_address, default_limits=["10000/minute"])
    app.state.limiter = limiter
    logging.info("Rate limiting disabled in mock/test mode (10000/minute)")

# Configure CORS
DEFAULT_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
cors_origins_str = os.getenv("MADSPARK_CORS_ORIGINS", "")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = DEFAULT_CORS_ORIGINS.copy()

if cors_origins == ["*"]:
    raise ValueError(
        "Invalid CORS configuration: MADSPARK_CORS_ORIGINS='*' is not allowed "
        "when allow_credentials=True. Use explicit origins instead."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware for large responses
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses larger than 1KB
    compresslevel=6     # Balanced compression level (1-9, 6 is good balance)
)

# Middleware to add security headers and session ID
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enhanced security headers middleware with comprehensive error handling."""
    # Generate a cryptographically secure session ID for each request
    # Using UUID4 for uniqueness and unpredictability
    request.state.session_id = str(uuid.uuid4())
    
    try:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS is only meaningful over HTTPS; check scheme and forwarded headers
        forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
        forwarded_ssl = request.headers.get("x-forwarded-ssl", "").strip().lower()
        is_https = (
            request.url.scheme == "https"
            or forwarded_proto == "https"
            or forwarded_ssl == "on"
        )
        if is_https:
            # preload is irreversible — only enable when explicitly configured for production
            hsts_preload = os.environ.get("HSTS_PRELOAD", "").strip().lower() == "true"
            hsts_value = "max-age=31536000; includeSubDomains"
            if hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )
        
        # Add session ID to response headers for client tracking if needed
        response.headers["X-Session-ID"] = request.state.session_id
        
        # Remove potentially sensitive server information
        if "server" in response.headers:
            del response.headers["server"]
        
        return response
        
    except Exception as e:
        # Enhanced error logging for middleware issues
        session_id = getattr(request.state, 'session_id', 'unknown')
        client_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')
        
        logging.error(
            f"Middleware error in security headers: {type(e).__name__}: {e}\n"
            f"Session ID: {session_id}\n"
            f"Client IP: {client_ip}\n"
            f"User Agent: {user_agent}\n"
            f"Request path: {request.url.path}\n"
            f"Request method: {request.method}",
            exc_info=True
        )
        
        # Re-raise the exception to maintain FastAPI's error handling behavior
        raise


# Pydantic models for API requests and responses
class IdeaGenerationRequest(BaseModel):
    """
    Request model for idea generation.

    Note on terminology for API backward compatibility:
    - 'topic' is the primary field name (previously 'theme')
    - 'context' is the primary field name (previously 'constraints')
    """
    topic: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Topic for idea generation",
        alias="theme"  # Backward compatibility
    )
    context: str = Field(
        default="Generate practical and innovative ideas",
        max_length=1000,
        description="Context and criteria (optional)",
        alias="constraints"  # Backward compatibility
    )
    num_top_candidates: int = Field(default=3, ge=1, le=5, description="Number of top ideas to process (max 5 for performance)")
    enable_novelty_filter: bool = Field(default=True, description="Enable novelty filtering")
    novelty_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Similarity threshold for novelty filter")
    temperature_preset: Optional[str] = Field(default=None, description="Temperature preset (conservative, balanced, creative, wild)")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Custom temperature value")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    enhanced_reasoning: bool = Field(default=False, description="Enable enhanced reasoning capabilities")
    multi_dimensional_eval: bool = Field(default=False, description="Use multi-dimensional evaluation")
    logical_inference: bool = Field(default=False, description="Enable logical inference chains")
    timeout: Optional[int] = Field(default=None, ge=60, le=3600, description="Request timeout in seconds (60-3600)")
    bookmark_ids: Optional[List[str]] = Field(default=None, description="Bookmark IDs to use for remix context")
    multimodal_urls: Optional[List[str]] = Field(
        default=None,
        max_items=5,
        description="URLs for multi-modal context (max 5 URLs)"
    )
    # LLM Router configuration
    llm_provider: Literal['auto', 'ollama', 'gemini'] = Field(
        default="auto",
        description="LLM provider selection (auto, ollama, gemini)"
    )
    model_tier: Literal['fast', 'balanced', 'quality'] = Field(
        default="fast",
        description="Model tier for inference (fast, balanced, quality)"
    )
    use_llm_cache: Optional[bool] = Field(
        default=True,
        description="Enable LLM response caching for cost optimization"
    )

    class Config:
        populate_by_name = True  # Accept both alias and original names (Pydantic V2)


class LLMMetrics(BaseModel):
    """LLM Router usage metrics."""
    total_requests: int = Field(default=0, description="Total LLM API requests")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    ollama_calls: int = Field(default=0, description="Number of Ollama API calls")
    gemini_calls: int = Field(default=0, description="Number of Gemini API calls")
    fallback_triggers: int = Field(default=0, description="Number of fallback triggers")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate (0.0-1.0)")
    avg_latency_ms: float = Field(default=0.0, description="Average latency in milliseconds")


class IdeaGenerationResponse(BaseModel):
    status: str
    message: str
    results: List[Dict[str, Any]]
    processing_time: float
    timestamp: str
    structured_output: bool = False  # Indicates if ideas are using structured output (no cleaning needed)
    llm_metrics: Optional[LLMMetrics] = Field(
        default=None,
        description="LLM Router usage metrics (tokens, cost, cache hits)"
    )


class BookmarkRequest(BaseModel):
    """
    Request model for creating a bookmark.

    Note on terminology for API backward compatibility:
    - 'topic' is the primary field name (previously 'theme')
    - 'context' is the primary field name (previously 'constraints')
    """
    idea: str = Field(..., min_length=10, max_length=10000, description="Original idea text")
    improved_idea: Optional[str] = Field(default=None, max_length=10000, description="Improved idea text")
    topic: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Topic used for generation",
        alias="theme"  # Backward compatibility
    )
    context: str = Field(
        default="",
        max_length=500,
        description="Context used",
        alias="constraints"  # Backward compatibility
    )
    initial_score: float = Field(..., ge=0, le=10, description="Initial critic score")
    improved_score: Optional[float] = Field(default=None, ge=0, le=10, description="Improved idea score")
    initial_critique: Optional[str] = Field(default=None, max_length=20000, description="Initial critique")
    improved_critique: Optional[str] = Field(default=None, max_length=20000, description="Improved critique")
    advocacy: Optional[str] = Field(default=None, max_length=20000, description="Advocate's arguments")
    skepticism: Optional[str] = Field(default=None, max_length=20000, description="Skeptic's analysis")
    tags: List[str] = Field(default=[], max_items=10, description="Tags for the bookmark")
    notes: Optional[str] = Field(default=None, max_length=500, description="Additional notes")

    class Config:
        populate_by_name = True  # Accept both alias and original names (Pydantic V2)
    
    @validator('idea', 'improved_idea', 'topic', 'context', 'initial_critique', 'improved_critique', 'advocacy', 'skepticism', 'notes')
    def sanitize_html(cls, v):
        if v is None:
            return None
        return html.escape(v.strip())
    
    @validator('tags')
    def sanitize_tags(cls, v):
        if not v:
            return []
        return [html.escape(tag.strip()[:50]) for tag in v if tag.strip()]


class BookmarkResponse(BaseModel):
    status: str
    message: str
    bookmark_id: Optional[str] = None


class SimilarBookmark(BaseModel):
    """Information about a similar bookmark."""
    id: str
    text: str
    topic: str  # Changed from 'theme' to match BookmarkedIdea model
    similarity_score: float
    match_type: str
    matched_features: List[str]


class DuplicateCheckRequest(BaseModel):
    """Request model for duplicate checking."""
    idea: str = Field(..., min_length=10, max_length=10000, description="Idea text to check for duplicates")
    topic: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Topic/theme of the idea",
        alias="theme"  # Backward compatibility
    )
    similarity_threshold: Optional[float] = Field(default=0.8, ge=0.1, le=1.0, description="Custom similarity threshold")

    class Config:
        populate_by_name = True

    @validator('idea', 'topic')
    def sanitize_html(cls, v):
        if v is None:
            return None
        return html.escape(v.strip())


class DuplicateCheckResponse(BaseModel):
    """Response model for duplicate checking."""
    status: str
    has_duplicates: bool
    similar_count: int
    recommendation: str  # 'block', 'warn', 'notice', 'allow'
    similarity_threshold: float
    similar_bookmarks: List[SimilarBookmark]
    message: str


class EnhancedBookmarkResponse(BaseModel):
    """Enhanced bookmark response with duplicate detection info."""
    status: str
    message: str
    bookmark_id: Optional[str] = None
    bookmark_created: bool
    duplicate_check: Optional[Dict[str, Any]] = None
    similar_bookmarks: List[SimilarBookmark] = []


def _create_success_response(
    results: List[Dict[str, Any]],
    start_time: datetime,
    message: str,
    llm_metrics: Optional[LLMMetrics] = None
) -> IdeaGenerationResponse:
    """Create a successful IdeaGenerationResponse with structured output detection.

    Args:
        results: Generated results from the coordinator containing idea data.
                Expected format: List of dicts with keys like 'idea', 'improved_idea',
                'initial_score', 'improved_score', etc.
        start_time: Request start time (datetime object) used to calculate the total
                   processing duration in seconds
        message: Success message to include in response (e.g., "Generated 5 ideas successfully")
        llm_metrics: Optional LLM router metrics (tokens, cost, cache hits, etc.)

    Returns:
        Formatted IdeaGenerationResponse with:
        - status: "success"
        - message: The provided success message
        - results: Frontend-formatted results with optional cleaning
        - processing_time: Duration in seconds
        - timestamp: ISO format timestamp
        - structured_output: Boolean flag indicating if structured output was used
        - llm_metrics: Optional LLM usage statistics
    """
    processing_time = (datetime.now() - start_time).total_seconds()
    structured_output_used = detect_structured_output_usage(results)

    # Log logical inference results
    logger.info(f"Creating success response with {len(results)} results")
    for i, result in enumerate(results):
        has_logical_inference = 'logical_inference' in result
        logger.info(f"Result {i}: has_logical_inference={has_logical_inference}")
        if has_logical_inference:
            logger.info(f"  Logical inference confidence: {result['logical_inference'].get('confidence', 'N/A')}")

    return IdeaGenerationResponse(
        status="success",
        message=message,
        results=format_results_for_frontend(results, structured_output_used),
        processing_time=processing_time,
        timestamp=start_time.isoformat(),
        structured_output=structured_output_used,
        llm_metrics=llm_metrics
    )


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_progress_update(self, message: str, progress: float = 0.0):
        """Send progress update to all connected clients using concurrent broadcasting."""
        if not self.active_connections:
            return
            
        update = {
            "type": "progress",
            "message": message,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        update_json = json.dumps(update)
        
        # Use concurrent sending to improve performance with many clients
        async def send_to_client(connection):
            try:
                await connection.send_text(update_json)
                return connection, True
            except Exception as e:
                # Catch all exceptions to ensure we always return a tuple
                logger.debug(f"WebSocket send failed for connection: {e}")
                return connection, False
        
        # Send to all connections concurrently
        results = await asyncio.gather(
            *[send_to_client(conn) for conn in self.active_connections],
            return_exceptions=False  # Changed to False since we handle exceptions in send_to_client
        )
        
        # Clean up disconnected connections
        disconnected = [conn for conn, success in results if not success]
        for conn in disconnected:
            self.disconnect(conn)


# Global WebSocket manager
ws_manager = WebSocketManager()


# Multi-modal file upload helper
async def save_upload_file(upload_file: UploadFile) -> Path:
    """Save uploaded file to temp directory with validation.

    Args:
        upload_file: FastAPI UploadFile object containing the uploaded file

    Returns:
        Path object pointing to the saved file

    Raises:
        HTTPException(413): File size exceeds limit
        HTTPException(400): Invalid file format or validation error
        HTTPException(500): File save operation failed
    """
    try:
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig
    except ImportError as e:
        logger.error(f"Failed to import multi-modal modules: {e}")
        raise HTTPException(
            status_code=500,
            detail="Multi-modal support not available"
        )

    # Validate file size before saving (initial check based on headers)
    file_size = getattr(upload_file, 'size', None)
    if file_size and file_size > MultiModalConfig.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {upload_file.filename} ({file_size} bytes). Maximum size: {MultiModalConfig.MAX_FILE_SIZE} bytes"
        )

    # Create temp directory
    temp_dir = Path("/tmp/madspark_uploads")
    temp_dir.mkdir(exist_ok=True)

    # Generate unique filename with traversal-safe basename
    safe_filename = os.path.basename(upload_file.filename or "upload.bin")
    temp_path = temp_dir / f"{uuid.uuid4()}_{safe_filename}"

    try:
        # Save file securely with chunked reading and incremental size validation
        total_size = 0

        async with await open_file(temp_path, "wb") as f:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > MultiModalConfig.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large: exceeded {MultiModalConfig.MAX_FILE_SIZE} bytes limit during upload"
                    )

                await f.write(chunk)

        # Validate using existing MultiModalInput
        mm_input = MultiModalInput()
        await asyncio.to_thread(mm_input.validate_file, temp_path)

        logger.info(f"Saved and validated file: {upload_file.filename} -> {temp_path}")
        return temp_path

    except ValueError as e:
        # Validation failed - clean up file if it was created
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

        logger.warning(f"File validation failed for {upload_file.filename}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"File validation failed: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like our 413 size limit)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        # File save failed - clean up if file was partially created
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

        logger.error(f"Failed to save file {upload_file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while saving file"
        )


@app.get("/")
async def root():
    """API root endpoint with system information."""
    return {
        "message": "MadSpark Multi-Agent System API",
        "version": "2.2.0",
        "status": "operational",
        "features": [
            "idea_generation",
            "enhanced_reasoning",
            "multi_dimensional_evaluation",
            "logical_inference",
            "bookmark_management",
            "real_time_updates"
        ]
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test core components
        temp_status = temp_manager is not None
        reasoning_status = reasoning_engine is not None
        bookmark_status = bookmark_system is not None
        
        # Calculate uptime
        uptime = 0
        if hasattr(app.state, 'start_time'):
            uptime = (datetime.now() - app.state.start_time).total_seconds()
        
        return {
            "status": "healthy" if all([temp_status, reasoning_status, bookmark_status]) else "degraded",
            "components": {
                "temperature_manager": temp_status,
                "reasoning_engine": reasoning_status,
                "bookmark_system": bookmark_status
            },
            "uptime": uptime,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_tracker.track_error('health_check_basic', str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Internal server error"}
        )


@app.get(
    "/api/temperature-presets",
    tags=["configuration"],
    summary="Get temperature presets",
    description=ENDPOINT_DESCRIPTIONS.get("get_temperature_presets", ""),
    responses={
        200: {
            "description": "Temperature presets retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "presets": {
                            "conservative": {
                                "idea_generation": 0.3,
                                "evaluation": 0.2,
                                "advocacy": 0.4,
                                "skepticism": 0.6,
                                "description": "Low creativity, focused on practical ideas"
                            },
                            "balanced": {
                                "idea_generation": 0.7,
                                "evaluation": 0.5,
                                "advocacy": 0.6,
                                "skepticism": 0.5,
                                "description": "Moderate creativity (default)"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_temperature_presets():
    """Get available temperature presets."""
    try:
        # Convert TemperatureConfig objects to dicts for JSON serialization
        presets_dict = {}
        for name, config in TemperatureManager.PRESETS.items():
            presets_dict[name] = {
                "base_temperature": config.base_temperature,
                "idea_generation": config.idea_generation,
                "evaluation": config.evaluation,
                "advocacy": config.advocacy,
                "skepticism": config.skepticism,
                "description": f"{name.capitalize()} temperature settings"
            }
        
        return {
            "status": "success",
            "presets": presets_dict,
            "default": "balanced"
        }
    except Exception as e:
        logger.error(f"Failed to get temperature presets: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# LLM Router endpoints
@app.get(
    "/api/llm/health",
    tags=["llm"],
    summary="Get LLM provider health status",
    description="Check availability and health of LLM providers (Ollama, Gemini)"
)
async def get_llm_health():
    """Get LLM provider health status."""
    if not LLM_ROUTER_AVAILABLE or get_router is None:
        return {
            "status": "unavailable",
            "message": "LLM Router not available",
            "providers": {}
        }

    try:
        router = get_router()
        health = router.health_status()
        return {
            "status": "available",
            "providers": health
        }
    except Exception as e:
        logger.error(f"Failed to get LLM health: {e}")
        return {
            "status": "error",
            "message": "Internal server error",
            "providers": {}
        }


@app.get(
    "/api/llm/metrics",
    tags=["llm"],
    summary="Get LLM usage metrics",
    description="Get router usage statistics including tokens, cost, and cache hits"
)
async def get_llm_metrics():
    """Get LLM router usage metrics."""
    if not LLM_ROUTER_AVAILABLE or get_router is None:
        return {
            "status": "unavailable",
            "message": "LLM Router not available",
            "metrics": {}
        }

    try:
        router = get_router()
        metrics = router.get_metrics()
        return {
            "status": "success",
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get LLM metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post(
    "/api/llm/cache/clear",
    tags=["llm"],
    summary="Clear LLM response cache",
    description="Clear the LLM response cache to force fresh API calls"
)
async def clear_llm_cache():
    """Clear LLM response cache."""
    if not LLM_ROUTER_AVAILABLE or reset_llm_cache is None:
        return {
            "status": "unavailable",
            "message": "LLM Router cache not available"
        }

    try:
        reset_llm_cache()
        return {
            "status": "success",
            "message": "LLM cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Failed to clear LLM cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/api/llm/providers",
    tags=["llm"],
    summary="Get available LLM providers",
    description="List available LLM providers and their configurations"
)
async def get_llm_providers():
    """Get available LLM providers and configurations."""
    return {
        "status": "success",
        "providers": [
            {
                "id": "auto",
                "name": "Auto (Ollama-first)",
                "description": "Automatically selects Ollama (free) with Gemini fallback"
            },
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "description": "Local inference using Ollama (free, requires Ollama server)"
            },
            {
                "id": "gemini",
                "name": "Gemini (Cloud)",
                "description": "Cloud inference using Google Gemini API (paid)"
            }
        ],
        "model_tiers": [
            {
                "id": "fast",
                "name": "Fast",
                "description": "Quick responses with gemma3:4b (Ollama)"
            },
            {
                "id": "balanced",
                "name": "Balanced",
                "description": "Better quality with gemma3:12b (Ollama)"
            },
            {
                "id": "quality",
                "name": "Quality",
                "description": "Best quality with larger models"
            }
        ],
        "router_available": LLM_ROUTER_AVAILABLE
    }


async def parse_idea_request(idea_request: Optional[str], request: Request) -> IdeaGenerationRequest:
    """
    Helper function to parse IdeaGenerationRequest from either FormData or JSON body.

    Args:
        idea_request: Optional JSON string from FormData field
        request: FastAPI Request object for JSON body access

    Returns:
        Parsed and validated IdeaGenerationRequest

    Raises:
        HTTPException: For JSON parsing errors
        RequestValidationError: For Pydantic validation errors
    """
    if idea_request:
        # FormData submission with files
        try:
            request_data = json.loads(idea_request)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON in FormData 'idea_request' field: {str(e)}")
        try:
            return IdeaGenerationRequest(**request_data)
        except PydanticValidationError as e:
            # Let Pydantic validation errors pass through for proper FastAPI formatting
            raise RequestValidationError(e.errors())
    else:
        # JSON submission without files - parse from request body
        try:
            body = await request.body()
            if not body:
                raise HTTPException(status_code=422, detail="Request body is required")
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=422, detail=f"Invalid JSON in request body: {str(e)}")
        try:
            return IdeaGenerationRequest(**request_data)
        except PydanticValidationError as e:
            # Let Pydantic validation errors pass through for proper FastAPI formatting
            raise RequestValidationError(e.errors())

@app.post(
    "/api/generate-ideas",
    response_model=IdeaGenerationResponse,
    tags=["idea-generation"],
    summary="Generate creative ideas",
    description=ENDPOINT_DESCRIPTIONS.get("generate_ideas", ""),
    responses={
        200: {
            "description": "Ideas generated successfully",
            "content": {
                "application/json": {
                    "example": API_EXAMPLES.get("idea_generation_response", {}).get("value", {})
                }
            }
        },
        422: {"$ref": "#/components/responses/ValidationError"},
        429: {"$ref": "#/components/responses/RateLimitError"},
        500: {"description": "Internal server error"}
    }
)
@limiter.limit("5/minute")  # Allow 5 idea generation requests per minute
async def generate_ideas(
    request: Request,
    idea_request: Optional[str] = Form(
        None,
        description="JSON string of IdeaGenerationRequest (for FormData uploads). Omit for JSON requests."
    ),
    multimodal_files: Optional[List[UploadFile]] = File(
        None,
        description="PDF/document files for multi-modal context (triggers FormData mode)"
    ),
    multimodal_images: Optional[List[UploadFile]] = File(
        None,
        description="Image files for multi-modal context (triggers FormData mode)"
    )
):
    """Generate ideas using the async MadSpark multi-agent workflow with optional multi-modal inputs.

    Note: This endpoint handles both JSON and FormData requests automatically.
    Request format is determined by parameter presence (not Content-Type header) for robustness:
    - If 'idea_request' Form parameter exists → FormData mode (with files)
    - If 'idea_request' is None → JSON mode (request body)
    """
    start_time = datetime.now()
    temp_files = []  # Track temp files for cleanup

    # Parse request using helper function (DRY principle)
    parsed_request = await parse_idea_request(idea_request, request)

    # Check if running in mock mode - check environment variable properly
    if _is_mock_mode():
        logger.info("Running in mock mode - returning sample results")
        mock_results = generate_mock_results(parsed_request.topic, parsed_request.num_top_candidates, parsed_request.logical_inference)
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(mock_results)} mock ideas",
            results=format_results_for_frontend(mock_results, structured_output_used=False),
            processing_time=0.5,
            timestamp=start_time.isoformat(),
            structured_output=False
        )
    
    try:
        # Define progress callback
        async def progress_callback(message: str, progress: float):
            await ws_manager.send_progress_update(message, progress)
        
        # Setup temperature manager
        if parsed_request.temperature_preset:
            temp_mgr = TemperatureManager.from_preset(parsed_request.temperature_preset)
        elif parsed_request.temperature:
            temp_mgr = TemperatureManager.from_base_temperature(parsed_request.temperature)
        else:
            temp_mgr = temp_manager or TemperatureManager()

        # Parse and validate MAX_CONCURRENT_AGENTS environment variable
        max_concurrent_agents = 10  # default
        env_val = os.getenv("MAX_CONCURRENT_AGENTS", "10")
        if env_val.isdigit():
            parsed_val = int(env_val)
            if parsed_val > 0:
                max_concurrent_agents = parsed_val
            else:
                logger.warning(f"MAX_CONCURRENT_AGENTS must be > 0, got {parsed_val}. Using default: 10")
        else:
            logger.warning(f"MAX_CONCURRENT_AGENTS must be a positive integer, got '{env_val}'. Using default: 10")
        
        # Handle remix context if bookmark IDs are provided
        context = parsed_request.context
        if parsed_request.bookmark_ids:
            if bookmark_system is None:
                logger.warning("bookmark_system is not initialized; skipping remix context")
            else:
                try:
                    from madspark.utils.bookmark_system import remix_with_bookmarks
                    context = await asyncio.to_thread(
                        remix_with_bookmarks,
                        topic=parsed_request.topic,
                        context=parsed_request.context,
                        bookmark_ids=parsed_request.bookmark_ids,
                        bookmark_file=bookmark_system.bookmark_file
                    )
                    await ws_manager.send_progress_update(f"Using {len(parsed_request.bookmark_ids)} bookmarks for remix context", 5.0)
                except Exception as e:
                    logger.warning(f"Failed to create remix context: {e}")
                    # Continue with original context if remix fails

        # Handle multi-modal file uploads
        multimodal_file_paths = []
        multimodal_url_list = parsed_request.multimodal_urls or []

        # Validate URLs for SSRF protection
        if multimodal_url_list:
            from madspark.utils.multimodal_input import MultiModalInput
            mm_input = MultiModalInput()
            for url in multimodal_url_list:
                try:
                    mm_input.validate_url(url)
                except ValueError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid URL: {str(e)}"
                    )

        try:
            # Process uploaded files
            if multimodal_files:
                for file in multimodal_files:
                    try:
                        temp_path = await save_upload_file(file)
                        temp_files.append(temp_path)
                        multimodal_file_paths.append(temp_path)
                        logger.info(f"Processed file upload: {file.filename}")
                    except HTTPException as e:
                        # Track file-specific errors
                        error_tracker.track_error('file_upload_validation', str(e.detail), {
                            'filename': file.filename,
                            'status_code': e.status_code
                        })
                        raise

            # Process uploaded images
            if multimodal_images:
                for file in multimodal_images:
                    try:
                        temp_path = await save_upload_file(file)
                        temp_files.append(temp_path)
                        multimodal_file_paths.append(temp_path)
                        logger.info(f"Processed image upload: {file.filename}")
                    except HTTPException as e:
                        # Track file-specific errors
                        error_tracker.track_error('file_upload_validation', str(e.detail), {
                            'filename': file.filename,
                            'status_code': e.status_code
                        })
                        raise

            # Log multi-modal inputs
            if multimodal_file_paths or multimodal_url_list:
                await ws_manager.send_progress_update(
                    f"Processing multi-modal inputs: {len(multimodal_file_paths)} files, {len(multimodal_url_list)} URLs",
                    3.0
                )

        except HTTPException:
            # Clean up temp files on error
            for temp_file in temp_files:
                try:
                    temp_file.unlink(missing_ok=True)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")
            raise

        # Create request-scoped router for thread-safe configuration
        request_router = create_request_router(parsed_request)

        # Create async coordinator with cache, progress callback, and request-scoped router
        async_coordinator = AsyncCoordinator(
            max_concurrent_agents=max_concurrent_agents,
            progress_callback=progress_callback,
            cache_manager=cache_manager,
            router=request_router,  # Pass request-scoped router for thread safety
        )

        # Add timeout handling
        # TimeoutConfig.DEFAULT_REQUEST_TIMEOUT is configurable via MADSPARK_DEFAULT_TIMEOUT env var
        timeout_seconds = parsed_request.timeout if parsed_request.timeout else TimeoutConfig.DEFAULT_REQUEST_TIMEOUT
        logger.info(f"Request timeout configured: {timeout_seconds}s (env override: MADSPARK_DEFAULT_TIMEOUT)")

        # Log workflow configuration
        logger.info(f"Running workflow: logical_inference={parsed_request.logical_inference}, "
                    f"provider={parsed_request.llm_provider or 'auto'}, "
                    f"tier={parsed_request.model_tier or 'balanced'}")

        try:
            try:
                results = await asyncio.wait_for(
                    async_coordinator.run_workflow(
                        topic=parsed_request.topic,
                        context=context,  # Use potentially remixed context
                        num_top_candidates=parsed_request.num_top_candidates,
                        enable_novelty_filter=parsed_request.enable_novelty_filter,
                        novelty_threshold=parsed_request.novelty_threshold,
                        temperature_manager=temp_mgr,
                        verbose=parsed_request.verbose,
                        enhanced_reasoning=parsed_request.enhanced_reasoning,
                        multi_dimensional_eval=True,  # Always enabled as a core feature
                        logical_inference=parsed_request.logical_inference,
                        # NOTE: reasoning_engine intentionally NOT passed
                        # Let async_coordinator create it with router for batch operations
                        multimodal_files=multimodal_file_paths if multimodal_file_paths else None,
                        multimodal_urls=multimodal_url_list if multimodal_url_list else None
                    ),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                await ws_manager.send_progress_update(f"Request timed out after {timeout_seconds} seconds", 0.0)
                raise HTTPException(
                    status_code=408,
                    detail=f"Request timed out after {timeout_seconds} seconds. Please try with fewer candidates or simpler constraints."
                )

            # Capture LLM metrics if router is available
            llm_metrics = None
            if LLM_ROUTER_AVAILABLE:
                try:
                    # Use request-scoped router for metrics (not singleton)
                    metrics_router = request_router if request_router is not None else get_router()
                    metrics = metrics_router.get_metrics()
                    llm_metrics = LLMMetrics(
                        total_requests=metrics.get("total_requests", 0),
                        cache_hits=metrics.get("cache_hits", 0),
                        ollama_calls=metrics.get("ollama_calls", 0),
                        gemini_calls=metrics.get("gemini_calls", 0),
                        fallback_triggers=metrics.get("fallback_triggers", 0),
                        total_tokens=metrics.get("total_tokens", 0),
                        total_cost=metrics.get("total_cost", 0.0),
                        cache_hit_rate=metrics.get("cache_hit_rate", 0.0),
                        avg_latency_ms=metrics.get("avg_latency_ms", 0.0)
                    )
                    logger.info(f"LLM metrics captured: {llm_metrics}")
                except Exception as metrics_error:
                    logger.warning(f"Failed to capture LLM metrics: {metrics_error}")

            return _create_success_response(
                results=results,
                start_time=start_time,
                message=f"Generated {len(results)} ideas successfully",
                llm_metrics=llm_metrics
            )
        finally:
            # Clean up temp files after processing (success or failure)
            for temp_file in temp_files:
                try:
                    temp_file.unlink(missing_ok=True)
                    logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file {temp_file}: {cleanup_error}")
        
    except HTTPException:
        # Re-raise HTTP exceptions (like timeout)
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        # Safe error logging: parsed_request may not be initialized if parsing failed
        topic_for_logging = getattr(parsed_request, 'topic', '[UNKNOWN]') if 'parsed_request' in locals() else '[UNKNOWN]'
        num_candidates_for_logging = getattr(parsed_request, 'num_top_candidates', 0) if 'parsed_request' in locals() else 0
        error_context = {
            'topic': topic_for_logging,
            'num_candidates': num_candidates_for_logging,
            'processing_time': processing_time,
            'error_type': type(e).__name__
        }
        
        error_tracker.track_error('idea_generation', str(e), error_context)
        await ws_manager.send_progress_update("Error: An internal error occurred during idea generation.", 0.0)
        
        # Provide more detailed error information (sanitized for user)
        # SECURE: Do not leak exception details to user
        error_detail = {
            "error": "An internal error occurred during idea generation.",
            "type": "InternalServerError",
        }
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/generate-ideas-async", response_model=IdeaGenerationResponse)
@limiter.limit("5/minute")  # Allow 5 async idea generation requests per minute
async def generate_ideas_async(request: Request, idea_request: IdeaGenerationRequest):
    """Generate ideas using the async MadSpark workflow for better performance."""
    start_time = datetime.now()

    # Check if running in mock mode - check environment variable properly
    if _is_mock_mode():
        logger.info("Running in mock mode (async) - returning sample results")
        mock_results = generate_mock_results(idea_request.topic, idea_request.num_top_candidates, idea_request.logical_inference)
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(mock_results)} mock ideas (async)",
            results=format_results_for_frontend(mock_results, structured_output_used=False),
            processing_time=0.5,
            timestamp=start_time.isoformat(),
            structured_output=False
        )

    # Define progress callback
    async def progress_callback(message: str, progress: float):
        await ws_manager.send_progress_update(message, progress)

    # Setup temperature manager
    if idea_request.temperature_preset:
        temp_mgr = TemperatureManager.from_preset(idea_request.temperature_preset)
    elif idea_request.temperature:
        temp_mgr = TemperatureManager.from_base_temperature(idea_request.temperature)
    else:
        temp_mgr = temp_manager or TemperatureManager()

    # Parse and validate MAX_CONCURRENT_AGENTS environment variable
    max_concurrent_agents = 10  # default
    env_val = os.getenv("MAX_CONCURRENT_AGENTS", "10")
    if env_val.isdigit():
        parsed_val = int(env_val)
        if parsed_val > 0:
            max_concurrent_agents = parsed_val
        else:
            logger.warning(f"MAX_CONCURRENT_AGENTS must be > 0, got {parsed_val}. Using default: 10")
    else:
        logger.warning(f"MAX_CONCURRENT_AGENTS must be a positive integer, got '{env_val}'. Using default: 10")

    # Create request-scoped router for thread-safe configuration
    request_router = create_request_router(idea_request)

    # Create async coordinator with cache and request-scoped router
    async_coordinator = AsyncCoordinator(
        max_concurrent_agents=max_concurrent_agents,
        progress_callback=progress_callback,
        cache_manager=cache_manager,
        router=request_router,  # Pass request-scoped router for thread safety
    )

    try:

        # Process and validate multimodal URLs if provided (async endpoint supports URLs only, not file uploads)
        multimodal_url_list = None
        if idea_request.multimodal_urls:
            from madspark.utils.multimodal_input import MultiModalInput
            multimodal_url_list = []
            mm_input = MultiModalInput()
            for url in idea_request.multimodal_urls:
                try:
                    mm_input.validate_url(url)
                    multimodal_url_list.append(url)
                except ValueError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid multimodal URL: {str(e)}"
                    )

        # Run the async workflow with router config and multimodal support
        results = await async_coordinator.run_workflow(
            topic=idea_request.topic,
            context=idea_request.context,
            num_top_candidates=idea_request.num_top_candidates,
            enable_novelty_filter=idea_request.enable_novelty_filter,
            novelty_threshold=idea_request.novelty_threshold,
            temperature_manager=temp_mgr,
            verbose=idea_request.verbose,
            enhanced_reasoning=idea_request.enhanced_reasoning,
            multi_dimensional_eval=True,  # Always enabled as a core feature
            logical_inference=idea_request.logical_inference,
            # NOTE: reasoning_engine intentionally NOT passed
            # Let async_coordinator create it with router for batch operations
            multimodal_files=None,  # Async endpoint does not support file uploads
            multimodal_urls=multimodal_url_list
        )

        # Capture LLM metrics if router is available (same as sync endpoint)
        llm_metrics = None
        if LLM_ROUTER_AVAILABLE:
            try:
                # Use request-scoped router for metrics (not singleton)
                metrics_router = request_router if request_router is not None else get_router()
                metrics = metrics_router.get_metrics()
                llm_metrics = LLMMetrics(
                    total_requests=metrics.get("total_requests", 0),
                    cache_hits=metrics.get("cache_hits", 0),
                    ollama_calls=metrics.get("ollama_calls", 0),
                    gemini_calls=metrics.get("gemini_calls", 0),
                    fallback_triggers=metrics.get("fallback_triggers", 0),
                    total_tokens=metrics.get("total_tokens", 0),
                    total_cost=metrics.get("total_cost", 0.0),
                    cache_hit_rate=metrics.get("cache_hit_rate", 0.0),
                    avg_latency_ms=metrics.get("avg_latency_ms", 0.0)
                )
                logger.info(f"Async LLM metrics captured: {llm_metrics}")
            except Exception as metrics_error:
                logger.warning(f"Failed to capture async LLM metrics: {metrics_error}")

        return _create_success_response(
            results=results,
            start_time=start_time,
            message=f"Generated {len(results)} ideas successfully (async)",
            llm_metrics=llm_metrics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Async idea generation failed: {e}")
        await ws_manager.send_progress_update("Error: An internal error occurred.", 0.0)
        # SECURE: Generic error for user
        raise HTTPException(status_code=500, detail="An internal error occurred.")
    finally:
        # Router cleanup not needed - request-scoped router will be garbage collected
        pass


@app.post(
    "/api/bookmarks/check-duplicates", 
    response_model=DuplicateCheckResponse,
    tags=["bookmarks"],
    summary="Check for duplicate ideas",
    description=ENDPOINT_DESCRIPTIONS.get("check_duplicates", ""),
    responses={
        200: {
            "description": "Duplicate check completed",
            "content": {
                "application/json": {
                    "examples": {
                        "no_duplicates": API_EXAMPLES.get("duplicate_check", {}).get("response_no_duplicates", {}),
                        "with_duplicates": API_EXAMPLES.get("duplicate_check", {}).get("response_with_duplicates", {})
                    }
                }
            }
        },
        422: {"$ref": "#/components/responses/ValidationError"},
        429: {"$ref": "#/components/responses/RateLimitError"}
    }
)
@limiter.limit("15/minute")  # Allow 15 duplicate checks per minute
async def check_bookmark_duplicates(request: Request, duplicate_request: DuplicateCheckRequest):
    """Check for potential duplicate bookmarks."""
    try:
        # Initialize bookmark manager with custom similarity threshold if provided
        if duplicate_request.similarity_threshold:
            bookmark_manager = BookmarkManager(
                bookmark_system.bookmark_file, 
                duplicate_request.similarity_threshold
            )
        else:
            bookmark_manager = bookmark_system
        
        # Check for duplicates
        duplicate_result = bookmark_manager.check_for_duplicates(
            duplicate_request.idea,
            duplicate_request.topic
        )
        
        # Convert to API response format
        similar_bookmarks = []
        for similar in duplicate_result.similar_bookmarks:
            bookmark = bookmark_manager.get_bookmark(similar.bookmark_id)
            if bookmark:
                similar_bookmarks.append(SimilarBookmark(
                    id=similar.bookmark_id,
                    text=bookmark.text[:300] + '...' if len(bookmark.text) > 300 else bookmark.text,
                    topic=bookmark.topic,
                    similarity_score=similar.similarity_score,
                    match_type=similar.match_type,
                    matched_features=similar.matched_features
                ))
        
        # Generate appropriate message
        message = "No similar bookmarks found."
        if duplicate_result.recommendation == "block":
            message = f"Potential duplicate detected! Found {len(similar_bookmarks)} very similar bookmark(s)."
        elif duplicate_result.recommendation == "warn":
            message = f"Similar bookmarks found. Found {len(similar_bookmarks)} bookmark(s) with high similarity."
        elif duplicate_result.recommendation == "notice":
            message = f"Some similar bookmarks found. Found {len(similar_bookmarks)} bookmark(s) with moderate similarity."
        
        return DuplicateCheckResponse(
            status="success",
            has_duplicates=duplicate_result.has_duplicates,
            similar_count=len(similar_bookmarks),
            recommendation=duplicate_result.recommendation,
            similarity_threshold=duplicate_result.similarity_threshold,
            similar_bookmarks=similar_bookmarks,
            message=message
        )
        
    except Exception as e:
        error_context = {
            'idea_length': len(duplicate_request.idea),
            'topic': duplicate_request.topic,
            'error_type': type(e).__name__
        }
        error_tracker.track_error('duplicate_check', str(e), error_context)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/bookmarks/similar")
@limiter.limit("20/minute")  # Allow 20 similarity searches per minute
async def find_similar_bookmarks(
    request: Request,
    idea: str = Query(..., min_length=10, description="Idea text to find similar bookmarks for"),
    topic: Optional[str] = Query(None, min_length=1, description="Topic of the idea"),
    theme: Optional[str] = Query(None, min_length=1, description="(Deprecated: use 'topic') Theme of the idea", alias="theme"),  # Backward compatibility
    max_results: int = Query(default=5, ge=1, le=20, description="Maximum number of results")
):
    """Find bookmarks similar to the given idea text."""
    # Handle backward compatibility: use topic if provided, otherwise fall back to theme
    actual_topic = topic or theme
    if not actual_topic:
        raise HTTPException(status_code=422, detail="Either 'topic' or 'theme' parameter is required")

    try:
        similar_bookmarks_data = bookmark_system.find_similar_bookmarks(
            idea, actual_topic, max_results
        )

        # Convert to API response format
        similar_bookmarks = []
        for bookmark_data in similar_bookmarks_data:
            similar_bookmarks.append(SimilarBookmark(
                id=bookmark_data['id'],
                text=bookmark_data['text'][:300] + '...' if len(bookmark_data['text']) > 300 else bookmark_data['text'],
                topic=bookmark_data['topic'],  # Changed from 'theme' to 'topic'
                similarity_score=bookmark_data['similarity_score'],
                match_type=bookmark_data['match_type'],
                matched_features=bookmark_data['matched_features']
            ))

        return {
            "status": "success",
            "similar_bookmarks": similar_bookmarks,
            "total_found": len(similar_bookmarks),
            "search_idea": idea[:100] + '...' if len(idea) > 100 else idea
        }

    except Exception as e:
        error_context = {
            'idea_length': len(idea),
            'topic': topic,  # Changed from 'theme' to 'topic'
            'max_results': max_results,
            'error_type': type(e).__name__
        }
        error_tracker.track_error('similar_search', str(e), error_context)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/bookmarks")
@limiter.limit("30/minute")  # Allow 30 requests per minute for reading bookmarks
async def get_bookmarks(request: Request, tags: Optional[str] = None):
    """Get all bookmarks, optionally filtered by tags."""
    try:
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            bookmarks = bookmark_system.list_bookmarks(tags=tag_list)
        else:
            bookmarks = bookmark_system.list_bookmarks()
        
        # Convert BookmarkedIdea objects to dicts
        bookmark_dicts = []
        for bookmark in bookmarks:
            bookmark_dicts.append({
                "id": bookmark.id,
                "text": bookmark.text,
                "topic": bookmark.topic,  # Changed from 'theme' to match BookmarkedIdea model
                "context": bookmark.context,  # Changed from 'constraints' to match BookmarkedIdea model
                "score": bookmark.score,
                "critique": bookmark.critique,
                "advocacy": bookmark.advocacy,
                "skepticism": bookmark.skepticism,
                "bookmarked_at": bookmark.bookmarked_at,
                "tags": bookmark.tags
            })
        
        return {
            "status": "success",
            "bookmarks": bookmark_dicts,
            "count": len(bookmark_dicts)
        }
    except Exception as e:
        logger.error(f"Failed to get bookmarks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/bookmarks", response_model=EnhancedBookmarkResponse)
@limiter.limit("10/minute")  # Allow 10 bookmark creations per minute
async def create_bookmark(
    request: Request, 
    bookmark_request: BookmarkRequest,
    check_duplicates: bool = Query(default=True, description="Enable duplicate detection"),
    force_save: bool = Query(default=False, description="Force save even if duplicates found")
):
    """Create a new bookmark with optional duplicate detection."""
    try:
        # Log the request for debugging (sanitized for security)
        sanitized_topic = sanitize_for_logging(bookmark_request.topic, 30)
        logger.info(f"Bookmark request received for topic='{sanitized_topic}' with {len(bookmark_request.tags)} tags.")
        
        # Use improved idea if available, otherwise use original
        idea_text = bookmark_request.improved_idea if bookmark_request.improved_idea is not None else bookmark_request.idea
        score = bookmark_request.improved_score if bookmark_request.improved_score is not None else bookmark_request.initial_score
        critique = bookmark_request.improved_critique if bookmark_request.improved_critique is not None else bookmark_request.initial_critique
        
        if check_duplicates:
            # Use enhanced bookmark creation with duplicate detection
            result = bookmark_system.bookmark_idea_with_duplicate_check(
                idea_text=idea_text,
                topic=bookmark_request.topic,
                context=bookmark_request.context,
                score=round(score, 1),
                critique=critique or "",
                advocacy=bookmark_request.advocacy or "",
                skepticism=bookmark_request.skepticism or "",
                tags=bookmark_request.tags,
                force_save=force_save
            )
            
            # Convert similar bookmarks to API format
            similar_bookmarks = []
            for similar in result['similar_bookmarks']:
                similar_bookmarks.append(SimilarBookmark(
                    id=similar['id'],
                    text=similar['text'],
                    topic=similar['topic'],  # Changed from 'theme' to match BookmarkedIdea model
                    similarity_score=similar['similarity_score'],
                    match_type=similar['match_type'],
                    matched_features=[]  # Simplified for API response
                ))
            
            return EnhancedBookmarkResponse(
                status="success" if result['bookmark_created'] else "warning",
                message=result['message'],
                bookmark_id=result['bookmark_id'],
                bookmark_created=result['bookmark_created'],
                duplicate_check=result['duplicate_check'],
                similar_bookmarks=similar_bookmarks
            )
        else:
            # Traditional bookmark creation without duplicate checking
            bookmark_id = bookmark_system.bookmark_idea(
                idea_text=idea_text,
                topic=bookmark_request.topic,
                context=bookmark_request.context,
                score=round(score, 1),
                critique=critique or "",
                advocacy=bookmark_request.advocacy or "",
                skepticism=bookmark_request.skepticism or "",
                tags=bookmark_request.tags
            )
            
            return EnhancedBookmarkResponse(
                status="success",
                message="Bookmark created successfully (duplicate checking disabled)",
                bookmark_id=bookmark_id,
                bookmark_created=True,
                duplicate_check=None,
                similar_bookmarks=[]
            )
            
    except RequestValidationError as e:
        logger.error(f"Validation error in bookmark request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        error_context = {
            'topic': bookmark_request.topic,
            'idea_length': len(bookmark_request.idea),
            'tags_count': len(bookmark_request.tags),
            'check_duplicates': check_duplicates,
            'force_save': force_save,
            'error_type': type(e).__name__
        }
        
        error_tracker.track_error('bookmark_creation', str(e), error_context)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/api/bookmarks/{bookmark_id}")
@limiter.limit("20/minute")  # Allow 20 bookmark deletions per minute
async def delete_bookmark(request: Request, bookmark_id: str):
    """Delete a bookmark by ID."""
    try:
        success = bookmark_system.remove_bookmark(bookmark_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Bookmark {bookmark_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Bookmark {bookmark_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        error_context = {
            'bookmark_id': bookmark_id,
            'error_type': type(e).__name__
        }
        
        error_tracker.track_error('bookmark_deletion', str(e), error_context)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        if not cache_manager:
            return {
                "status": "disabled",
                "message": "Cache manager not initialized"
            }
        
        stats = await cache_manager.get_cache_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None):
    """Invalidate cache entries matching pattern."""
    try:
        if not cache_manager:
            return {
                "status": "error",
                "message": "Cache manager not initialized"
            }
        
        if pattern:
            deleted = await cache_manager.invalidate_cache(pattern)
            return {
                "status": "success",
                "message": f"Invalidated {deleted} cache entries matching pattern: {pattern}"
            }
        else:
            success = await cache_manager.clear_all_cache()
            return {
                "status": "success" if success else "error",
                "message": "All cache cleared" if success else "Failed to clear cache"
            }
            
    except Exception as e:
        error_tracker.track_error('cache_invalidation', str(e), {'pattern': pattern})
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/system/errors")
async def get_error_stats():
    """Get error statistics for debugging."""
    try:
        stats = error_tracker.get_error_stats()
        sanitized_recent_errors = []
        for error in stats.get("recent_errors", []):
            sanitized_error = dict(error)
            if "message" in sanitized_error:
                sanitized_error["message"] = "[REDACTED]"
            sanitized_recent_errors.append(sanitized_error)

        sanitized_stats = dict(stats)
        sanitized_stats["recent_errors"] = sanitized_recent_errors

        return {
            "status": "success",
            "error_stats": sanitized_stats,
            "system_info": {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - app.state.start_time).total_seconds() if hasattr(app.state, 'start_time') else 0,
                "environment": os.getenv('ENVIRONMENT', 'development')
            }
        }
    except Exception as e:
        logger.error(f"Failed to get error stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/system/health")
async def detailed_health_check():
    """Detailed health check with component status."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "temperature_manager": temp_manager is not None,
                "reasoning_engine": reasoning_engine is not None,
                "bookmark_system": bookmark_system is not None,
                "cache_manager": cache_manager is not None,
                "websocket_manager": ws_manager is not None
            },
            "error_stats": error_tracker.get_error_stats()['total_errors'],
            "memory_usage": {
                "cache_enabled": cache_manager is not None,
                "log_entries": len(error_tracker.errors)
            }
        }
        
        # Check if any critical components are missing
        critical_components = ['temperature_manager', 'reasoning_engine', 'bookmark_system']
        if not all(health_status['components'][comp] for comp in critical_components):
            health_status['status'] = 'degraded'
        
        return health_status
        
    except Exception as e:
        error_tracker.track_error('health_check', str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
        )


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates with security controls."""
    try:
        # Security: Check connection limits to prevent abuse
        if len(ws_manager.active_connections) >= 100:  # Configurable limit
            await websocket.close(code=1008, reason="Connection limit exceeded")
            return
            
        # Security: Basic authentication via query parameter
        # In production, use proper JWT token validation
        client_id = websocket.query_params.get("client_id", "anonymous")
        if not client_id or len(client_id) < 4:
            await websocket.close(code=1008, reason="Invalid client identification")
            return
        
        await ws_manager.connect(websocket)
        
        # Send initial connection confirmation with security info
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "WebSocket connected successfully",
            "client_id": client_id,
            "connections": len(ws_manager.active_connections),
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            try:
                # Wait for ping messages or other client data
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong for keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Echo back other messages for testing
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "message": f"Received: {data}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except asyncio.TimeoutError:
                # Send keep-alive ping to detect disconnections
                try:
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.info(f"WebSocket connection lost during ping: {e}")
                    break
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected normally")
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")
                # Don't break on minor errors, continue listening
                continue
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected during connection")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        ws_manager.disconnect(websocket)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Apply customizations from openapi_enhancements
    customizations = get_openapi_customization()
    
    # Update info section
    if "info" in customizations:
        openapi_schema["info"].update(customizations["info"])
    
    # Add servers
    if "servers" in customizations:
        openapi_schema["servers"] = customizations["servers"]
    
    # Add tags
    if "tags" in customizations:
        openapi_schema["tags"] = customizations["tags"]
    
    # Update components
    if "components" in customizations:
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        openapi_schema["components"].update(customizations["components"])
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Override the default OpenAPI function
app.openapi = custom_openapi


# Test support endpoint
@app.post("/test/init", include_in_schema=False)
async def initialize_for_testing():
    """Initialize components for testing - not for production use."""
    components = initialize_components_for_testing()
    return {"status": "initialized", "components": list(components.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
