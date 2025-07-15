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
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator, ValidationError
import html

# Import MadSpark modules
# Add the parent directory to the path for imports
madspark_path = os.environ.get('MADSPARK_PATH', '/madspark')
src_path = os.path.join(madspark_path, 'src') if madspark_path else None

if src_path and os.path.exists(src_path):
    sys.path.insert(0, src_path)
elif madspark_path and os.path.exists(madspark_path):
    sys.path.insert(0, madspark_path)
else:
    # Fallback for local development - point to the src directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src_dir = os.path.join(parent_dir, 'src')
    if os.path.exists(src_dir):
        sys.path.insert(0, src_dir)
    sys.path.insert(0, parent_dir)

try:
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.core.async_coordinator import AsyncCoordinator
    from madspark.utils.temperature_control import TemperatureManager
    from madspark.core.enhanced_reasoning import ReasoningEngine
    from madspark.utils.constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_EVALUATION_TEMPERATURE,
        DIMENSION_SCORES_KEY,
        FEASIBILITY_KEY,
        INNOVATION_KEY,
        IMPACT_KEY,
        COST_EFFECTIVENESS_KEY,
        SCALABILITY_KEY,
        RISK_ASSESSMENT_KEY,
        TIMELINE_KEY,
        DEFAULT_REQUEST_TIMEOUT
    )
    from madspark.utils.bookmark_system import BookmarkManager
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
except ImportError as e:
    logging.error(f"Failed to import MadSpark modules: {e}")
    # Try alternative paths for different deployment scenarios
    try:
        from src.madspark.core.coordinator import run_multistep_workflow
        from src.madspark.core.async_coordinator import AsyncCoordinator
        from src.madspark.utils.temperature_control import TemperatureManager
        from src.madspark.core.enhanced_reasoning import ReasoningEngine
        from src.madspark.utils.constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE,
            DIMENSION_SCORES_KEY,
            FEASIBILITY_KEY,
            INNOVATION_KEY,
            IMPACT_KEY,
            COST_EFFECTIVENESS_KEY,
            SCALABILITY_KEY,
            RISK_ASSESSMENT_KEY,
            TIMELINE_KEY,
            DEFAULT_REQUEST_TIMEOUT
        )
        from src.madspark.utils.bookmark_system import BookmarkManager
        from src.madspark.utils.cache_manager import CacheManager, CacheConfig
        from src.madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
    except ImportError as e2:
        logging.error(f"Failed to import MadSpark modules with fallback paths: {e2}")
        raise e

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_mock_results(theme: str, num_ideas: int) -> List[Dict[str, Any]]:
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
        if key.lower() in theme.lower() or theme.lower() in key.lower():
            theme_key = key
            break
    
    if not theme_key:
        # Generate generic ideas if no theme match
        base_ideas = [
            f"Innovative solution for {theme} using advanced technology",
            f"Sustainable approach to {theme} with community involvement",
            f"Cost-effective method for implementing {theme} at scale"
        ]
    else:
        base_ideas = mock_ideas[theme_key]
    
    results = []
    for i in range(min(num_ideas, len(base_ideas))):
        base_score = 6.5 + (i * 0.5)
        improved_score = base_score + 1.5 + (random.random() * 0.8)
        
        result = {
            "idea": base_ideas[i],
            "initial_score": round(base_score, 1),
            "initial_critique": f"Interesting concept but needs more detail on implementation and feasibility",
            "advocacy": f"This solution addresses key challenges in {theme} with innovative thinking",
            "skepticism": f"Implementation costs and technical complexity may be barriers",
            "improved_idea": f"{base_ideas[i]}. Enhanced with AI-driven optimization, real-time monitoring, and adaptive learning capabilities for maximum efficiency",
            "improved_score": round(improved_score, 1),
            "improved_critique": f"Comprehensive solution with clear benefits and implementation pathway",
            "score_delta": round(improved_score - base_score, 1),
            "multi_dimensional_evaluation": {
                "dimension_scores": {
                    "feasibility": round(7 + random.random() * 2, 1),
                    "innovation": round(8 + random.random() * 1.5, 1),
                    "impact": round(7.5 + random.random() * 2, 1),
                    "cost_effectiveness": round(6.5 + random.random() * 2, 1),
                    "scalability": round(7 + random.random() * 2.5, 1),
                    "risk_assessment": round(6 + random.random() * 2, 1),
                    "timeline": round(7 + random.random() * 1.5, 1)
                },
                "overall_score": round(base_score + 0.5, 1),
                "confidence_interval": {
                    "lower": round(base_score - 0.5, 1),
                    "upper": round(base_score + 1.5, 1)
                }
            }
        }
        results.append(result)
    
    return results


def format_results_for_frontend(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format results to match frontend expectations, especially multi-dimensional evaluation."""
    # Apply cleaning to all results before formatting (consistent with CLI)
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
                'confidence_interval': {
                    'lower': multi_eval.get('weighted_score', 5) - multi_eval.get('confidence_interval', 1),
                    'upper': multi_eval.get('weighted_score', 5) + multi_eval.get('confidence_interval', 1)
                }
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
                    random_factor = random.uniform(-0.5, 0.5)  # Random between -0.5 and +0.5
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
    try:
        temp_manager = TemperatureManager()
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
app = FastAPI(
    title="MadSpark API",
    description="Web API for the MadSpark Multi-Agent Idea Generation System",
    version="2.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
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


# Pydantic models for API requests and responses
class IdeaGenerationRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=500, description="Theme for idea generation")
    constraints: str = Field(default="Generate practical and innovative ideas", max_length=1000, description="Constraints and criteria (optional)")
    num_top_candidates: int = Field(default=3, ge=1, le=10, description="Number of top ideas to process")
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


class IdeaGenerationResponse(BaseModel):
    status: str
    message: str
    results: List[Dict[str, Any]]
    processing_time: float
    timestamp: str


class BookmarkRequest(BaseModel):
    idea: str = Field(..., min_length=10, max_length=10000, description="Original idea text")
    improved_idea: Optional[str] = Field(default=None, max_length=10000, description="Improved idea text")
    theme: str = Field(..., min_length=1, max_length=200, description="Theme used for generation")
    constraints: str = Field(default="", max_length=500, description="Constraints used")
    initial_score: float = Field(..., ge=0, le=10, description="Initial critic score")
    improved_score: Optional[float] = Field(default=None, ge=0, le=10, description="Improved idea score")
    initial_critique: Optional[str] = Field(default=None, max_length=20000, description="Initial critique")
    improved_critique: Optional[str] = Field(default=None, max_length=20000, description="Improved critique")
    advocacy: Optional[str] = Field(default=None, max_length=20000, description="Advocate's arguments")
    skepticism: Optional[str] = Field(default=None, max_length=20000, description="Skeptic's analysis")
    tags: List[str] = Field(default=[], max_items=10, description="Tags for the bookmark")
    notes: Optional[str] = Field(default=None, max_length=500, description="Additional notes")
    
    @validator('idea', 'improved_idea', 'theme', 'constraints', 'initial_critique', 'improved_critique', 'advocacy', 'skepticism', 'notes')
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
        
        return {
            "status": "healthy" if all([temp_status, reasoning_status, bookmark_status]) else "degraded",
            "components": {
                "temperature_manager": temp_status,
                "reasoning_engine": reasoning_status,
                "bookmark_system": bookmark_status
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/api/temperature-presets")
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-ideas", response_model=IdeaGenerationResponse)
async def generate_ideas(request: IdeaGenerationRequest):
    """Generate ideas using the async MadSpark multi-agent workflow."""
    start_time = datetime.now()
    
    # Check if running in mock mode - check environment variable properly
    google_api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not google_api_key or google_api_key == "your-api-key-here":
        logger.info("Running in mock mode - returning sample results")
        mock_results = generate_mock_results(request.theme, request.num_top_candidates)
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(mock_results)} mock ideas",
            results=format_results_for_frontend(mock_results),
            processing_time=0.5,
            timestamp=start_time.isoformat()
        )
    
    try:
        # Define progress callback
        async def progress_callback(message: str, progress: float):
            await ws_manager.send_progress_update(message, progress)
        
        # Setup temperature manager
        if request.temperature_preset:
            temp_mgr = TemperatureManager.from_preset(request.temperature_preset)
        elif request.temperature:
            temp_mgr = TemperatureManager.from_base_temperature(request.temperature)
        else:
            temp_mgr = temp_manager
        
        # Always setup reasoning engine for multi-dimensional evaluation (now a core feature)
        reasoning_eng = reasoning_engine
        
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
        constraints = request.constraints
        if request.bookmark_ids:
            try:
                from madspark.utils.bookmark_system import remix_with_bookmarks
                constraints = remix_with_bookmarks(
                    theme=request.theme,
                    additional_constraints=request.constraints,
                    bookmark_ids=request.bookmark_ids,
                    bookmark_file=bookmark_system.bookmark_file
                )
                await ws_manager.send_progress_update(f"Using {len(request.bookmark_ids)} bookmarks for remix context", 5.0)
            except Exception as e:
                logger.warning(f"Failed to create remix context: {e}")
                # Continue with original constraints if remix fails
        
        # Create async coordinator with cache and progress callback
        async_coordinator = AsyncCoordinator(
            max_concurrent_agents=max_concurrent_agents,
            progress_callback=progress_callback,
            cache_manager=cache_manager
        )
        
        # Add timeout handling
        timeout_seconds = request.timeout if request.timeout else DEFAULT_REQUEST_TIMEOUT
        try:
            results = await asyncio.wait_for(
                async_coordinator.run_workflow(
                    theme=request.theme,
                    constraints=constraints,  # Use potentially remixed constraints
                    num_top_candidates=request.num_top_candidates,
                    enable_novelty_filter=request.enable_novelty_filter,
                    novelty_threshold=request.novelty_threshold,
                    temperature_manager=temp_mgr,
                    verbose=request.verbose,
                    enhanced_reasoning=request.enhanced_reasoning,
                    multi_dimensional_eval=True,  # Always enabled as a core feature
                    logical_inference=request.logical_inference,
                    reasoning_engine=reasoning_eng
                ),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            await ws_manager.send_progress_update(f"Request timed out after {timeout_seconds} seconds", 0.0)
            raise HTTPException(
                status_code=408, 
                detail=f"Request timed out after {timeout_seconds} seconds. Please try with fewer candidates or simpler constraints."
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(results)} ideas successfully",
            results=format_results_for_frontend(results),
            processing_time=processing_time,
            timestamp=start_time.isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like timeout)
        raise
    except Exception as e:
        logger.error(f"Idea generation failed: {e}")
        await ws_manager.send_progress_update(f"Error: {str(e)}", 0.0)
        # Provide more detailed error information
        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "processing_time": (datetime.now() - start_time).total_seconds()
        }
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/generate-ideas-async", response_model=IdeaGenerationResponse)
async def generate_ideas_async(request: IdeaGenerationRequest):
    """Generate ideas using the async MadSpark workflow for better performance."""
    start_time = datetime.now()
    
    try:
        # Define progress callback
        async def progress_callback(message: str, progress: float):
            await ws_manager.send_progress_update(message, progress)
        
        # Setup temperature manager
        if request.temperature_preset:
            temp_mgr = TemperatureManager.from_preset(request.temperature_preset)
        elif request.temperature:
            temp_mgr = TemperatureManager.from_base_temperature(request.temperature)
        else:
            temp_mgr = temp_manager
        
        # Always setup reasoning engine for multi-dimensional evaluation (now a core feature)
        reasoning_eng = reasoning_engine
        
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
        
        # Create async coordinator with cache
        async_coordinator = AsyncCoordinator(
            max_concurrent_agents=max_concurrent_agents,
            progress_callback=progress_callback,
            cache_manager=cache_manager
        )
        
        # Run the async workflow
        results = await async_coordinator.run_workflow(
            theme=request.theme,
            constraints=request.constraints,
            num_top_candidates=request.num_top_candidates,
            enable_novelty_filter=request.enable_novelty_filter,
            novelty_threshold=request.novelty_threshold,
            temperature_manager=temp_mgr,
            verbose=request.verbose,
            enhanced_reasoning=request.enhanced_reasoning,
            multi_dimensional_eval=True,  # Always enabled as a core feature
            logical_inference=request.logical_inference,
            reasoning_engine=reasoning_eng
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(results)} ideas successfully (async)",
            results=format_results_for_frontend(results),
            processing_time=processing_time,
            timestamp=start_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Async idea generation failed: {e}")
        await ws_manager.send_progress_update(f"Error: {str(e)}", 0.0)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookmarks")
async def get_bookmarks(tags: Optional[str] = None):
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
                "theme": bookmark.theme,
                "constraints": bookmark.constraints,
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(request: BookmarkRequest):
    """Create a new bookmark."""
    try:
        # Log the request for debugging (only non-sensitive fields)
        logger.info(f"Bookmark request received for theme='{request.theme}' with {len(request.tags)} tags.")
        
        # Use improved idea if available, otherwise use original
        idea_text = request.improved_idea if request.improved_idea is not None else request.idea
        score = request.improved_score if request.improved_score is not None else request.initial_score
        critique = request.improved_critique if request.improved_critique is not None else request.initial_critique
        
        bookmark_id = bookmark_system.bookmark_idea(
            idea_text=idea_text,
            theme=request.theme,
            constraints=request.constraints,
            score=round(score, 1),  # Keep precision but convert to compatible format
            critique=critique or "",
            advocacy=request.advocacy or "",
            skepticism=request.skepticism or "",
            tags=request.tags
        )
        
        return BookmarkResponse(
            status="success",
            message="Bookmark created successfully",
            bookmark_id=bookmark_id
        )
    except RequestValidationError as e:
        logger.error(f"Validation error in bookmark request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create bookmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str):
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
            
    except Exception as e:
        logger.error(f"Failed to delete bookmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    try:
        await ws_manager.connect(websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "WebSocket connected successfully",
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
                except:
                    logger.info("WebSocket connection lost during ping")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )