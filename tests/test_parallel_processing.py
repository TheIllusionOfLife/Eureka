"""Tests for parallel processing implementation.

This test suite ensures that:
1. Multiple operations can run concurrently when appropriate
2. No race conditions or data loss occurs
3. Proper timeout handling is in place
4. Performance improvements are measurable
"""
import asyncio
import time
import pytest
from unittest.mock import patch, AsyncMock


class TestParallelAdvocacySkepticism:
    """Test that advocacy and skepticism can run in parallel."""
    
    @pytest.mark.asyncio
    async def test_advocacy_and_skepticism_run_concurrently(self):
        """Test that advocacy and skepticism batch operations run at the same time."""
        from src.madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()

        # Create test candidates
        test_candidates = [
            {"text": "Idea 1", "critique": "Good", "context": "test context"},
            {"text": "Idea 2", "critique": "Better", "context": "test context"}
        ]

        # Track when each operation starts and ends
        advocacy_start = None
        advocacy_end = None
        skepticism_start = None
        skepticism_end = None

        async def mock_advocacy(candidates, topic, context):
            nonlocal advocacy_start, advocacy_end
            advocacy_start = time.time()
            await asyncio.sleep(0.1)  # Simulate async work
            advocacy_end = time.time()
            for i, candidate in enumerate(candidates):
                candidate["advocacy"] = f"Advocacy {i + 1}"
            return candidates, 100

        async def mock_skepticism(candidates, topic, context):
            nonlocal skepticism_start, skepticism_end
            skepticism_start = time.time()
            await asyncio.sleep(0.1)  # Simulate async work
            skepticism_end = time.time()
            for i, candidate in enumerate(candidates):
                candidate["skepticism"] = f"Skepticism {i + 1}"
            return candidates, 100

        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async",
            new=AsyncMock(side_effect=mock_advocacy)
        ), patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_skepticism_async",
            new=AsyncMock(side_effect=mock_skepticism)
        ):
            # Process candidates with parallel advocacy and skepticism
            await coordinator.process_candidates_parallel_advocacy_skepticism(
                test_candidates,
                "test topic",
                "test context",
                0.5,
                0.5
            )

            # Verify both operations ran
            assert advocacy_start is not None
            assert skepticism_start is not None

            # Verify they overlapped (ran concurrently)
            # If sequential: advocacy_end would be before skepticism_start
            # If parallel: skepticism_start would be before advocacy_end
            assert skepticism_start < advocacy_end, "Skepticism should start before advocacy finishes"

            # Verify results were properly assigned
            assert test_candidates[0]["advocacy"] == "Advocacy 1"
            assert test_candidates[0]["skepticism"] == "Skepticism 1"
            assert test_candidates[1]["advocacy"] == "Advocacy 2"
            assert test_candidates[1]["skepticism"] == "Skepticism 2"


class TestParallelEvaluationImprovement:
    """Test that re-evaluation and improvement can run in parallel after both complete."""
    
    @pytest.mark.asyncio
    async def test_evaluation_and_improvement_dependencies(self):
        """Test that improvement waits for advocacy and skepticism before starting."""
        from src.madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()

        # Create test candidates with advocacy and skepticism
        test_candidates = [
            {
                "text": "Idea 1",
                "critique": "Good",
                "context": "test context",
                "advocacy": "Strong points",
                "skepticism": "Some concerns",
                "score": 7  # Add initial score
            }
        ]

        # Track operation order
        operation_order = []

        async def mock_improvement(candidates, topic, context):
            operation_order.append("improvement")
            for candidate in candidates:
                candidate["improved_idea"] = "Better Idea 1"
            return candidates, 100

        async def mock_evaluation(*args, **kwargs):
            operation_order.append("evaluation")
            return '[{"score": 9, "comment": "Much better"}]'

        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.improve_ideas_async",
            new=AsyncMock(side_effect=mock_improvement)
        ), patch('src.madspark.core.async_coordinator.async_evaluate_ideas', mock_evaluation):
            # Process improvement and re-evaluation
            await coordinator.process_candidates_parallel_improvement_evaluation(
                test_candidates,
                "test topic",
                "test context",
                0.9,
                0.7
            )

            # Verify improvement ran before evaluation
            assert operation_order == ["improvement", "evaluation"]

            # Verify results
            assert test_candidates[0]["improved_idea"] == "Better Idea 1"
            assert test_candidates[0]["improved_score"] == 9


class TestTimeoutHandling:
    """Test timeout handling in parallel operations."""
    
    @pytest.mark.asyncio
    async def test_parallel_operations_respect_timeout(self):
        """Test that parallel operations are cancelled if they exceed timeout."""
        from src.madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()

        test_candidates = [{"text": "Idea", "critique": "Good", "context": "test"}]

        async def slow_operation(candidates, topic, context):
            await asyncio.sleep(2)  # Longer than timeout
            return candidates, 100

        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async",
            new=AsyncMock(side_effect=slow_operation)
        ), patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_skepticism_async",
            new=AsyncMock(side_effect=slow_operation)
        ):
            # Process with short timeout
            with pytest.raises(asyncio.TimeoutError):
                await coordinator.process_candidates_parallel_advocacy_skepticism(
                    test_candidates,
                    "test topic",
                    "test context",
                    0.5,
                    0.5,
                    timeout=0.1
                )


class TestDataIntegrity:
    """Test that parallel processing maintains data integrity."""
    
    @pytest.mark.asyncio
    async def test_no_data_loss_in_parallel_processing(self):
        """Test that all candidates are processed without data loss."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        import src.madspark.core.workflow_orchestrator

        coordinator = AsyncCoordinator()

        # Create many candidates to test concurrent processing
        num_candidates = 10
        test_candidates = [
            {"text": f"Idea {i}", "critique": f"Critique {i}", "context": "test"}
            for i in range(num_candidates)
        ]

        # Save originals
        original_advocacy = src.madspark.core.workflow_orchestrator.advocate_ideas_batch
        original_skepticism = src.madspark.core.workflow_orchestrator.criticize_ideas_batch

        def mock_batch_operation(items, *args, **kwargs):
            # Return results for all items
            return ([{"formatted": f"Result for {item['idea']}"} for item in items], 100)

        try:
            # Patch WorkflowOrchestrator batch functions
            src.madspark.core.workflow_orchestrator.advocate_ideas_batch = mock_batch_operation
            src.madspark.core.workflow_orchestrator.criticize_ideas_batch = mock_batch_operation

            await coordinator.process_candidates_parallel_advocacy_skepticism(
                test_candidates,
                "test topic",
                "test context",
                0.5,
                0.5
            )

            # Verify all candidates were processed
            for i, candidate in enumerate(test_candidates):
                assert "advocacy" in candidate
                assert "skepticism" in candidate
                assert candidate["advocacy"] == f"Result for Idea {i}"
                assert candidate["skepticism"] == f"Result for Idea {i}"
        finally:
            # Restore originals
            src.madspark.core.workflow_orchestrator.advocate_ideas_batch = original_advocacy
            src.madspark.core.workflow_orchestrator.criticize_ideas_batch = original_skepticism


class TestPerformanceImprovement:
    """Test that parallel processing improves performance."""
    
    @pytest.mark.asyncio
    async def test_parallel_faster_than_sequential(self):
        """Test that parallel processing is faster than sequential."""
        from src.madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()

        test_candidates = [{"text": "Idea", "critique": "Good", "context": "test"}]

        # Simulate operations that take 100ms each
        async def timed_operation(candidates, topic, context):
            await asyncio.sleep(0.1)
            for candidate in candidates:
                candidate["advocacy"] = "Result"
                candidate["skepticism"] = "Result"
            return candidates, 100

        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async",
            new=AsyncMock(side_effect=timed_operation)
        ), patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_skepticism_async",
            new=AsyncMock(side_effect=timed_operation)
        ):
            # Measure parallel execution time
            start = time.time()
            await coordinator.process_candidates_parallel_advocacy_skepticism(
                test_candidates,
                "test topic",
                "test context",
                0.5,
                0.5
            )
            parallel_time = time.time() - start

            # If operations ran in parallel, should take ~0.1s
            # If sequential, would take ~0.2s
            # Allow some overhead
            assert parallel_time < 0.15, f"Parallel execution took {parallel_time}s, should be < 0.15s"


class TestErrorHandlingInParallel:
    """Test error handling in parallel operations."""
    
    @pytest.mark.asyncio
    async def test_one_operation_fails_other_continues(self):
        """Test that if one parallel operation fails, the other still completes."""
        from src.madspark.core.async_coordinator import AsyncCoordinator

        coordinator = AsyncCoordinator()

        test_candidates = [{"text": "Idea", "critique": "Good", "context": "test"}]

        async def failing_operation(candidates, topic, context):
            raise Exception("Simulated failure")

        async def successful_operation(candidates, topic, context):
            for candidate in candidates:
                candidate["skepticism"] = "Success"
            return candidates, 100

        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async",
            new=AsyncMock(side_effect=failing_operation)
        ), patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_skepticism_async",
            new=AsyncMock(side_effect=successful_operation)
        ):
            # Process should continue despite one failure
            await coordinator.process_candidates_parallel_advocacy_skepticism(
                test_candidates,
                "test topic",
                "test context",
                0.5,
                0.5
            )

            # Verify the successful operation completed
            assert test_candidates[0]["skepticism"] == "Success"

            # Verify the failed operation has fallback
            assert "advocacy" in test_candidates[0]
            assert "failed" in test_candidates[0]["advocacy"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])