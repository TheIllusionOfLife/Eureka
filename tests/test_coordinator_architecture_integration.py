"""Integration tests for unified coordinator architecture.

This module tests that both async and batch coordinators work identically
after architecture unification, with no regressions in functionality.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.madspark.core.async_coordinator import AsyncCoordinator

# Note: coordinator_batch.py contains functions, not a BatchCoordinator class
# This test focuses on AsyncCoordinator using the shared BatchOperationsBase


class TestCoordinatorArchitectureIntegration:
    """Integration tests comparing async and batch coordinator behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.async_coordinator = AsyncCoordinator()
    
    def test_both_coordinators_use_same_batch_operations(self):
        """Test that both coordinators inherit from the same base class."""
        # AsyncCoordinator should inherit from BatchOperationsBase
        from src.madspark.core.batch_operations_base import BatchOperationsBase
        
        assert isinstance(self.async_coordinator, BatchOperationsBase)
    
    def test_shared_batch_input_preparation(self):
        """Test that both coordinators prepare batch inputs identically."""
        candidates = [
            {"text": "Solar panels", "critique": "Expensive but effective"},
            {"text": "Wind turbines", "critique": "Clean but intermittent"}
        ]
        
        # AsyncCoordinator should prepare advocacy input correctly
        async_input = self.async_coordinator.prepare_advocacy_input(candidates)
        
        expected = [
            {"idea": "Solar panels", "evaluation": "Expensive but effective"},
            {"idea": "Wind turbines", "evaluation": "Clean but intermittent"}
        ]
        assert async_input == expected
    
    @pytest.mark.asyncio
    async def test_async_coordinator_batch_advocacy_workflow(self):
        """Test complete advocacy workflow in async coordinator using shared operations."""
        candidates = [
            {"text": "Solar energy", "critique": "High initial cost"},
            {"text": "Hydroelectric", "critique": "Environmental impact"}
        ]
        
        # Mock the batch advocacy function results - should be formatted dictionaries
        mock_advocacy_results = [
            {"formatted": "Strong advocacy: Solar energy provides long-term cost savings"},
            {"formatted": "Strong advocacy: Modern hydroelectric minimizes environmental impact"}
        ]
        
        with patch.object(self.async_coordinator, 'run_batch_with_timeout') as mock_batch:
            # Batch functions return tuples (results, token_count)
            mock_batch.return_value = (mock_advocacy_results, 1000)
            
            # This should use the shared batch operations
            result = await self.async_coordinator._process_candidates_with_batch_advocacy(
                candidates, "renewable energy", 0.7
            )
            
            # Verify batch operation was called
            mock_batch.assert_called_once_with(
                'advocate_ideas_batch',
                self.async_coordinator.prepare_advocacy_input(candidates),
                "renewable energy",
                0.7
            )
            
            # Verify candidates were updated with formatted values
            assert result[0]["advocacy"] == mock_advocacy_results[0]["formatted"]
            assert result[1]["advocacy"] == mock_advocacy_results[1]["formatted"]
    
    @pytest.mark.asyncio 
    async def test_async_coordinator_batch_skepticism_workflow(self):
        """Test complete skepticism workflow using shared operations."""
        candidates = [
            {
                "text": "Electric vehicles", 
                "critique": "Battery technology limitations",
                "advocacy": "Strong environmental benefits"
            },
            {
                "text": "Hydrogen fuel cells", 
                "critique": "Infrastructure challenges",
                "advocacy": "Zero emissions potential"
            }
        ]
        
        mock_skepticism_results = [
            {"formatted": "Critical analysis: Battery disposal remains problematic"},
            {"formatted": "Critical analysis: Hydrogen production still carbon-intensive"}
        ]
        
        with patch.object(self.async_coordinator, 'run_batch_with_timeout') as mock_batch:
            mock_batch.return_value = (mock_skepticism_results, 1000)
            
            result = await self.async_coordinator._process_candidates_with_batch_skepticism(
                candidates, "clean transportation", 0.8
            )
            
            # Verify correct input preparation
            expected_input = self.async_coordinator.prepare_skepticism_input(candidates)
            mock_batch.assert_called_once_with(
                'criticize_ideas_batch',
                expected_input,
                "clean transportation", 
                0.8
            )
            
            # Verify results
            assert result[0]["skepticism"] == mock_skepticism_results[0]["formatted"]
            assert result[1]["skepticism"] == mock_skepticism_results[1]["formatted"]
    
    @pytest.mark.asyncio
    async def test_async_coordinator_batch_improvement_workflow(self):
        """Test complete improvement workflow using shared operations."""
        candidates = [
            {
                "text": "Smart grid technology",
                "critique": "Complex implementation",
                "advocacy": "Enables renewable integration", 
                "skepticism": "High cybersecurity risks"
            }
        ]
        
        mock_improvement_results = [
            {"improved_idea": "Improved: Smart grid with enhanced security protocols and phased rollout"}
        ]
        
        with patch.object(self.async_coordinator, 'run_batch_with_timeout') as mock_batch:
            mock_batch.return_value = (mock_improvement_results, 2000)
            
            result = await self.async_coordinator._process_candidates_with_batch_improvement(
                candidates, "energy infrastructure", 0.75
            )
            
            # Verify proper input preparation
            expected_input = self.async_coordinator.prepare_improvement_input(candidates)
            mock_batch.assert_called_once_with(
                'improve_ideas_batch',
                expected_input,
                "energy infrastructure",
                0.75
            )
            
            assert result[0]["improved_idea"] == mock_improvement_results[0]["improved_idea"]
    
    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that error handling is consistent across coordinators."""
        candidates = [{"text": "Test idea", "critique": "Test critique"}]
        
        # Test with non-existent batch function
        with pytest.raises(ValueError, match="Unknown batch function"):
            await self.async_coordinator.run_batch_with_timeout('nonexistent_batch')
        
        # Test with timeout
        def slow_batch_func(*args):
            import time
            time.sleep(2)
            return ["result"]
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'slow_batch': slow_batch_func}):
            with pytest.raises(asyncio.TimeoutError):
                await self.async_coordinator.run_batch_with_timeout(
                    'slow_batch', candidates, timeout=0.1
                )


class TestCoordinatorLogicalInferenceIntegration:
    """Integration tests for logical inference in coordinator workflows."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.coordinator = AsyncCoordinator()
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_batch_logical_inference(self):
        """Test complete coordinator workflow with batch logical inference."""
        # Mock all necessary components
        mock_engine = Mock()
        mock_logical_engine = Mock()
        
        # Mock logical inference results
        from tests.test_batch_logical_inference_async import MockInferenceResult
        mock_logical_results = [
            MockInferenceResult("Chain 1", "Conclusion 1", 0.85, "Improvements 1"),
            MockInferenceResult("Chain 2", "Conclusion 2", 0.90, "Improvements 2")
        ]
        mock_logical_engine.analyze_batch.return_value = mock_logical_results
        mock_engine.logical_inference_engine = mock_logical_engine
        
        self.coordinator.reasoning_engine = mock_engine
        self.coordinator._send_progress = AsyncMock()
        
        # Mock candidates that would come from earlier workflow steps
        candidates = [
            {
                "text": "Solar panel installation", 
                "critique": "High upfront cost",
                "score": 8.5,
                "advocacy": "Long-term savings",
                "skepticism": "Weather dependency"
            },
            {
                "text": "Wind turbine deployment",
                "critique": "Noise concerns", 
                "score": 8.0,
                "advocacy": "Clean energy source",
                "skepticism": "Visual impact"
            }
        ]
        
        # Test the logical inference integration
        ideas = [c["text"] for c in candidates]
        batch_results = await self.coordinator._run_batch_logical_inference(
            ideas, "renewable energy", "cost-effective", "FULL"
        )
        
        # Apply the results to candidates (simulate main workflow)
        CONFIDENCE_THRESHOLD = 0.7
        for i, (candidate, result) in enumerate(zip(candidates, batch_results)):
            if result and hasattr(result, 'confidence'):
                if result.confidence >= CONFIDENCE_THRESHOLD:
                    candidate["logical_inference"] = result.__dict__()
        
        # Verify single batch call
        mock_logical_engine.analyze_batch.assert_called_once_with(
            ideas, "renewable energy", "cost-effective", "FULL"
        )
        
        # Verify candidates have logical inference data
        assert "logical_inference" in candidates[0]
        assert "logical_inference" in candidates[1]
        assert candidates[0]["logical_inference"]["confidence"] == 0.85
        assert candidates[1]["logical_inference"]["confidence"] == 0.90
    
    @pytest.mark.asyncio
    async def test_api_call_efficiency_end_to_end(self):
        """Test that API calls are minimized in complete workflow."""
        api_call_tracker = {"count": 0}
        
        def track_api_calls(*args, **kwargs):
            api_call_tracker["count"] += 1
            from tests.test_batch_logical_inference_async import MockInferenceResult
            return [MockInferenceResult(f"Chain {i}", f"Conc {i}", 0.8, f"Imp {i}") 
                   for i in range(len(args[0]))]
        
        # Set up coordinator with call tracking
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = track_api_calls
        mock_engine.logical_inference_engine = mock_logical_engine
        
        self.coordinator.reasoning_engine = mock_engine
        
        # Test with multiple batches of ideas
        batch1_ideas = ["Idea 1", "Idea 2", "Idea 3"]
        batch2_ideas = ["Idea 4", "Idea 5"]
        
        # Run multiple batch operations
        await self.coordinator._run_batch_logical_inference(
            batch1_ideas, "topic1", "context1"
        )
        await self.coordinator._run_batch_logical_inference(
            batch2_ideas, "topic2", "context2"
        )
        
        # Should be 2 API calls total (1 per batch), not 5 individual calls
        assert api_call_tracker["count"] == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_batch_operations_with_logical_inference(self):
        """Test that batch operations can run concurrently with logical inference."""
        import time
        
        # Mock functions with realistic delays
        def mock_advocacy_batch(*args):
            time.sleep(0.1)
            return ["Advocacy result 1", "Advocacy result 2"]
        
        def mock_logical_batch(ideas, *args):
            time.sleep(0.1)
            from tests.test_batch_logical_inference_async import MockInferenceResult
            return [MockInferenceResult(f"Chain {i}", f"Conc {i}", 0.8, f"Imp {i}") 
                   for i in range(len(ideas))]
        
        # Set up coordinator with mocked functions
        mock_engine = Mock()
        mock_logical_engine = Mock()  
        mock_logical_engine.analyze_batch.side_effect = mock_logical_batch
        mock_engine.logical_inference_engine = mock_logical_engine
        self.coordinator.reasoning_engine = mock_engine
        
        candidates = [
            {"text": "Idea 1", "critique": "Critique 1"},
            {"text": "Idea 2", "critique": "Critique 2"}
        ]
        ideas = [c["text"] for c in candidates]
        
        with patch.object(self.coordinator, 'run_batch_with_timeout') as mock_advocacy:
            mock_advocacy.return_value = ["Advocacy 1", "Advocacy 2"]
            
            start_time = time.time()
            
            # Run operations concurrently
            advocacy_task = self.coordinator._process_candidates_with_batch_advocacy(
                candidates, "theme", 0.7
            )
            logical_task = self.coordinator._run_batch_logical_inference(
                ideas, "topic", "context"
            )
            
            advocacy_result, logical_result = await asyncio.gather(
                advocacy_task, logical_task
            )
            
            elapsed = time.time() - start_time
            
            # Should complete in ~0.1s (concurrent) not ~0.2s (sequential)
            # Allow more time in CI environments  
            assert elapsed < 0.25, f"Operations should run concurrently: {elapsed}s"
            assert len(logical_result) == 2
            assert len(advocacy_result) == 2


@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests with real API endpoints (when available)."""
    
    @pytest.mark.asyncio
    async def test_batch_logical_inference_with_real_api(self):
        """Test batch logical inference with real Google GenAI API."""
        try:
            import google.genai  # noqa: F401
        except ImportError:
            pytest.skip("Google GenAI not available")
        
        import os
        
        # Skip if no API key available
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("No GOOGLE_API_KEY available for real API testing")
        
        from src.madspark.core.enhanced_reasoning import ReasoningEngine
        from src.madspark.utils.logical_inference_engine import InferenceType
        
        # Create coordinator with real reasoning engine
        from google import genai
        
        genai_client = genai.Client()
        coordinator = AsyncCoordinator()
        reasoning_engine = ReasoningEngine(genai_client=genai_client)
        coordinator.reasoning_engine = reasoning_engine
        
        # Test with real ideas
        ideas = [
            "Solar panel installation on residential rooftops",
            "Community wind farm development"
        ]
        
        # Run batch logical inference
        results = await coordinator._run_batch_logical_inference(
            ideas, "renewable energy", "cost-effective solutions", InferenceType.FULL
        )
        
        # Verify results
        assert len(results) == 2
        
        for result in results:
            assert hasattr(result, 'inference_chain')
            assert hasattr(result, 'conclusion')
            assert hasattr(result, 'confidence')
            assert 0.0 <= result.confidence <= 1.0
            
            # Verify content quality
            assert len(result.inference_chain) > 10  # Non-trivial content
            assert len(result.conclusion) > 10       # Non-trivial content
    
    @pytest.mark.asyncio 
    async def test_api_call_count_with_real_api(self):
        """Verify that batch processing actually reduces API calls with real API."""
        try:
            import google.genai  # noqa: F401
        except ImportError:
            pytest.skip("Google GenAI not available")
        
        import os
        
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("No GOOGLE_API_KEY available for real API testing")
        
        from src.madspark.core.enhanced_reasoning import ReasoningEngine
        
        from google import genai
        
        genai_client = genai.Client()
        coordinator = AsyncCoordinator()
        reasoning_engine = ReasoningEngine(genai_client=genai_client)
        coordinator.reasoning_engine = reasoning_engine
        
        # Track API calls by monitoring the genai client
        original_generate_content = None
        call_count = {"value": 0}
        
        def count_api_calls(*args, **kwargs):
            call_count["value"] += 1
            return original_generate_content(*args, **kwargs)
        
        # Patch the API client to count calls
        import google.genai as genai
        if hasattr(genai, 'Client'):
            client = genai.Client()
            if hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
                original_generate_content = client.models.generate_content
                client.models.generate_content = count_api_calls
        
        ideas = ["Solar energy", "Wind power", "Hydroelectric", "Geothermal", "Biomass"]
        
        # Run batch logical inference
        results = await coordinator._run_batch_logical_inference(
            ideas, "renewable energy", "sustainable solutions"
        )
        
        # Should be 1 API call for 5 ideas
        assert call_count["value"] == 1, f"Expected 1 API call, got {call_count['value']}"
        assert len(results) == 5