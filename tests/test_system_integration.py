"""Comprehensive system integration tests for MadSpark."""

import os
import sys
import time
import pytest
import requests
import subprocess
from pathlib import Path
from unittest.mock import patch, Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment for testing
os.environ["MADSPARK_MODE"] = "mock"

# Import after setting environment
from madspark.core.coordinator import run_multistep_workflow

# Base URL for API tests
API_BASE_URL = "http://localhost:8000"


class TestSystemIntegration:
    """Test full system integration across all components."""
    
    @pytest.mark.integration
    def test_cli_to_core_integration(self):
        """Test CLI integration with core workflow."""
        # Run CLI command
        result = subprocess.run(
            ["python", "-m", "madspark.cli.cli", "blockchain", "supply chain"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src", "MADSPARK_MODE": "mock"}
        )
        
        assert result.returncode == 0
        assert "blockchain" in result.stdout.lower()
        # In mock mode, we should get a solution
        assert "solution" in result.stdout.lower() or "score" in result.stdout.lower()
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_end_to_end_workflow(self):
        """Test complete workflow from idea generation to final output."""
        from madspark.core.coordinator import run_multistep_workflow
        
        result = run_multistep_workflow(
            theme="renewable energy",
            constraints="cost-effective for developing countries"
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check result structure
        for item in result:
            assert "idea" in item
            assert "initial_score" in item
            assert "improved_idea" in item
            assert "improved_score" in item
            assert item["improved_score"] >= item["initial_score"]
    
    def test_multi_language_support(self):
        """Test system handling of multiple languages."""
        from madspark.core.coordinator import run_multistep_workflow
        
        # Test with Japanese topic
        result = run_multistep_workflow(
            theme="人工知能",  # AI in Japanese
            constraints="医療応用"  # Medical applications
        )
        
        assert isinstance(result, list)
        # Mock mode should detect and handle Japanese
        if result:
            assert any("モック" in str(item) for item in result)
    
    def test_error_resilience(self):
        """Test system resilience to various error conditions."""
        from madspark.core.coordinator import run_multistep_workflow
        
        # Test with empty inputs - now raises ValidationError
        from madspark.utils.errors import ValidationError
        with pytest.raises(ValidationError):
            run_multistep_workflow("", "")
        
        # Test with very long inputs
        long_text = "test " * 1000
        result = run_multistep_workflow(long_text, long_text)
        assert isinstance(result, list)
        
        # Test with special characters
        result = run_multistep_workflow(
            "test!@#$%^&*()",
            "test<>?:{}"
        )
        assert isinstance(result, list)


class TestDockerIntegration:
    """Test Docker container integration."""
    
    @pytest.mark.skipif(
        not os.path.exists("/.dockerenv") and subprocess.run(
            ["docker", "version"], 
            capture_output=True
        ).returncode != 0,
        reason="Docker not available"
    )
    def test_docker_compose_setup(self):
        """Test Docker Compose configuration."""
        # Check docker-compose.yml exists
        compose_file = Path("web/docker-compose.yml")
        assert compose_file.exists()
        
        # Validate compose file
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True
        )
        # Docker compose should validate successfully
        assert result.returncode == 0
        # Ensure both services are defined in the configuration
        assert "frontend" in result.stdout
        assert "backend" in result.stdout
    
    @pytest.mark.skipif(
        not os.path.exists("/.dockerenv") and subprocess.run(
            ["docker", "version"], 
            capture_output=True
        ).returncode != 0,
        reason="Docker not available"
    )
    def test_container_networking(self):
        """Test container networking configuration."""
        compose_file = Path("web/docker-compose.yml")
        
        # Check network configuration
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True
        )
        
        # Docker compose should validate successfully
        assert result.returncode == 0
        # Verify network configuration exists
        assert "madspark-network" in result.stdout or "networks:" in result.stdout


class TestWebAPIIntegration:
    """Test Web API integration."""
    
    @pytest.fixture(scope="class")
    def api_server(self):
        """Start API server for testing."""
        # Import here to avoid issues if FastAPI not installed
        try:
            import fastapi  # noqa: F401
        except ImportError:
            pytest.skip("FastAPI not available - web API tests require FastAPI")
            
        # Start server in background
        process = subprocess.Popen(
            ["python", "web/backend/main.py"],
            env={**os.environ, "PYTHONPATH": "src", "MADSPARK_MODE": "mock"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(2)
        
        # Check if server is running
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                process.terminate()
                pytest.skip("API server failed to start")
        except requests.exceptions.RequestException:
            process.terminate()
            pytest.skip("API server not responding")
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    def test_health_endpoint(self, api_server):
        """Test API health endpoint."""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "components" in data
        assert "uptime" in data
    
    def test_idea_generation_endpoint(self, api_server):
        """Test idea generation via API."""
        # Initialize components for testing
        requests.post(f"{API_BASE_URL}/test/init")
        
        response = requests.post(
            f"{API_BASE_URL}/api/generate-ideas",
            json={
                "topic": "blockchain technology",
                "context": "supply chain management"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        if data["results"]:
            assert "idea" in data["results"][0]
            assert "improved_idea" in data["results"][0]
        
        # Test with old field names (theme/constraints) for backward compatibility
        response = requests.post(
            f"{API_BASE_URL}/api/generate-ideas",
            json={
                "theme": "artificial intelligence",
                "constraints": "ethical considerations"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
    
    def test_bookmark_functionality(self, api_server):
        """Test bookmark CRUD operations."""
        # Create bookmark
        bookmark_data = {
            "theme": "test theme",
            "constraints": "test constraints",
            "idea": "test idea",
            "improved_idea": "test improved idea",
            "initial_critique": "test critique",
            "advocacy": "test advocacy",
            "skepticism": "test skepticism",
            "initial_score": 7.5,
            "improved_score": 8.5
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/bookmarks",
            json=bookmark_data
        )
        assert response.status_code in [200, 201]
        created = response.json()
        assert "bookmark_id" in created or "id" in created
        bookmark_id = created.get("bookmark_id") or created.get("id")
        
        # List bookmarks
        response = requests.get(f"{API_BASE_URL}/api/bookmarks")
        assert response.status_code == 200
        bookmarks = response.json()
        assert isinstance(bookmarks, list)
        # Handle both response formats
        if isinstance(bookmarks, dict) and "bookmarks" in bookmarks:
            bookmark_list = bookmarks["bookmarks"]
        else:
            bookmark_list = bookmarks
        assert isinstance(bookmark_list, list)
        assert any(b["id"] == bookmark_id for b in bookmark_list)
        
        # Delete bookmark
        response = requests.delete(f"{API_BASE_URL}/api/bookmarks/{bookmark_id}")
        assert response.status_code in [200, 204]
    
    def test_error_handling(self, api_server):
        """Test API error handling."""
        # Test validation error
        response = requests.post(
            f"{API_BASE_URL}/api/generate-ideas",
            json={"invalid": "data"}
        )
        assert response.status_code == 422
        
        # Test not found
        response = requests.get(f"{API_BASE_URL}/api/bookmarks/nonexistent")
        assert response.status_code == 404
        
        # Test method not allowed
        response = requests.patch(f"{API_BASE_URL}/health")
        assert response.status_code == 405


class TestWorkflowErrorHandling:
    """Test workflow error handling and resilience."""
    
    @pytest.mark.skipif(os.getenv("MADSPARK_MODE") == "mock", reason="Mock mode doesn't simulate failures")
    @patch('madspark.agents.idea_generator.genai')
    @pytest.mark.integration
    def test_workflow_with_agent_failures(self, mock_gen_genai):
        """Test workflow resilience to agent failures."""
        
        # Mock idea generation success
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = '''
        {
            "ideas": [
                {
                    "title": "Resilient Test Idea",
                    "description": "Testing error resilience",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ]
        }
        '''
        mock_gen_client.models.generate_content.return_value = mock_gen_response
        mock_gen_genai.Client.return_value = mock_gen_client
        
        # Mock critic failure
        with patch('madspark.agents.critic.genai') as mock_critic_genai:
            mock_critic_client = Mock()
            mock_critic_client.models.generate_content.side_effect = Exception("Critic API error")
            mock_critic_genai.Client.return_value = mock_critic_client
            
            # Workflow should handle critic failure gracefully
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # Should return empty list if critic fails
            assert result is not None
            assert isinstance(result, list)
            # When critical step fails, workflow returns empty list
            assert len(result) == 0
    
    @patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry')
    def test_workflow_with_invalid_parameters(self, mock_generate):
        """Test workflow with invalid parameters."""
        # Mock to return empty ideas
        mock_generate.return_value = ""
        
        # Test with None parameters - now raises ValidationError
        from madspark.utils.errors import ValidationError
        with pytest.raises(ValidationError):
            run_multistep_workflow(None, None)
        
        # Test with very short parameters - valid but returns empty
        result = run_multistep_workflow("a", "b")
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with empty strings - now raises ValidationError
        with pytest.raises(ValidationError):
            run_multistep_workflow("", "")
        
        # Test with invalid timeout - negative timeout should still work (no timeout enforcement in sync mode)
        result = run_multistep_workflow("test", "test", timeout=-1)
        assert isinstance(result, list)
    
    @pytest.mark.skipif(os.getenv("MADSPARK_MODE") == "mock", reason="Mock mode doesn't simulate network issues")
    @pytest.mark.integration
    @pytest.mark.slow
    def test_workflow_network_resilience(self):
        """Test workflow resilience to network issues."""
        
        # Mock network timeout
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            mock_client = Mock()
            mock_client.models.generate_content.side_effect = TimeoutError("Network timeout")
            mock_genai.Client.return_value = mock_client
            
            # Should handle network errors gracefully
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 0  # Empty list on network failure


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""
    
    @pytest.mark.slow
    def test_workflow_execution_time(self):
        """Test workflow completes within reasonable time."""
        from madspark.core.coordinator import run_multistep_workflow
        
        start_time = time.time()
        result = run_multistep_workflow(
            theme="performance test",
            constraints="quick execution"
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Mock mode should be very fast
        if os.getenv("MADSPARK_MODE") == "mock":
            assert execution_time < 5.0  # 5 seconds max for mock mode
        else:
            assert execution_time < 30.0  # 30 seconds max for API mode
            
        assert isinstance(result, list)
    
    @pytest.mark.slow
    def test_workflow_memory_usage(self):
        """Test workflow doesn't have memory leaks."""
        import psutil
        import gc
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run workflow multiple times
        for _ in range(10):
            result = run_multistep_workflow(
                theme="memory test",
                constraints="resource efficiency"
            )
            assert isinstance(result, list)
        
        # Force garbage collection
        gc.collect()
        
        # Check memory didn't grow excessively
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Allow for some growth but not excessive
        assert memory_growth < 100  # Less than 100MB growth


class TestWorkflowDataIntegrity:
    """Test data integrity throughout the workflow."""
    
    @pytest.mark.integration
    def test_workflow_data_consistency(self):
        """Test data remains consistent through workflow steps."""
        from madspark.core.coordinator import run_multistep_workflow
        
        result = run_multistep_workflow(
            theme="data integrity test",
            constraints="maintain consistency"
        )
        
        assert isinstance(result, list)
        
        for item in result:
            # Check all required fields present
            required_fields = [
                "idea", "initial_score", "initial_critique",
                "advocacy", "skepticism", "improved_idea",
                "improved_score", "improved_critique", "score_delta"
            ]
            
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
            
            # Check data types
            assert isinstance(item["idea"], str)
            assert isinstance(item["initial_score"], (int, float))
            assert isinstance(item["improved_score"], (int, float))
            assert isinstance(item["score_delta"], (int, float))
            
            # Check logical consistency
            assert item["score_delta"] == item["improved_score"] - item["initial_score"]
            assert 0 <= item["initial_score"] <= 10
            assert 0 <= item["improved_score"] <= 10


class TestConfigurationValidation:
    """Test configuration and environment handling."""
    
    def test_environment_variables(self):
        """Test environment variable handling."""
        # Test mock mode
        os.environ["MADSPARK_MODE"] = "mock"
        # Import should work without API key
        from madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        assert coordinator is not None
    
    def test_import_compatibility(self):
        """Test import compatibility across environments."""
        # Test basic imports
        try:
            from madspark.agents.idea_generator import generate_ideas
            from madspark.agents.critic import evaluate_ideas
            from madspark.agents.advocate import advocate_idea
            from madspark.agents.skeptic import criticize_idea
            from madspark.core.async_coordinator import AsyncCoordinator
            from madspark.utils.cache_manager import CacheManager
            
            assert all([generate_ideas, evaluate_ideas, advocate_idea, 
                       criticize_idea, AsyncCoordinator, CacheManager])
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_field_alias_compatibility(self):
        """Test theme/topic and constraints/context compatibility."""
        # Test via API endpoints instead since models.py doesn't exist
        # The API should accept both field names - this is handled by the
        # Pydantic model aliases in main.py (IdeaGenerationRequest)
        # We'll test this more thoroughly in the API tests above


if __name__ == "__main__":
    pytest.main([__file__, "-v"])