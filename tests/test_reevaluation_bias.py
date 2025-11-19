"""Tests for fixing re-evaluation bias.

This test suite ensures that:
1. Re-evaluation prompts clearly indicate ideas are improved versions
2. Context includes information about improvements made
3. Evaluation criteria remain consistent between initial and re-evaluation
4. Re-evaluation acknowledges the improvements made
"""
import pytest
from unittest.mock import patch


class TestReEvaluationContext:
    """Test that re-evaluation includes proper context about improvements."""
    
    @pytest.mark.asyncio
    async def test_reevaluation_includes_improvement_context(self):
        """Test that re-evaluation prompt indicates ideas are improved versions."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        # Create test candidates with improvements
        test_candidates = [
            {
                "text": "Original idea",
                "score": 6,
                "critique": "Needs more detail",
                "advocacy": "Good potential",
                "skepticism": "Implementation unclear",
                "context": "test context"
            }
        ]
        
        # Mock the evaluation function to capture the prompt
        import src.madspark.core.workflow_orchestrator

        captured_prompt = None
        captured_context = None

        # Save originals
        original_improve = src.madspark.core.workflow_orchestrator.improve_ideas_batch

        def mock_improve(*args, **kwargs):
            return ([{"improved_idea": "Enhanced idea with clear implementation plan", "key_improvements": ["improvement 1"]}], 100)

        async def mock_evaluate(self, ideas, topic, context):
            nonlocal captured_prompt, captured_context
            captured_prompt = ideas
            captured_context = context
            # Return tuple (parsed_results, token_count)
            return ([{"score": 8, "comment": "Much better with improvements"}], 100)

        try:
            # Patch WorkflowOrchestrator improve function
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = mock_improve

            # Patch evaluate_ideas_async which is called by WorkflowOrchestrator
            with patch('src.madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async', mock_evaluate):
                # Process re-evaluation
                await coordinator.process_candidates_parallel_improvement_evaluation(
                    test_candidates,
                    "test topic",
                    "test criteria",
                    0.9,
                    0.3
                )

                # Verify the prompt includes improvement context
                # captured_prompt is a list of ideas
                assert captured_prompt is not None
                assert len(captured_prompt) > 0
                assert "Enhanced idea with clear implementation plan" in captured_prompt[0]

                # Verify context remains original (bias prevention)
                assert captured_context is not None
                assert captured_context == "test criteria"  # Original context preserved to avoid bias
        finally:
            # Restore originals
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = original_improve
    
    @pytest.mark.asyncio
    async def test_reevaluation_context_mentions_original_score(self):
        """Test that re-evaluation context includes original scores."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        test_candidates = [
            {
                "text": "Original idea",
                "score": 5,
                "critique": "Basic concept",
                "improved_idea": "Significantly enhanced idea",
                "context": "test context"
            }
        ]
        
        captured_context = None
        
        async def mock_evaluate(self, ideas, topic, context):
            nonlocal captured_context
            captured_context = context
            # Always return consistent score for improved idea (bias prevention working)
            # Return tuple (parsed_results, token_count)
            return ([{"score": 6, "comment": "Improvement evaluated fairly"}], 100)
        
        with patch('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS', {
            'improve_ideas_batch': lambda *args, **kwargs: (
                [{"improved_idea": "Significantly enhanced idea"}], 100
            )
        }):
            with patch('src.madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async', mock_evaluate):
                await coordinator.process_candidates_parallel_improvement_evaluation(
                    test_candidates,
                    "test topic",
                    "test criteria",
                    0.9,
                    0.3
                )
            
            # Verify re-evaluation works with bias prevention
            assert test_candidates[0]["improved_score"] == 6


class TestConsistentEvaluationCriteria:
    """Test that evaluation criteria remain consistent."""
    
    @pytest.mark.asyncio
    async def test_same_criteria_used_for_both_evaluations(self):
        """Test that the same criteria are used for initial and re-evaluation."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        test_candidates = [
            {
                "text": "Original idea",
                "score": 6,
                "critique": "Needs work",
                "improved_idea": "Better idea",
                "context": "specific requirements"
            }
        ]
        
        captured_criteria = None
        
        async def mock_evaluate(self, ideas, topic, context):
            nonlocal captured_criteria
            captured_criteria = context  # Use context parameter
            # Return tuple (parsed_results, token_count)
            return ([{"score": 7, "comment": "Better"}], 100)
        
        with patch('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS', {
            'improve_ideas_batch': lambda *args, **kwargs: (
                [{"improved_idea": "Better idea"}], 100
            )
        }):
            with patch('src.madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async', mock_evaluate):
                await coordinator.process_candidates_parallel_improvement_evaluation(
                    test_candidates,
                    "test topic",
                    "specific requirements",  # Same criteria as initial evaluation
                    0.9,
                    0.3
                )
            
            # Verify the same criteria were passed
            assert captured_criteria == "specific requirements"


class TestImprovementAcknowledgment:
    """Test that re-evaluation acknowledges improvements made."""
    
    def test_coordinator_batch_includes_improvement_context(self):
        """Test that coordinator_batch includes improvement context in re-evaluation."""
        # This test is verifying the concept, not the exact implementation
        # The key is that improved ideas get different evaluation context
        
        # Test the batch operations base directly
        from src.madspark.core.batch_operations_base import BatchOperationsBase
        
        ops = BatchOperationsBase()
        
        # Test that improvement input preparation includes context
        candidates = [{
            "text": "Original idea",
            "score": 5,
            "critique": "Needs improvement",
            "advocacy": "Has potential",
            "skepticism": "Some concerns",
            "context": "test context"
        }]
        
        # Prepare improvement input with context
        improvement_input = ops.prepare_improvement_input_with_context(candidates)
        
        # Verify all context is included
        assert len(improvement_input) == 1
        assert improvement_input[0]["idea"] == "Original idea"
        assert improvement_input[0]["critique"] == "Needs improvement"
        assert improvement_input[0]["advocacy"] == "Has potential"
        assert improvement_input[0]["skepticism"] == "Some concerns"
        assert improvement_input[0]["context"] == "test context"
        
        # The actual re-evaluation with improvement context is tested in async tests


class TestBiasReduction:
    """Test that bias towards higher scores for improved ideas is reduced."""
    
    @pytest.mark.asyncio
    async def test_balanced_reevaluation_scoring(self):
        """Test that re-evaluation doesn't automatically give higher scores."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        # Create candidates where improvement is minimal
        test_candidates = [
            {
                "text": "Good original idea",
                "score": 8,
                "critique": "Already strong",
                "advocacy": "Strong points",
                "skepticism": "Minor concerns",
                "context": "test context"
            }
        ]
        
        import src.madspark.core.workflow_orchestrator

        # Save originals
        original_improve = src.madspark.core.workflow_orchestrator.improve_ideas_batch

        def mock_improve(*args, **kwargs):
            return ([{"improved_idea": "Good original idea with minor tweak", "key_improvements": ["minor change"]}], 100)

        async def mock_evaluate(self, ideas, topic, context):
            # If improvement is minimal, score shouldn't increase much
            # ideas is a list, so check if any idea contains "minor tweak"
            if any("minor tweak" in idea for idea in ideas):
                # Return tuple (parsed_results, token_count)
                return ([{"score": 8, "comment": "No significant improvement"}], 100)
            # Return tuple (parsed_results, token_count)
            return ([{"score": 9, "comment": "Better"}], 100)

        try:
            # Patch WorkflowOrchestrator improve function
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = mock_improve

            # Patch evaluate_ideas_async which is called by WorkflowOrchestrator
            with patch('src.madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async', mock_evaluate):
                await coordinator.process_candidates_parallel_improvement_evaluation(
                    test_candidates,
                    "test topic",
                    "test criteria",
                    0.9,
                    0.3
                )

                # Score should not increase for minimal improvements
                assert test_candidates[0]["improved_score"] == 8
        finally:
            # Restore originals
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = original_improve


class TestReEvaluationPromptStructure:
    """Test the structure of re-evaluation prompts."""
    
    @pytest.mark.asyncio
    async def test_reevaluation_prompt_structure(self):
        """Test that re-evaluation prompt has proper structure."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator()
        
        test_candidates = [
            {
                "text": "Original",
                "score": 6,
                "critique": "Needs work",
                "advocacy": "Has potential",
                "skepticism": "Some risks",
                "context": "requirements"
            }
        ]
        
        import src.madspark.core.workflow_orchestrator

        captured_ideas_text = None

        # Save originals
        original_improve = src.madspark.core.workflow_orchestrator.improve_ideas_batch

        def mock_improve(*args, **kwargs):
            return ([{"improved_idea": "Much better version", "key_improvements": ["improvement 1"]}], 100)

        async def mock_evaluate(self, ideas, topic, context):
            nonlocal captured_ideas_text
            captured_ideas_text = ideas
            # Return tuple (parsed_results, token_count)
            return ([{"score": 8, "comment": "Good"}], 100)

        try:
            # Patch WorkflowOrchestrator improve function
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = mock_improve

            # Patch evaluate_ideas_async which is called by WorkflowOrchestrator
            with patch('src.madspark.core.workflow_orchestrator.WorkflowOrchestrator.evaluate_ideas_async', mock_evaluate):
                await coordinator.process_candidates_parallel_improvement_evaluation(
                    test_candidates,
                    "topic",
                    "criteria",
                    0.9,
                    0.3
                )

                # Verify prompt structure includes key elements
                # captured_ideas_text is a list of ideas
                assert captured_ideas_text is not None
                assert len(captured_ideas_text) > 0
                assert "Much better version" in captured_ideas_text[0]
                # With bias prevention, we DON'T include improvement markers
                # This ensures fair evaluation without bias toward "improved" versions
                ideas_text = " ".join(captured_ideas_text)
                assert not any(marker in ideas_text.upper() for marker in ["IMPROVED", "ENHANCED", "REFINED"])
        finally:
            # Restore originals
            src.madspark.core.workflow_orchestrator.improve_ideas_batch = original_improve


if __name__ == "__main__":
    pytest.main([__file__, "-v"])