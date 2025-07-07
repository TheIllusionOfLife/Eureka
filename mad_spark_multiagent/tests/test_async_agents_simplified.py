"""Simplified tests for async agent execution (Phase 2.3)

Focus on testing the core async functionality without complex mocking.
"""
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest

from async_coordinator import (
    AsyncCoordinator,
    run_async_workflow
)
from temperature_control import TemperatureManager


class TestAsyncExecution:
    """Test core async execution capabilities."""

    @pytest.mark.asyncio
    async def test_basic_async_workflow(self):
        """Test basic async workflow execution with mocked agents."""
        # Create a coordinator
        coordinator = AsyncCoordinator()
        
        # Mock the agent functions at module level
        with patch('async_coordinator.generate_ideas') as mock_gen:
            with patch('async_coordinator.evaluate_ideas') as mock_eval:
                with patch('async_coordinator.advocate_idea') as mock_adv:
                    with patch('async_coordinator.criticize_idea') as mock_crit:
                        # Set return values
                        mock_gen.return_value = "Idea 1\nIdea 2\nIdea 3"
                        mock_eval.return_value = '{"score": 8, "comment": "Good"}\n{"score": 7, "comment": "Fair"}\n{"score": 9, "comment": "Excellent"}'
                        mock_adv.return_value = "Strong support for this idea"
                        mock_crit.return_value = "Some minor concerns"
                        
                        # Run workflow
                        results = await coordinator.run_workflow(
                            theme="test theme",
                            constraints="test constraints",
                            num_top_candidates=2
                        )
        
        # Verify results
        assert len(results) == 2
        assert all('idea' in r for r in results)
        assert results[0]['initial_score'] >= results[1]['initial_score']

    @pytest.mark.asyncio
    async def test_parallel_execution_performance(self):
        """Test that parallel execution is faster than sequential."""
        coordinator = AsyncCoordinator(max_concurrent_agents=4)
        
        # Track timing
        call_count = 0
        async def slow_advocate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate API delay
            return f"Advocacy {call_count}"
        
        async def slow_critic(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API delay  
            return f"Criticism"
        
        # Mock the async functions
        with patch('async_coordinator.async_advocate_idea', side_effect=slow_advocate):
            with patch('async_coordinator.async_criticize_idea', side_effect=slow_critic):
                # Process 3 candidates
                candidates = [
                    {"text": f"Idea {i}", "score": 8-i, "critique": "Good"}
                    for i in range(3)
                ]
                
                start = time.time()
                results = await coordinator.process_top_candidates(
                    candidates, "test theme"
                )
                duration = time.time() - start
        
        # Should take ~0.2s (advocacy + criticism in sequence per candidate)
        # but with parallelism should be faster
        assert len(results) == 3
        assert duration < 0.4  # Some parallelism occurred
        assert call_count == 3  # All advocates were called

    @pytest.mark.asyncio
    async def test_progress_callback(self):
        """Test progress callback functionality."""
        progress_updates = []
        
        async def callback(msg, progress):
            progress_updates.append((msg, progress))
        
        coordinator = AsyncCoordinator(progress_callback=callback)
        
        # Mock all agent functions
        with patch('async_coordinator.generate_ideas', return_value="Idea 1"):
            with patch('async_coordinator.evaluate_ideas', return_value='{"score": 8, "comment": "Good"}'):
                with patch('async_coordinator.advocate_idea', return_value="Support"):
                    with patch('async_coordinator.criticize_idea', return_value="Concern"):
                        await coordinator.run_workflow(
                            theme="test",
                            constraints="test",
                            num_top_candidates=1
                        )
        
        # Check progress updates
        assert len(progress_updates) > 0
        assert any("Starting" in msg for msg, _ in progress_updates)
        assert any("Generating ideas" in msg for msg, _ in progress_updates)
        assert any(progress == 1.0 for _, progress in progress_updates)

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors are properly propagated."""
        coordinator = AsyncCoordinator()
        
        # Mock generate_ideas to raise an error
        with patch('async_coordinator.generate_ideas', side_effect=RuntimeError("API Error")):
            with pytest.raises(RuntimeError) as exc_info:
                await coordinator.run_workflow(
                    theme="test",
                    constraints="test"
                )
            assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_semaphore_limits(self):
        """Test that semaphore properly limits concurrency."""
        max_concurrent = 2
        coordinator = AsyncCoordinator(max_concurrent_agents=max_concurrent)
        
        # Track concurrent executions
        current_concurrent = 0
        max_seen = 0
        
        async def tracked_function(*args, **kwargs):
            nonlocal current_concurrent, max_seen
            current_concurrent += 1
            max_seen = max(max_seen, current_concurrent)
            await asyncio.sleep(0.05)
            current_concurrent -= 1
            return "Result"
        
        # Run many tasks
        tasks = []
        for i in range(5):
            task = coordinator._run_with_semaphore(
                tracked_function()
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Verify concurrency was limited
        assert max_seen <= max_concurrent

    @pytest.mark.asyncio
    async def test_temperature_manager_integration(self):
        """Test integration with temperature manager."""
        temp_manager = TemperatureManager.from_preset('creative')
        
        # Capture temperatures used
        used_temps = {}
        
        def capture_temp(name):
            def wrapper(*args, **kwargs):
                # The temperature is passed as a keyword argument
                used_temps[name] = kwargs.get('temperature', 0)
                return f"{name} result"
            return wrapper
        
        with patch('async_coordinator.generate_ideas', side_effect=capture_temp('generate')):
            with patch('async_coordinator.evaluate_ideas', side_effect=capture_temp('evaluate')):
                with patch('async_coordinator.advocate_idea', side_effect=capture_temp('advocate')):
                    with patch('async_coordinator.criticize_idea', side_effect=capture_temp('criticize')):
                        results = await run_async_workflow(
                            theme="test",
                            constraints="test",
                            temperature_manager=temp_manager,
                            num_top_candidates=1
                        )
        
        # Verify functions were called (temperature passing verified in coordinator tests)
        assert 'generate' in used_temps
        assert 'evaluate' in used_temps
        assert 'advocate' in used_temps
        assert 'criticize' in used_temps