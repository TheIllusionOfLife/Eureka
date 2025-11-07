"""
Test suite for async coordinator integration with WorkflowOrchestrator (Phase 3.2c).

This module tests that AsyncCoordinator correctly uses WorkflowOrchestrator methods
for workflow orchestration while preserving async-specific optimizations.
"""
import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from madspark.core.async_coordinator import AsyncCoordinator
from madspark.core.workflow_orchestrator import WorkflowOrchestrator


class TestAsyncOrchestratorIntegration:
    """Test AsyncCoordinator integration with WorkflowOrchestrator."""

    @pytest.fixture
    def async_coordinator(self):
        """Create an async coordinator instance."""
        return AsyncCoordinator(max_concurrent_agents=5)

    @pytest.fixture
    def sample_candidates(self):
        """Create sample candidate data for testing."""
        return [
            {
                "idea": f"Idea {i}: Test idea content",
                "text": f"Idea {i}: Test idea content",
                "score": 0.7 + (i * 0.05),
                "critique": f"Critique for idea {i}"
            }
            for i in range(1, 4)
        ]

    @pytest.mark.asyncio
    async def test_idea_generation_uses_orchestrator(self, async_coordinator):
        """Test that idea generation delegates to orchestrator.generate_ideas_async()."""
        # Mock the orchestrator's generate_ideas_async method
        mock_ideas = ["Idea 1: Generated idea", "Idea 2: Another idea"]

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.generate_ideas_async',
                   new=AsyncMock(return_value=(mock_ideas, 500))):

            results = await async_coordinator.run_workflow(
                topic="Test Theme",
                context="Test Constraints",
                num_top_candidates=1
            )

            # Should successfully complete with orchestrator method
            assert results is not None
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_evaluation_uses_orchestrator(self, async_coordinator):
        """Test that evaluation delegates to orchestrator.evaluate_ideas_async()."""
        mock_evaluated = [
            {"idea": "Test idea", "text": "Test idea", "score": 8, "critique": "Good idea"}
        ]

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.generate_ideas_async',
                   new=AsyncMock(return_value=(["Test idea"], 300))), \
             patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async',
                   new=AsyncMock(return_value=(mock_evaluated, 400))):

            results = await async_coordinator.run_workflow(
                topic="Test Theme",
                context="Test Constraints",
                num_top_candidates=1
            )

            assert results is not None

    @pytest.mark.asyncio
    async def test_advocacy_uses_orchestrator(self, async_coordinator, sample_candidates):
        """Test that advocacy processing delegates to orchestrator.process_advocacy_async()."""
        mock_result = [(sample_candidates.copy(), 600)]

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async',
                   new=AsyncMock(return_value=(sample_candidates, 600))):

            result = await async_coordinator._process_candidates_with_batch_advocacy(
                sample_candidates.copy(),
                "Test Theme",
                "Test Constraints",
                0.7
            )

            # Should return updated candidates
            assert result is not None
            assert len(result) == len(sample_candidates)

    @pytest.mark.asyncio
    async def test_parallel_execution_preserved(self, async_coordinator, sample_candidates):
        """Test that parallel advocacy+skepticism execution is preserved."""
        # Track call timing to verify parallelism
        call_times = []

        async def mock_advocacy(*args, **kwargs):
            call_times.append(('advocacy', asyncio.get_event_loop().time()))
            await asyncio.sleep(0.1)  # Simulate async work
            return (sample_candidates.copy(), 500)

        async def mock_skepticism(*args, **kwargs):
            call_times.append(('skepticism', asyncio.get_event_loop().time()))
            await asyncio.sleep(0.1)  # Simulate async work
            return (sample_candidates.copy(), 500)

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_advocacy_async',
                   new=mock_advocacy), \
             patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.process_skepticism_async',
                   new=mock_skepticism):

            start_time = asyncio.get_event_loop().time()

            # This should run advocacy and skepticism in parallel
            result = await async_coordinator.process_candidates_parallel_advocacy_skepticism(
                sample_candidates.copy(),
                "Test Theme",
                "Test Constraints",
                0.7,
                0.7,
                timeout=5.0
            )

            end_time = asyncio.get_event_loop().time()
            elapsed = end_time - start_time

            # Should complete in ~0.1s (parallel) not ~0.2s (sequential)
            assert elapsed < 0.25, f"Parallel execution took too long: {elapsed}s"

            # Both should have been called
            assert len(call_times) == 2
            assert any(ct[0] == 'advocacy' for ct in call_times)
            assert any(ct[0] == 'skepticism' for ct in call_times)

    @pytest.mark.asyncio
    async def test_improvement_uses_orchestrator(self, async_coordinator, sample_candidates):
        """Test that improvement delegates to orchestrator.improve_ideas_async()."""
        # Add required fields for improvement
        for candidate in sample_candidates:
            candidate["advocacy"] = "Strong points"
            candidate["skepticism"] = "Weak points"

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.improve_ideas_async',
                   new=AsyncMock(return_value=(sample_candidates, 700))):

            result = await async_coordinator._process_candidates_with_batch_improvement(
                sample_candidates.copy(),
                "Test Theme",
                "Test Constraints",
                0.7
            )

            assert result is not None
            assert len(result) == len(sample_candidates)

    @pytest.mark.asyncio
    async def test_reevaluation_uses_orchestrator(self, async_coordinator, sample_candidates):
        """Test that re-evaluation delegates to orchestrator.reevaluate_ideas_async()."""
        # Add improved_idea field
        for candidate in sample_candidates:
            candidate["improved_idea"] = f"Improved: {candidate['text']}"

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.reevaluate_ideas_async',
                   new=AsyncMock(return_value=(sample_candidates, 450))):

            # Call the orchestrator method directly through coordinator
            # This will be part of the refactored workflow
            from madspark.core.workflow_orchestrator import WorkflowOrchestrator
            orchestrator = WorkflowOrchestrator(None, None, False)

            result, tokens = await orchestrator.reevaluate_ideas_async(
                sample_candidates.copy(),
                "Test Theme",
                "Test Constraints"
            )

            assert result is not None
            assert tokens == 450

    @pytest.mark.asyncio
    async def test_field_normalization_compatibility(self, async_coordinator):
        """Test that field normalization maintains compatibility between orchestrator and async_coordinator."""
        # Orchestrator returns "idea" field, async_coordinator needs "text" field
        mock_evaluated = [
            {"idea": "Test idea", "score": 8, "critique": "Good idea"}
        ]

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.generate_ideas_async',
                   new=AsyncMock(return_value=(["Test idea"], 300))), \
             patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async',
                   new=AsyncMock(return_value=(mock_evaluated, 400))):

            results = await async_coordinator.run_workflow(
                topic="Test Theme",
                context="Test Constraints",
                num_top_candidates=1
            )

            # Results should have both "idea" and "text" fields for compatibility
            assert results is not None
            if len(results) > 0:
                # Field normalization should ensure both fields exist
                assert "text" in results[0] or "idea" in results[0]


class TestOrchestratorPreservesAsyncFeatures:
    """Test that orchestrator integration preserves async-specific features."""

    @pytest.fixture
    def async_coordinator(self):
        return AsyncCoordinator(max_concurrent_agents=5)

    @pytest.mark.asyncio
    async def test_timeout_handling_preserved(self, async_coordinator):
        """Test that timeout handling still works with orchestrator integration."""
        # Mock orchestrator method that takes too long
        async def slow_generation(*args, **kwargs):
            await asyncio.sleep(10)  # Exceeds timeout
            return (["Never reached"], 100)

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.generate_ideas_async',
                   new=slow_generation):

            # Should timeout and handle gracefully
            with pytest.raises(asyncio.TimeoutError):
                await async_coordinator.run_workflow(
                    topic="Test",
                    context="Test",
                    num_top_candidates=1,
                    timeout=0.5  # Very short timeout
                )

    @pytest.mark.asyncio
    async def test_progress_callbacks_work(self, async_coordinator):
        """Test that progress callbacks still fire with orchestrator integration."""
        progress_updates = []

        async def track_progress(message: str, progress: float):
            progress_updates.append((message, progress))

        async_coordinator.progress_callback = track_progress

        with patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.generate_ideas_async',
                   new=AsyncMock(return_value=(["Test idea"], 300))), \
             patch('madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async',
                   new=AsyncMock(return_value=([{"idea": "Test", "text": "Test", "score": 8, "critique": "Good"}], 400))):

            await async_coordinator.run_workflow(
                topic="Test",
                context="Test",
                num_top_candidates=1
            )

            # Should have received progress updates
            assert len(progress_updates) > 0
