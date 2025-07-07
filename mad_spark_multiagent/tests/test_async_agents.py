"""Tests for async agent execution (Phase 2.3)

This test module verifies the async agent execution functionality
for concurrent processing of agent calls.
"""
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import pytest

from async_coordinator import (
    AsyncCoordinator,
    async_generate_ideas,
    async_evaluate_ideas,
    async_advocate_idea,
    async_criticize_idea,
    run_async_workflow
)
from temperature_control import TemperatureManager
from enhanced_reasoning import ReasoningEngine


class TestAsyncAgentExecution:
    """Test cases for async agent execution functionality."""

    @pytest.mark.asyncio
    async def test_async_idea_generation(self):
        """Test async idea generation with mock."""
        mock_response = "Idea 1: Solar panels\nIdea 2: Wind turbines\nIdea 3: Hydroelectric"
        
        with patch('agent_defs.idea_generator.generate_ideas', 
                   return_value=mock_response):
            result = await async_generate_ideas(
                topic="renewable energy",
                context="urban environment",
                temperature=0.9
            )
            
        assert result == mock_response
        assert "Solar panels" in result
        assert "Wind turbines" in result

    @pytest.mark.asyncio
    async def test_async_evaluation(self):
        """Test async evaluation with mock."""
        mock_response = """{"score": 8, "comment": "Excellent feasibility"}
{"score": 7, "comment": "Good scalability"}
{"score": 9, "comment": "High impact potential"}"""
        
        with patch('agent_defs.critic.evaluate_ideas',
                   return_value=mock_response):
            result = await async_evaluate_ideas(
                ideas="Idea 1\nIdea 2\nIdea 3",
                criteria="feasibility and impact",
                context="urban planning",
                temperature=0.3
            )
            
        assert result == mock_response
        assert "Excellent feasibility" in result

    @pytest.mark.asyncio
    async def test_concurrent_agent_calls(self):
        """Test concurrent execution of multiple agent calls."""
        # Mock responses
        mock_idea_response = "Idea 1\nIdea 2\nIdea 3"
        mock_eval_response = '{"score": 8, "comment": "Good"}'
        
        # Track call timings
        call_times = []
        
        async def mock_generate_with_delay(*args, **kwargs):
            call_times.append(('generate_start', time.time()))
            await asyncio.sleep(0.1)  # Simulate API delay
            call_times.append(('generate_end', time.time()))
            return mock_idea_response
            
        async def mock_evaluate_with_delay(*args, **kwargs):
            call_times.append(('evaluate_start', time.time()))
            await asyncio.sleep(0.1)  # Simulate API delay
            call_times.append(('evaluate_end', time.time()))
            return mock_eval_response
        
        with patch('agent_defs.idea_generator.generate_ideas',
                   side_effect=lambda *args, **kwargs: mock_idea_response):
            with patch('agent_defs.critic.evaluate_ideas',
                       side_effect=lambda *args, **kwargs: mock_eval_response):
                # Create async wrapper functions that add delays
                async def async_gen(*args, **kwargs):
                    return await mock_generate_with_delay(*args, **kwargs)
                    
                async def async_eval(*args, **kwargs):
                    return await mock_evaluate_with_delay(*args, **kwargs)
                
                with patch('async_coordinator.async_generate_ideas', async_gen):
                    with patch('async_coordinator.async_evaluate_ideas', async_eval):
                        # Run two operations concurrently
                        start_time = time.time()
                        results = await asyncio.gather(
                            async_generate_ideas("topic1", "context1"),
                            async_evaluate_ideas("ideas", "criteria", "context")
                        )
                        end_time = time.time()
        
        # Verify both operations completed
        assert len(results) == 2
        assert results[0] == mock_idea_response
        assert results[1] == mock_eval_response
        
        # Verify concurrent execution (should take ~0.1s, not 0.2s)
        total_time = end_time - start_time
        assert total_time < 0.15  # Allow some overhead

    @pytest.mark.asyncio
    async def test_async_coordinator_workflow(self):
        """Test complete async coordinator workflow."""
        coordinator = AsyncCoordinator()
        
        # Mock all agent responses
        mock_ideas = "Solar power station\nWind farm network\nTidal energy system"
        mock_evaluations = """{"score": 8, "comment": "Excellent renewable solution"}
{"score": 7, "comment": "Good for windy regions"}  
{"score": 9, "comment": "Innovative coastal solution"}"""
        mock_advocacy = "This solution offers sustainable energy..."
        mock_skepticism = "Implementation challenges include..."
        
        with patch('agent_defs.idea_generator.generate_ideas',
                   return_value=mock_ideas):
            with patch('agent_defs.critic.evaluate_ideas',
                       return_value=mock_evaluations):
                with patch('agent_defs.advocate.advocate_idea',
                           return_value=mock_advocacy):
                    with patch('agent_defs.skeptic.criticize_idea',
                               return_value=mock_skepticism):
                        results = await coordinator.run_workflow(
                            theme="renewable energy",
                            constraints="coastal city implementation",
                            num_top_candidates=2
                        )
        
        # Verify results
        assert len(results) == 2
        assert all('idea' in r for r in results)
        assert all('initial_score' in r for r in results)
        assert all('advocacy' in r for r in results)
        assert all('skepticism' in r for r in results)

    @pytest.mark.asyncio
    async def test_parallel_advocacy_skepticism(self):
        """Test parallel execution of advocacy and skepticism for multiple ideas."""
        coordinator = AsyncCoordinator()
        
        # Track concurrent calls
        advocacy_calls = []
        skepticism_calls = []
        
        async def mock_advocate_async(idea, evaluation, context, temperature=0.5):
            advocacy_calls.append(time.time())
            await asyncio.sleep(0.05)  # Simulate API delay
            return f"Advocating for: {idea[:20]}..."
            
        async def mock_skeptic_async(idea, advocacy, context, temperature=0.5):
            skepticism_calls.append(time.time())
            await asyncio.sleep(0.05)  # Simulate API delay
            return f"Concerns about: {idea[:20]}..."
        
        with patch('async_coordinator.async_advocate_idea',
                   side_effect=mock_advocate_async):
            with patch('async_coordinator.async_criticize_idea',
                       side_effect=mock_skeptic_async):
                # Process multiple ideas
                ideas = [
                    {"text": "Solar panels on rooftops", "score": 8, "critique": "Good"},
                    {"text": "Community wind turbines", "score": 7, "critique": "Fair"},
                    {"text": "Geothermal heating", "score": 9, "critique": "Excellent"}
                ]
                
                start_time = time.time()
                results = await coordinator.process_top_candidates(
                    ideas, "renewable energy"
                )
                end_time = time.time()
        
        # Verify all ideas were processed
        assert len(results) == 3
        assert all('advocacy' in r for r in results)
        assert all('skepticism' in r for r in results)
        
        # Verify parallel execution
        total_time = end_time - start_time
        assert total_time < 0.2  # Should be much less than 0.3s (sequential)

    @pytest.mark.asyncio
    async def test_error_handling_in_async_workflow(self):
        """Test error handling in async workflow."""
        coordinator = AsyncCoordinator()
        
        # Mock a failing agent
        with patch('agent_defs.idea_generator.generate_ideas',
                   side_effect=Exception("API Error")):
            with pytest.raises(Exception) as exc_info:
                await coordinator.run_workflow(
                    theme="test",
                    constraints="test"
                )
            
            assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_progress_callback_integration(self):
        """Test progress callback during async execution."""
        progress_updates = []
        
        async def progress_callback(message: str, progress: float):
            progress_updates.append((message, progress))
        
        coordinator = AsyncCoordinator(progress_callback=progress_callback)
        
        # Mock responses
        with patch('agent_defs.idea_generator.generate_ideas',
                   return_value="Idea 1\nIdea 2"):
            with patch('agent_defs.critic.evaluate_ideas',
                       return_value='{"score": 8, "comment": "Good"}\n{"score": 7, "comment": "Fair"}'):
                with patch('agent_defs.advocate.advocate_idea',
                           return_value="Great idea"):
                    with patch('agent_defs.skeptic.criticize_idea',
                               return_value="Some concerns"):
                        await coordinator.run_workflow(
                            theme="test",
                            constraints="test",
                            num_top_candidates=1
                        )
        
        # Verify progress updates were sent
        assert len(progress_updates) > 0
        assert any("Generating ideas" in update[0] for update in progress_updates)
        assert any("Evaluating ideas" in update[0] for update in progress_updates)
        assert any(update[1] == 1.0 for update in progress_updates)  # Completion

    @pytest.mark.asyncio
    async def test_cancellation_support(self):
        """Test cancellation of async workflow."""
        coordinator = AsyncCoordinator()
        
        # Mock slow agent
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(1.0)  # Long delay
            return "Ideas"
        
        with patch('async_coordinator.async_generate_ideas',
                   side_effect=slow_generate):
            # Start workflow and cancel it
            task = asyncio.create_task(
                coordinator.run_workflow("test", "test")
            )
            
            await asyncio.sleep(0.1)  # Let it start
            task.cancel()
            
            with pytest.raises(asyncio.CancelledError):
                await task

    @pytest.mark.asyncio 
    async def test_configurable_parallelism(self):
        """Test configurable parallelism limits."""
        coordinator = AsyncCoordinator(max_concurrent_agents=2)
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        async def mock_agent_with_tracking(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)
            concurrent_count -= 1
            return "Result"
        
        # Patch all agents with tracking
        with patch('async_coordinator.async_advocate_idea',
                   side_effect=mock_agent_with_tracking):
            with patch('async_coordinator.async_criticize_idea',
                       side_effect=mock_agent_with_tracking):
                # Process 4 ideas with max 2 concurrent
                ideas = [
                    {"text": f"Idea {i}", "score": 8, "critique": "Good"}
                    for i in range(4)
                ]
                
                await coordinator.process_top_candidates(ideas, "test")
        
        # Verify parallelism was limited
        assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_run_async_workflow_integration():
    """Test the main async workflow entry point."""
    # Mock responses
    mock_ideas = "Idea 1\nIdea 2\nIdea 3"
    mock_evaluations = """{"score": 8, "comment": "Good"}
{"score": 9, "comment": "Excellent"}
{"score": 7, "comment": "Fair"}"""
    mock_advocacy = "Strong support"
    mock_skepticism = "Minor concerns"
    
    with patch('mad_spark_multiagent.agent_defs.idea_generator.generate_ideas',
               return_value=mock_ideas):
        with patch('agent_defs.critic.evaluate_ideas',
                   return_value=mock_evaluations):
            with patch('mad_spark_multiagent.agent_defs.advocate.advocate_idea',
                       return_value=mock_advocacy):
                with patch('mad_spark_multiagent.agent_defs.skeptic.criticize_idea',
                           return_value=mock_skepticism):
                    # Test with temperature manager
                    temp_manager = TemperatureManager()
                    results = await run_async_workflow(
                        theme="sustainable cities",
                        constraints="budget-friendly",
                        temperature_manager=temp_manager,
                        num_top_candidates=2
                    )
    
    assert len(results) == 2
    assert results[0]['initial_score'] >= results[1]['initial_score']  # Sorted by score
    assert all('advocacy' in r and 'skepticism' in r for r in results)