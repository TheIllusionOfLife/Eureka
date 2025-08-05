"""Test parameter standardization across the MadSpark workflow.

This test suite ensures consistent use of 'topic' and 'context' parameters
throughout all layers of the application.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from typing import Dict, Any

# Test data
TEST_TOPIC = "sustainable urban farming"
TEST_CONTEXT = "low-cost solutions for apartment dwellers"


class TestBackendParameterStandardization:
    """Test that the backend API uses topic/context consistently."""
    
    @pytest.mark.asyncio
    async def test_api_accepts_topic_context_parameters(self):
        """Test that API endpoints accept topic and context parameters."""
        from web.backend.main import IdeaGenerationRequest
        
        # Should accept topic and context
        request = IdeaGenerationRequest(
            topic=TEST_TOPIC,
            context=TEST_CONTEXT
        )
        assert request.topic == TEST_TOPIC
        assert request.context == TEST_CONTEXT
    
    @pytest.mark.asyncio
    async def test_api_backward_compatibility(self):
        """Test that API still accepts theme/constraints for backward compatibility."""
        from web.backend.main import IdeaGenerationRequest
        
        # Should still accept theme/constraints via aliases
        request = IdeaGenerationRequest(
            context=TEST_TOPIC,
            context=TEST_CONTEXT
        )
        # But internally map to topic/context
        assert request.topic == TEST_TOPIC
        assert request.context == TEST_CONTEXT
    
    @pytest.mark.asyncio
    async def test_generate_ideas_endpoint_uses_topic_context(self):
        """Test that generate_ideas endpoint passes topic/context to coordinator."""
        from web.backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        with patch('web.backend.main.AsyncCoordinator') as mock_coordinator:
            mock_instance = AsyncMock()
            mock_instance.run_workflow = AsyncMock(return_value=[])
            mock_coordinator.return_value = mock_instance
            
            # Make request with topic/context
            response = client.post("/api/generate-ideas", json={
                "topic": TEST_TOPIC,
                "context": TEST_CONTEXT,
                "num_top_candidates": 1
            })
            
            # Verify coordinator was called with topic/context
            mock_instance.run_workflow.assert_called_once()
            call_args = mock_instance.run_workflow.call_args[1]
            assert call_args['topic'] == TEST_TOPIC
            assert call_args['context'] == TEST_CONTEXT


class TestCoordinatorParameterStandardization:
    """Test that coordinators use topic/context consistently."""
    
    @pytest.mark.asyncio
    async def test_async_coordinator_run_workflow_signature(self):
        """Test AsyncCoordinator.run_workflow accepts topic/context."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        # Mock the internal workflow method
        with patch.object(coordinator, '_run_workflow_internal', new_callable=AsyncMock) as mock_workflow:
            mock_workflow.return_value = []
            
            # Call with topic/context
            await coordinator.run_workflow(
                topic=TEST_TOPIC,
                context=TEST_CONTEXT,
                num_top_candidates=1
            )
            
            # Verify internal method was called with topic/context
            mock_workflow.assert_called_once()
            call_args = mock_workflow.call_args[1]
            assert call_args['topic'] == TEST_TOPIC
            assert call_args['context'] == TEST_CONTEXT
    
    @pytest.mark.asyncio 
    async def test_coordinator_passes_context_as_criteria_to_evaluator(self):
        """Test that coordinator passes context as criteria to the evaluator."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        with patch('src.madspark.core.async_coordinator.async_evaluate_ideas') as mock_eval:
            mock_eval.return_value = json.dumps([{"score": 8, "comment": "Good"}])
            
            with patch('src.madspark.core.async_coordinator.async_generate_ideas') as mock_gen:
                mock_gen.return_value = json.dumps([{"idea_number": 1, "description": "Test idea"}])
                
                await coordinator.run_workflow(
                    topic=TEST_TOPIC,
                    context=TEST_CONTEXT,
                    num_top_candidates=1
                )
                
                # Verify evaluator was called with context as criteria
                # Check the first call (initial evaluation, not re-evaluation)
                assert mock_eval.call_count >= 1
                first_call_args = mock_eval.call_args_list[0][1]
                assert first_call_args['criteria'] == TEST_CONTEXT
                assert first_call_args['context'] == TEST_TOPIC


class TestAgentParameterStandardization:
    """Test that agents use consistent parameter names."""
    
    def test_idea_generator_uses_topic_context(self):
        """Test that idea generator accepts topic and context."""
        from src.madspark.agents.idea_generator import build_generation_prompt
        
        prompt = build_generation_prompt(
            topic=TEST_TOPIC,
            context=TEST_CONTEXT
        )
        
        # Verify the prompt contains both topic and context
        assert TEST_TOPIC in prompt
        assert TEST_CONTEXT in prompt
    
    def test_critic_uses_criteria_and_context(self):
        """Test that critic accepts ideas, criteria, and context."""
        from src.madspark.agents.critic import evaluate_ideas
        
        with patch('src.madspark.agents.critic.critic_client') as mock_client:
            mock_client.models.generate_content.return_value = Mock(text='{"score": 8, "comment": "Good"}')
            
            result = evaluate_ideas(
                ideas="Test idea",
                criteria=TEST_CONTEXT,  # Context is passed as criteria
                context=TEST_TOPIC,     # Topic is passed as context
                use_structured_output=False
            )
            
            # Verify the function accepts these parameters
            assert result is not None
    
    def test_advocate_uses_context(self):
        """Test that advocate accepts context parameter."""
        from src.madspark.agents.advocate import advocate_idea
        
        with patch('src.madspark.agents.advocate.advocate_client') as mock_client:
            mock_client.models.generate_content.return_value = Mock(text="Strong advocacy")
            
            result = advocate_idea(
                idea="Test idea",
                evaluation="Good evaluation",
                context=TEST_TOPIC,  # Should accept context, not theme
                use_structured_output=False
            )
            
            assert result is not None
    
    def test_improvement_agent_uses_context(self):
        """Test that improvement agent uses context instead of theme."""
        from src.madspark.agents.idea_generator import improve_idea
        
        with patch('src.madspark.agents.idea_generator.idea_generator_client') as mock_client:
            mock_client.models.generate_content.return_value = Mock(text="Improved idea")
            
            # Should accept context parameter (not theme)
            result = improve_idea(
                original_idea="Test idea",
                critique="Needs work",
                advocacy_points="Good potential",
                skeptic_points="Some risks",
                context=TEST_TOPIC,  # Changed from theme to context
                temperature=0.9
            )
            
            assert result is not None


class TestBatchOperationsParameterStandardization:
    """Test that batch operations pass context correctly."""
    
    def test_batch_advocacy_includes_context(self):
        """Test that batch advocacy preparation includes context."""
        from src.madspark.core.batch_operations_base import BatchOperationsBase
        
        ops = BatchOperationsBase()
        candidates = [
            {"text": "Idea 1", "critique": "Good", "context": TEST_TOPIC},
            {"text": "Idea 2", "critique": "Better", "context": TEST_TOPIC}
        ]
        
        # Prepare advocacy input - should include context
        advocacy_input = ops.prepare_advocacy_input_with_context(candidates)
        
        assert len(advocacy_input) == 2
        for item in advocacy_input:
            assert "idea" in item
            assert "evaluation" in item
            assert "context" in item
            assert item["context"] == TEST_TOPIC
    
    def test_batch_improvement_includes_all_context(self):
        """Test that batch improvement includes all necessary context."""
        from src.madspark.core.batch_operations_base import BatchOperationsBase
        
        ops = BatchOperationsBase()
        candidates = [
            {
                "text": "Idea 1",
                "critique": "Good",
                "advocacy": "Strong points",
                "skepticism": "Some risks",
                "context": TEST_TOPIC,
                "logical_inference": {"conclusion": "Feasible"}
            }
        ]
        
        # Prepare improvement input - should include all feedback and context
        improvement_input = ops.prepare_improvement_input_with_context(candidates)
        
        assert len(improvement_input) == 1
        item = improvement_input[0]
        assert "original_idea" in item
        assert "critique" in item
        assert "advocacy" in item
        assert "skepticism" in item
        assert "context" in item
        assert "logical_inference" in item


if __name__ == "__main__":
    pytest.main([__file__, "-v"])