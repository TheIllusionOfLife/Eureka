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
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import MadSpark modules using relative imports
try:
    # Try relative imports first (when run as package)
    from ...coordinator import run_multistep_workflow, CandidateData
    from ...temperature_control import TemperatureManager
    from ...enhanced_reasoning import ReasoningEngine
    from ...constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_EVALUATION_TEMPERATURE,
        TEMPERATURE_PRESETS
    )
    from ...bookmark_system import BookmarkSystem
except ImportError:
    # Fallback for development when run directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from coordinator import run_multistep_workflow, CandidateData
        from temperature_control import TemperatureManager
        from enhanced_reasoning import ReasoningEngine
        from constants import (
            DEFAULT_IDEA_TEMPERATURE,
            DEFAULT_EVALUATION_TEMPERATURE,
            TEMPERATURE_PRESETS
        )
        from bookmark_system import BookmarkSystem
    except ImportError as e:
        logging.error(f"Failed to import MadSpark modules: {e}")
        raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for MadSpark components
temp_manager: Optional[TemperatureManager] = None
reasoning_engine: Optional[ReasoningEngine] = None
bookmark_system: Optional[BookmarkSystem] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup MadSpark components."""
    global temp_manager, reasoning_engine, bookmark_system
    
    # Startup
    logger.info("Initializing MadSpark backend services...")
    try:
        temp_manager = TemperatureManager()
        reasoning_engine = ReasoningEngine()
        bookmark_system = BookmarkSystem()
        logger.info("✅ MadSpark backend initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize MadSpark backend: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down MadSpark backend services...")


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


# Pydantic models for API requests and responses
class IdeaGenerationRequest(BaseModel):
    theme: str = Field(..., min_length=1, max_length=500, description="Theme for idea generation")
    constraints: str = Field(..., min_length=1, max_length=1000, description="Constraints and criteria")
    num_top_candidates: int = Field(default=2, ge=1, le=10, description="Number of top ideas to process")
    enable_novelty_filter: bool = Field(default=True, description="Enable novelty filtering")
    novelty_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Similarity threshold for novelty filter")
    temperature_preset: Optional[str] = Field(default=None, description="Temperature preset (conservative, balanced, creative, wild)")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Custom temperature value")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    enhanced_reasoning: bool = Field(default=False, description="Enable enhanced reasoning capabilities")
    multi_dimensional_eval: bool = Field(default=False, description="Use multi-dimensional evaluation")
    logical_inference: bool = Field(default=False, description="Enable logical inference chains")


class IdeaGenerationResponse(BaseModel):
    status: str
    message: str
    results: List[Dict[str, Any]]
    processing_time: float
    timestamp: str


class BookmarkRequest(BaseModel):
    idea: str = Field(..., min_length=1, description="Idea text to bookmark")
    tags: List[str] = Field(default=[], description="Tags for the bookmark")
    notes: Optional[str] = Field(default=None, description="Additional notes")


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
        return {
            "status": "success",
            "presets": TEMPERATURE_PRESETS,
            "default": "balanced"
        }
    except Exception as e:
        logger.error(f"Failed to get temperature presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-ideas", response_model=IdeaGenerationResponse)
async def generate_ideas(request: IdeaGenerationRequest):
    """Generate ideas using the MadSpark multi-agent workflow."""
    start_time = datetime.now()
    
    try:
        # Send initial progress update
        await ws_manager.send_progress_update("Initializing idea generation...", 0.1)
        
        # Setup temperature manager
        if request.temperature_preset:
            temp_mgr = TemperatureManager(preset=request.temperature_preset)
        elif request.temperature:
            temp_mgr = TemperatureManager()
            temp_mgr.set_all_temperatures(request.temperature)
        else:
            temp_mgr = temp_manager
        
        await ws_manager.send_progress_update("Temperature settings configured", 0.2)
        
        # Setup reasoning engine if needed
        reasoning_eng = reasoning_engine if (
            request.enhanced_reasoning or 
            request.multi_dimensional_eval or 
            request.logical_inference
        ) else None
        
        if reasoning_eng:
            await ws_manager.send_progress_update("Enhanced reasoning engine ready", 0.3)
        
        await ws_manager.send_progress_update("Starting multi-agent workflow...", 0.4)
        
        # Run the workflow
        results = run_multistep_workflow(
            theme=request.theme,
            constraints=request.constraints,
            num_top_candidates=request.num_top_candidates,
            enable_novelty_filter=request.enable_novelty_filter,
            novelty_threshold=request.novelty_threshold,
            temperature_manager=temp_mgr,
            verbose=request.verbose,
            enhanced_reasoning=request.enhanced_reasoning,
            multi_dimensional_eval=request.multi_dimensional_eval,
            logical_inference=request.logical_inference,
            reasoning_engine=reasoning_eng
        )
        
        await ws_manager.send_progress_update("Workflow completed successfully!", 1.0)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return IdeaGenerationResponse(
            status="success",
            message=f"Generated {len(results)} ideas successfully",
            results=[dict(result) for result in results],
            processing_time=processing_time,
            timestamp=start_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Idea generation failed: {e}")
        await ws_manager.send_progress_update(f"Error: {str(e)}", 0.0)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookmarks")
async def get_bookmarks(tags: Optional[str] = None):
    """Get all bookmarks, optionally filtered by tags."""
    try:
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            bookmarks = bookmark_system.search_by_tags(tag_list)
        else:
            bookmarks = bookmark_system.list_bookmarks()
        
        return {
            "status": "success",
            "bookmarks": bookmarks,
            "count": len(bookmarks)
        }
    except Exception as e:
        logger.error(f"Failed to get bookmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(request: BookmarkRequest):
    """Create a new bookmark."""
    try:
        bookmark_id = bookmark_system.add_bookmark(
            idea=request.idea,
            tags=request.tags,
            notes=request.notes
        )
        
        return BookmarkResponse(
            status="success",
            message="Bookmark created successfully",
            bookmark_id=bookmark_id
        )
    except Exception as e:
        logger.error(f"Failed to create bookmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for connection testing
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
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