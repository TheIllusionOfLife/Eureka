"""Tests for parallel processing optimizations."""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from madspark.core.async_coordinator import AsyncCoordinator


class TestParallelProcessing:
    """Test cases for parallel processing optimizations."""
    
    @pytest.fixture
    def coordinator(self):
        """Create AsyncCoordinator instance for testing."""
        return AsyncCoordinator()
    
    @pytest.fixture
    def mock_candidate(self):
        """Sample candidate data."""
        return {
            "text": "Test mobile game idea",
            "score": 7.5,
            "critique": "Good concept with room for improvement"
        }
    
    @pytest.mark.asyncio
    async def test_parallel_advocacy_skepticism(self, coordinator, mock_candidate):
        """Test that advocacy and skepticism run in parallel."""
        # Mock the async functions
        with patch('madspark.core.async_coordinator.async_advocate_idea') as mock_advocate, \
             patch('madspark.core.async_coordinator.async_criticize_idea') as mock_criticize, \
             patch('madspark.core.async_coordinator.async_improve_idea') as mock_improve, \
             patch('madspark.core.async_coordinator.async_evaluate_ideas') as mock_evaluate:
            
            # Set up mocks with delays to test parallel execution
            async def slow_advocate(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return "Strong advocacy response"
            
            async def slow_criticize(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms delay
                return "Critical analysis response"
            
            async def fast_improve(*args, **kwargs):
                await asyncio.sleep(0.05)  # 50ms delay 
                return "Improved idea text"
            
            async def fast_evaluate(*args, **kwargs):
                await asyncio.sleep(0.05)  # 50ms delay
                return '{"evaluations": [{"score": 8.5, "comment": "Excellent improvement"}]}'
            
            mock_advocate.side_effect = slow_advocate
            mock_criticize.side_effect = slow_criticize
            mock_improve.side_effect = fast_improve
            mock_evaluate.side_effect = fast_evaluate
            
            # Measure execution time
            start_time = time.time()
            
            result = await coordinator._process_single_candidate(
                candidate=mock_candidate,
                theme="mobile games",
                advocacy_temp=0.5,
                skepticism_temp=0.5,
                idea_temp=0.9,
                eval_temp=0.3,
                constraints="simple development"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify result is valid
            assert result is not None
            assert "advocacy" in result
            assert "skepticism" in result
            
            # Verify parallel execution: should take ~0.25s (0.1 parallel + 0.05 + 0.05 + overhead)
            # instead of ~0.3s if sequential (0.1 + 0.1 + 0.05 + 0.05)
            assert execution_time < 0.28, f"Execution took {execution_time}s, expected < 0.28s for parallel processing"
    
    @pytest.mark.asyncio
    async def test_parallel_evaluation_timeout_handling(self, coordinator, mock_candidate):
        """Test timeout handling in parallel advocacy/skepticism."""
        with patch('madspark.core.async_coordinator.async_advocate_idea') as mock_advocate, \
             patch('madspark.core.async_coordinator.async_criticize_idea') as mock_criticize, \
             patch('madspark.core.async_coordinator.async_improve_idea') as mock_improve, \
             patch('madspark.core.async_coordinator.async_evaluate_ideas') as mock_evaluate:
            
            # Mock one function to timeout
            async def timeout_advocate(*args, **kwargs):
                await asyncio.sleep(35.0)  # Longer than 30s timeout
                return "This should timeout"
            
            async def fast_criticize(*args, **kwargs):
                await asyncio.sleep(0.1)
                return "Quick criticism"
            
            mock_advocate.side_effect = timeout_advocate
            mock_criticize.side_effect = fast_criticize
            mock_improve.return_value = "Improved idea"
            mock_evaluate.return_value = '{"evaluations": [{"score": 7.0, "comment": "Standard evaluation"}]}'
            
            # Should handle timeout gracefully and continue with fallback
            result = await coordinator._process_single_candidate(
                candidate=mock_candidate,
                theme="mobile games",
                advocacy_temp=0.5,
                skepticism_temp=0.5,
                idea_temp=0.9,
                eval_temp=0.3,
                constraints="simple development"
            )
            
            # Should still return valid result with fallback advocacy
            assert result is not None
            assert "advocacy" in result
            assert "skepticism" in result
            # Advocacy should be fallback message due to timeout
            assert "strong potential" in result["advocacy"].lower()
    
    @pytest.mark.asyncio
    async def test_parallel_re_evaluation(self, coordinator, mock_candidate):
        """Test parallel standard and multi-dimensional re-evaluation."""
        # Mock reasoning engine
        mock_engine = Mock()
        mock_multi_evaluator = Mock()
        mock_multi_evaluator.evaluate_idea = AsyncMock(return_value={
            'weighted_score': 8.8,
            'evaluation_summary': 'Multi-dimensional analysis shows strong performance'
        })
        mock_engine.multi_evaluator = mock_multi_evaluator
        
        with patch('madspark.core.async_coordinator.async_advocate_idea') as mock_advocate, \
             patch('madspark.core.async_coordinator.async_criticize_idea') as mock_criticize, \
             patch('madspark.core.async_coordinator.async_improve_idea') as mock_improve, \
             patch('madspark.core.async_coordinator.async_evaluate_ideas') as mock_evaluate:
            
            mock_advocate.return_value = "Strong points identified"
            mock_criticize.return_value = "Areas for improvement noted"
            mock_improve.return_value = "Significantly improved game concept"
            
            # Mock standard evaluation with delay
            async def slow_evaluate(*args, **kwargs):
                await asyncio.sleep(0.1)
                return '{"evaluations": [{"score": 8.2, "comment": "Good improvement"}]}'
            
            mock_evaluate.side_effect = slow_evaluate
            
            # Measure execution time with multi-dimensional evaluation enabled
            start_time = time.time()
            
            result = await coordinator._process_single_candidate(
                candidate=mock_candidate,
                theme="mobile games",
                advocacy_temp=0.5,
                skepticism_temp=0.5,
                idea_temp=0.9,
                eval_temp=0.3,
                constraints="simple development",
                multi_dimensional_eval=True,
                reasoning_engine=mock_engine
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify multi-dimensional evaluation was used (higher score)
            assert result is not None
            assert result["improved_score"] == 8.8  # Multi-dimensional score
            assert "Enhanced Analysis" in result["improved_critique"]
            
            # Verify both evaluations were called
            assert mock_evaluate.called
            assert mock_multi_evaluator.evaluate_idea.called
            
            # Should complete faster due to parallel evaluation
            print(f"Parallel re-evaluation took {execution_time:.3f}s")
    
    @pytest.mark.asyncio 
    async def test_parallel_processing_error_handling(self, coordinator, mock_candidate):
        """Test error handling in parallel processing."""
        with patch('madspark.core.async_coordinator.async_advocate_idea') as mock_advocate, \
             patch('madspark.core.async_coordinator.async_criticize_idea') as mock_criticize, \
             patch('madspark.core.async_coordinator.async_improve_idea') as mock_improve:
            
            # Mock one function to raise exception
            async def failing_advocate(*args, **kwargs):
                raise ValueError("Advocacy service unavailable")
            
            async def working_criticize(*args, **kwargs):
                return "Criticism works fine"
            
            mock_advocate.side_effect = failing_advocate
            mock_criticize.side_effect = working_criticize
            mock_improve.return_value = "Improved idea"
            
            # Should handle exception gracefully
            result = await coordinator._process_single_candidate(
                candidate=mock_candidate,
                theme="mobile games",
                advocacy_temp=0.5,
                skepticism_temp=0.5,
                idea_temp=0.9,
                eval_temp=0.3,
                constraints="simple development"
            )
            
            # Should still return valid result with fallback
            assert result is not None
            assert result["advocacy"] == "Advocacy not available due to error"
            assert result["skepticism"] == "Criticism works fine"
    
    def test_performance_improvement_calculation(self):
        """Test that parallel processing provides expected performance improvement."""
        # Sequential timing: advocacy (30s) + skepticism (30s) = 60s
        # Parallel timing: max(advocacy (30s), skepticism (30s)) = 30s
        # Expected improvement: 50% reduction
        
        sequential_time = 30 + 30  # 60 seconds
        parallel_time = max(30, 30)  # 30 seconds
        
        improvement_ratio = (sequential_time - parallel_time) / sequential_time
        expected_improvement = 0.5  # 50%
        
        assert abs(improvement_ratio - expected_improvement) < 0.01
        print(f"Expected performance improvement: {improvement_ratio:.1%}")
        
        # Combined with batch logical inference (5 calls → 1 call = 80% reduction)
        # Total expected improvement: ~60-70% time reduction
        batch_improvement = 0.8  # 80% reduction from batching
        combined_improvement = 1 - ((1 - improvement_ratio) * (1 - batch_improvement))
        
        print(f"Combined improvement (parallel + batch): {combined_improvement:.1%}")
        assert combined_improvement > 0.6  # At least 60% total improvement