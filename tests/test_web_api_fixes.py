"""Test file for Web API fixes - TDD approach"""
import pytest
import time
from datetime import datetime
import sys
import os

# Add web backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web', 'backend'))


def test_health_endpoint_has_uptime():
    """Test that health endpoint includes uptime field."""
    from main import app, initialize_components_for_testing
    from fastapi.testclient import TestClient
    
    # Initialize components
    initialize_components_for_testing()
    
    client = TestClient(app)
    
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "uptime" in data  # This should be present
    assert isinstance(data["uptime"], (int, float))
    assert data["uptime"] >= 0


def test_idea_generation_response_structure():
    """Test that idea generation returns expected structure."""
    from main import app, initialize_components_for_testing
    from fastapi.testclient import TestClient
    
    # Force mock mode
    os.environ["GOOGLE_API_KEY"] = "mock-key"
    
    # Initialize components
    initialize_components_for_testing()
    
    client = TestClient(app)
    
    response = client.post("/api/generate-ideas", json={
        "topic": "test topic",
        "context": "test context"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    # Current API returns this structure
    assert "status" in data
    assert "results" in data
    assert isinstance(data["results"], list)
    
    # Each result should have these fields
    if data["results"]:
        result = data["results"][0]
        assert "idea" in result
        assert "improved_idea" in result
        assert "initial_score" in result
        assert "improved_score" in result


def test_bookmark_creation_response():
    """Test bookmark creation returns correct response structure."""
    from main import app, initialize_components_for_testing
    from fastapi.testclient import TestClient
    
    # Initialize components
    initialize_components_for_testing()
    
    client = TestClient(app)
    
    bookmark_data = {
        "idea": "Test idea for bookmarking",
        "improved_idea": "Improved test idea",
        "theme": "test theme",  # Using 'theme' alias
        "constraints": "test constraints",  # Using 'constraints' alias
        "initial_score": 7.5,  # Required field
        "improved_score": 8.5,
        "initial_critique": "Initial critique",  # Correct field name
        "improved_critique": "Improved critique",
        "advocacy": "test advocacy",
        "skepticism": "test skepticism"
    }
    
    response = client.post("/api/bookmarks", json=bookmark_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert "bookmark_id" in data  # API returns bookmark_id, not id


def test_bookmark_field_aliases():
    """Test that bookmark creation accepts both field names."""
    from main import app, initialize_components_for_testing
    from fastapi.testclient import TestClient
    
    # Initialize components
    initialize_components_for_testing()
    
    client = TestClient(app)
    
    # Test with 'topic' and 'context' (new names)
    bookmark_data_new = {
        "idea": "Test idea that is long enough",  # Must be at least 10 characters
        "topic": "test topic",  # New field name
        "context": "test context",  # New field name
        "initial_score": 7.0
    }
    
    response = client.post("/api/bookmarks", json=bookmark_data_new)
    assert response.status_code == 200
    
    # Test with 'theme' and 'constraints' (old names)
    bookmark_data_old = {
        "idea": "Test idea 2 that is also long enough",  # Must be at least 10 characters
        "theme": "test theme",  # Old field name
        "constraints": "test constraints",  # Old field name
        "initial_score": 7.5
    }
    
    response = client.post("/api/bookmarks", json=bookmark_data_old)
    assert response.status_code == 200


def test_api_import_compatibility():
    """Test that API can import required modules."""
    # These should not raise ImportError
    from main import AsyncCoordinator
    from main import TemperatureManager
    from main import ReasoningEngine
    from main import BookmarkManager
    
    assert AsyncCoordinator is not None
    assert TemperatureManager is not None
    assert ReasoningEngine is not None
    assert BookmarkManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])