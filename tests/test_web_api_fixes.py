"""Tests for Web API fixes and improvements."""

import pytest
from datetime import datetime
from unittest.mock import patch

# Check for FastAPI availability
try:
    import fastapi  # noqa: F401
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available - web API tests require FastAPI")


class TestWebAPIFixes:
    """Test Web API fixes and improvements."""
    
    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        from web.backend.main import app, initialize_components_for_testing
        
        # Initialize components
        initialize_components_for_testing()
        
        # Set app start time for uptime calculation
        app.state.start_time = datetime.now()
        
        return app
    
    @pytest.fixture
    def client(self, mock_app):
        """Create test client."""
        from fastapi.testclient import TestClient
        return TestClient(mock_app)
    
    @pytest.mark.integration
    def test_health_endpoint_with_uptime(self, client):
        """Test health endpoint includes uptime field."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "uptime" in data  # This was missing before
        assert "timestamp" in data
        
        # Verify uptime is a number
        assert isinstance(data["uptime"], (int, float))
        assert data["uptime"] >= 0
    
    @pytest.mark.integration
    def test_idea_generation_response_structure(self, client):
        """Test idea generation returns correct structure."""
        # Test with new field names (using async endpoint for JSON support)
        response = client.post(
            "/api/generate-ideas-async",
            json={
                "topic": "renewable energy",
                "context": "urban environments"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # API should return results array
        assert "results" in data
        assert isinstance(data["results"], list)
        
        if data["results"]:
            result = data["results"][0]
            assert "idea" in result
            assert "improved_idea" in result
            assert "initial_score" in result
            assert "improved_score" in result
    
    @pytest.mark.integration
    def test_field_alias_compatibility(self, client):
        """Test both old and new field names work."""
        # Test with old field names (theme/constraints) using async endpoint
        response = client.post(
            "/api/generate-ideas-async",
            json={
                "theme": "space exploration",
                "constraints": "low budget"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        
        # Test with new field names (topic/context) using async endpoint
        response = client.post(
            "/api/generate-ideas-async",
            json={
                "topic": "ocean conservation",
                "context": "tropical regions"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    @pytest.mark.integration
    def test_bookmark_field_validation(self, client):
        """Test bookmark creation with proper field validation."""
        bookmark_data = {
            "topic": "test topic",
            "context": "test context",
            "idea": "test idea that is long enough to meet validation",
            "improved_idea": "test improved idea that also meets length requirements",
            "initial_critique": "test critique with sufficient length",
            "advocacy": "test advocacy with sufficient length",
            "skepticism": "test skepticism with sufficient length",
            "initial_score": 7.5,
            "improved_score": 8.5
        }
        
        response = client.post("/api/bookmarks", json=bookmark_data)
        assert response.status_code in [200, 201]
        
        created = response.json()
        assert "bookmark_id" in created or "id" in created
        
        # Verify bookmark was created
        bookmark_id = created.get("bookmark_id") or created.get("id")
        assert bookmark_id is not None
    
    @pytest.mark.integration
    def test_import_path_fixes(self):
        """Test correct import paths are used."""
        # These imports should work
        try:
            from madspark.core.async_coordinator import AsyncCoordinator
            from madspark.core.coordinator import run_multistep_workflow
            assert AsyncCoordinator is not None
            assert run_multistep_workflow is not None
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    @pytest.mark.integration
    def test_error_response_format(self, client):
        """Test error responses have consistent format."""
        # Test 404 error
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        
        # Test 422 validation error
        response = client.post("/api/generate-ideas", json={"invalid": "data"})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.integration
    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        # Note: TestClient doesn't trigger CORS middleware, so we verify the middleware
        # is configured correctly by checking the app's middleware stack
        from web.backend.main import app

        # Check that CORSMiddleware is in the app's middleware stack
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        assert any('CORS' in name for name in middleware_types), \
            "CORSMiddleware not found in app middleware stack"
    
    @patch('web.backend.main.temp_manager')
    @patch('web.backend.main.reasoning_engine')
    @patch('web.backend.main.bookmark_system')
    @pytest.mark.integration
    def test_health_check_degraded_state(self, mock_bookmark, mock_reasoning, mock_temp, client):
        """Test health check shows degraded when components are missing."""
        # Simulate one component being None by patching it to None
        
        with patch('web.backend.main.temp_manager', None):
            response = client.get("/api/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["temperature_manager"] is False
    
    @pytest.mark.integration
    def test_concurrent_request_handling(self, client):
        """Test API handles concurrent requests properly."""
        import concurrent.futures

        def make_request():
            return client.post(
                "/api/generate-ideas-async",
                json={"topic": "test", "context": "concurrent"}
            )

        # Make multiple concurrent requests (reduced to 5 to avoid any limits)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed (200) or at least not fail completely
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 4, f"Only {success_count}/5 requests succeeded"
    
    @pytest.mark.integration
    def test_request_validation_details(self, client):
        """Test detailed validation error messages."""
        # Missing required fields
        response = client.post("/api/generate-ideas", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        
        # Check validation error structure
        if data["detail"]:
            error = data["detail"][0]
            assert "loc" in error  # Location of error
            assert "msg" in error  # Error message
            assert "type" in error  # Error type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])