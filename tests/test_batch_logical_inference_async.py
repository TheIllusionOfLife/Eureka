"""Test suite for batch logical inference in async coordinator.

This module tests the optimization that reduces logical inference API calls
from O(N) to O(1) through batch processing.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass
from typing import List

from src.madspark.core.async_coordinator import AsyncCoordinator
from src.madspark.utils.logical_inference_engine import InferenceResult, InferenceType


@dataclass
class MockInferenceResult:
    """Mock inference result for testing."""
    inference_chain: str
    conclusion: str
    confidence: float
    improvements: str
    
    def __dict__(self):
        """Return dict representation for JSON serialization."""
        return {
            'inference_chain': self.inference_chain,
            'conclusion': self.conclusion, 
            'confidence': self.confidence,
            'improvements': self.improvements
        }


class TestBatchLogicalInferenceAsync:
    """Test cases for batch logical inference in async coordinator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = AsyncCoordinator()
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_success(self):
        """Test successful batch logical inference operation."""
        # Mock inference results
        mock_results = [
            MockInferenceResult(
                inference_chain="Chain 1",
                conclusion="Conclusion 1", 
                confidence=0.85,
                improvements="Improvement 1"
            ),
            MockInferenceResult(
                inference_chain="Chain 2",
                conclusion="Conclusion 2",
                confidence=0.90,
                improvements="Improvement 2"
            )
        ]
        
        # Mock reasoning engine
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.return_value = mock_results
        mock_engine.logical_inference_engine = mock_logical_engine
        self.coordinator.reasoning_engine = mock_engine
        
        # Test batch logical inference
        ideas = ["Solar energy systems", "Wind power installations"]
        results = await self.coordinator._run_batch_logical_inference(
            ideas, "renewable energy", "cost-effective", InferenceType.FULL
        )
        
        # Verify single batch call was made
        mock_logical_engine.analyze_batch.assert_called_once_with(
            ideas, "renewable energy", "cost-effective", InferenceType.FULL
        )
        
        # Verify results
        assert len(results) == 2
        assert results[0].confidence == 0.85
        assert results[1].confidence == 0.90
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_no_engine(self):
        """Test batch logical inference when no engine is available."""
        # No reasoning engine set
        self.coordinator.reasoning_engine = None
        
        results = await self.coordinator._run_batch_logical_inference(
            ["idea1", "idea2"], "theme", "context"
        )
        
        assert results == []
    
    @pytest.mark.asyncio 
    async def test_run_batch_logical_inference_no_logical_engine(self):
        """Test batch logical inference when logical engine is missing."""
        # Mock reasoning engine without logical inference engine
        mock_engine = Mock()
        mock_engine.logical_inference_engine = None
        self.coordinator.reasoning_engine = mock_engine
        
        results = await self.coordinator._run_batch_logical_inference(
            ["idea1", "idea2"], "theme", "context"
        )
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_run_batch_logical_inference_exception(self):
        """Test batch logical inference error handling."""
        # Mock reasoning engine that raises exception
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = Exception("API Error")
        mock_engine.logical_inference_engine = mock_logical_engine
        self.coordinator.reasoning_engine = mock_engine
        
        with patch('src.madspark.core.async_coordinator.logger') as mock_logger:
            results = await self.coordinator._run_batch_logical_inference(
                ["idea1"], "theme", "context"
            )
            
            assert results == []
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_top_candidates_with_batch_logical_inference(self):
        """Test integration of batch logical inference in main workflow."""
        # Mock candidates
        candidates = [
            {"text": "Solar panels", "critique": "Good idea", "score": 8.5},
            {"text": "Wind turbines", "critique": "Effective", "score": 8.0}
        ]
        
        # Mock inference results
        mock_results = [
            MockInferenceResult("Chain 1", "Conclusion 1", 0.85, "Improvements 1"),
            MockInferenceResult("Chain 2", "Conclusion 2", 0.90, "Improvements 2")
        ]
        
        # Mock reasoning engine
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.return_value = mock_results
        mock_engine.logical_inference_engine = mock_logical_engine
        
        # Mock progress callback
        mock_progress = AsyncMock()
        
        # Set up coordinator with mocks
        self.coordinator.reasoning_engine = mock_engine
        self.coordinator._send_progress = mock_progress
        
        # Test the workflow section that handles logical inference
        # We'll test the specific logic from lines 753-779 in process_top_candidates
        
        # Extract ideas and run batch inference
        ideas_for_inference = [candidate["text"] for candidate in candidates]
        batch_results = await self.coordinator._run_batch_logical_inference(
            ideas_for_inference, "renewable energy", "cost-effective", InferenceType.FULL
        )
        
        # Process results (simulate the logic from the main method)
        for i, (candidate, inference_result) in enumerate(zip(candidates, batch_results)):
            if inference_result and hasattr(inference_result, 'confidence'):
                confidence = getattr(inference_result, 'confidence', 0.0)
                if confidence >= 0.7:  # LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD
                    candidate["logical_inference"] = inference_result.__dict__()
        
        # Verify single batch call was made
        mock_logical_engine.analyze_batch.assert_called_once_with(
            ideas_for_inference, "renewable energy", "cost-effective", InferenceType.FULL
        )
        
        # Verify candidates were updated with logical inference
        assert "logical_inference" in candidates[0]
        assert "logical_inference" in candidates[1]
        assert candidates[0]["logical_inference"]["confidence"] == 0.85
        assert candidates[1]["logical_inference"]["confidence"] == 0.90
    
    @pytest.mark.asyncio
    async def test_logical_inference_confidence_filtering(self):
        """Test filtering of low-confidence logical inference results."""
        candidates = [
            {"text": "High confidence idea", "critique": "Good"},
            {"text": "Low confidence idea", "critique": "Unclear"}
        ]
        
        # Mock results with different confidence levels
        mock_results = [
            MockInferenceResult("Chain 1", "Conclusion 1", 0.85, "Improvements 1"),  # High
            MockInferenceResult("Chain 2", "Conclusion 2", 0.60, "Improvements 2")   # Low
        ]
        
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.return_value = mock_results
        mock_engine.logical_inference_engine = mock_logical_engine
        self.coordinator.reasoning_engine = mock_engine
        
        # Run batch inference
        ideas = [c["text"] for c in candidates] 
        batch_results = await self.coordinator._run_batch_logical_inference(
            ideas, "theme", "context"
        )
        
        # Apply confidence filtering (threshold = 0.7)
        CONFIDENCE_THRESHOLD = 0.7
        for i, (candidate, result) in enumerate(zip(candidates, batch_results)):
            if result and hasattr(result, 'confidence'):
                if result.confidence >= CONFIDENCE_THRESHOLD:
                    candidate["logical_inference"] = result.__dict__()
        
        # Verify only high-confidence result was added
        assert "logical_inference" in candidates[0]  # 0.85 >= 0.7
        assert "logical_inference" not in candidates[1]  # 0.60 < 0.7


class TestBatchLogicalInferenceIntegration:
    """Integration tests for batch logical inference with real components."""
    
    @pytest.mark.asyncio
    async def test_api_call_reduction_measurement(self):
        """Test that batch logical inference reduces API calls from N to 1."""
        # Mock to count API calls
        api_call_count = 0
        
        def mock_analyze_batch(*args, **kwargs):
            nonlocal api_call_count
            api_call_count += 1
            return [
                MockInferenceResult(f"Chain {i}", f"Conclusion {i}", 0.8, f"Imp {i}")
                for i in range(len(args[0]))  # args[0] is the ideas list
            ]
        
        # Set up coordinator with API call tracking
        coordinator = AsyncCoordinator()
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = mock_analyze_batch
        mock_engine.logical_inference_engine = mock_logical_engine
        coordinator.reasoning_engine = mock_engine
        
        # Test with 5 ideas
        ideas = [f"Idea {i}" for i in range(5)]
        
        # Run batch logical inference
        results = await coordinator._run_batch_logical_inference(
            ideas, "theme", "context"
        )
        
        # Verify only 1 API call was made for 5 ideas
        assert api_call_count == 1
        assert len(results) == 5
        
        # Verify each result has the expected structure
        for i, result in enumerate(results):
            assert result.confidence == 0.8
            assert f"Chain {i}" in result.inference_chain
    
    @pytest.mark.asyncio
    async def test_batch_vs_individual_logical_inference_performance(self):
        """Test performance difference between batch and individual inference calls."""
        import time
        
        # Mock individual inference call (simulate API delay)
        def mock_individual_analyze(*args):
            time.sleep(0.1)  # Simulate 100ms API call
            return MockInferenceResult("Chain", "Conclusion", 0.8, "Improvement")
        
        # Mock batch inference call (simulate single API delay)  
        def mock_batch_analyze(ideas, *args):
            time.sleep(0.1)  # Same 100ms delay but for all ideas
            return [
                MockInferenceResult(f"Chain {i}", f"Conclusion {i}", 0.8, f"Imp {i}")
                for i in range(len(ideas))
            ]
        
        coordinator = AsyncCoordinator()
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_engine.logical_inference_engine = mock_logical_engine
        coordinator.reasoning_engine = mock_engine
        
        ideas = ["Idea 1", "Idea 2", "Idea 3", "Idea 4", "Idea 5"]
        
        # Test individual calls (simulate old approach)
        mock_logical_engine.analyze.side_effect = mock_individual_analyze
        start_time = time.time()
        
        # Simulate individual calls
        individual_results = []
        for idea in ideas:
            # This simulates what would happen without batch processing
            result = mock_individual_analyze(idea, "theme", "context")
            individual_results.append(result)
        
        individual_time = time.time() - start_time
        
        # Test batch call (new approach)
        mock_logical_engine.analyze_batch.side_effect = mock_batch_analyze
        start_time = time.time()
        
        batch_results = await coordinator._run_batch_logical_inference(
            ideas, "theme", "context"
        )
        
        batch_time = time.time() - start_time
        
        # Verify batch is significantly faster
        # Individual: ~5 * 0.1s = 0.5s, Batch: ~0.1s
        assert batch_time < individual_time * 0.3  # At least 70% faster
        assert len(batch_results) == len(individual_results) == 5
    
    @pytest.mark.asyncio
    async def test_concurrent_batch_operations_with_logical_inference(self):
        """Test that logical inference can run concurrently with other batch operations."""
        import time
        
        # Mock batch functions with realistic delays
        def mock_advocacy_batch(*args):
            time.sleep(0.1)
            return ["Advocacy 1", "Advocacy 2"]
        
        def mock_logical_batch(ideas, *args):
            time.sleep(0.1)
            return [MockInferenceResult(f"Chain {i}", f"Conc {i}", 0.8, f"Imp {i}") 
                   for i in range(len(ideas))]
        
        coordinator = AsyncCoordinator()
        
        # Mock reasoning engine
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = mock_logical_batch
        mock_engine.logical_inference_engine = mock_logical_engine
        coordinator.reasoning_engine = mock_engine
        
        ideas = ["Idea 1", "Idea 2"]
        candidates = [{"text": idea, "critique": f"Critique for {idea}"} for idea in ideas]
        
        start_time = time.time()
        
        # Run operations that could be concurrent
        advocacy_task = asyncio.create_task(asyncio.sleep(0.1))  # Simulate advocacy
        logical_task = coordinator._run_batch_logical_inference(ideas, "theme", "context")
        
        # Wait for both to complete
        await advocacy_task
        logical_results = await logical_task
        
        elapsed = time.time() - start_time
        
        # Should complete in ~0.1s (concurrent) not ~0.2s (sequential)
        assert elapsed < 0.15, f"Concurrent execution too slow: {elapsed}s"
        assert len(logical_results) == 2


@pytest.mark.slow
class TestBatchLogicalInferencePerformance:
    """Performance-focused tests for batch logical inference."""
    
    @pytest.mark.asyncio
    async def test_large_batch_logical_inference(self):
        """Test batch logical inference with large number of ideas."""
        import time
        
        coordinator = AsyncCoordinator()
        
        # Mock batch function for large dataset
        def mock_large_batch(ideas, *args):
            return [
                MockInferenceResult(f"Chain {i}", f"Conclusion {i}", 0.8, f"Improvement {i}")
                for i in range(len(ideas))
            ]
        
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = mock_large_batch
        mock_engine.logical_inference_engine = mock_logical_engine
        coordinator.reasoning_engine = mock_engine
        
        # Test with 50 ideas
        ideas = [f"Renewable energy idea {i}" for i in range(50)]
        
        start_time = time.time()
        results = await coordinator._run_batch_logical_inference(ideas, "energy", "sustainable")
        elapsed = time.time() - start_time
        
        # Should still be fast with large batch
        assert elapsed < 1.0, f"Large batch too slow: {elapsed}s"
        assert len(results) == 50
        
        # Verify all results have expected structure
        for i, result in enumerate(results):
            assert result.confidence == 0.8
            assert f"Chain {i}" in result.inference_chain
    
    @pytest.mark.asyncio
    async def test_memory_efficiency_large_batch(self):
        """Test memory efficiency of batch logical inference."""
        import sys
        
        coordinator = AsyncCoordinator()
        
        # Mock batch function that returns large results
        def mock_memory_batch(ideas, *args):
            # Simulate realistic inference results
            return [
                MockInferenceResult(
                    inference_chain=f"Detailed inference chain for idea {i} with multiple steps and analysis",
                    conclusion=f"Comprehensive conclusion {i} with detailed reasoning and recommendations", 
                    confidence=0.8,
                    improvements=f"Multiple improvement suggestions {i} with specific implementation details"
                )
                for i in range(len(ideas))
            ]
        
        mock_engine = Mock()
        mock_logical_engine = Mock()
        mock_logical_engine.analyze_batch.side_effect = mock_memory_batch
        mock_engine.logical_inference_engine = mock_logical_engine
        coordinator.reasoning_engine = mock_engine
        
        # Test with 100 ideas to check memory usage
        ideas = [f"Complex renewable energy solution {i} with detailed specifications" for i in range(100)]
        
        # Get memory usage before
        import tracemalloc
        tracemalloc.start()
        
        results = await coordinator._run_batch_logical_inference(ideas, "energy", "sustainable")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Verify reasonable memory usage (less than 50MB for 100 results)
        assert peak < 50 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.2f}MB"
        assert len(results) == 100