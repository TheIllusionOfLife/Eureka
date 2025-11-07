"""Tests for information flow between agents.

This test suite ensures that:
1. Advocate receives context along with idea and evaluation
2. Skeptic receives context along with idea and advocacy
3. Improvement phase gets all information (original context, critiques, advocacy, skepticism)
4. Logical inference is included when available
"""

import json
import pytest
from unittest.mock import Mock, patch

# Test data
TEST_TOPIC = "renewable energy solutions"
TEST_CONTEXT = "affordable for developing countries"
TEST_IDEA = "Solar panel sharing program"
TEST_EVALUATION = "Good feasibility but needs cost analysis"
TEST_ADVOCACY = "Strong community impact"
TEST_SKEPTICISM = "Maintenance concerns"
TEST_LOGICAL_INFERENCE = {
    "implications": ["Reduced energy costs", "Community building"]
}


class TestAdvocateInformationFlow:
    """Test that advocate receives proper context."""

    def test_advocate_batch_receives_context(self):
        """Test that advocate batch function includes context."""
        from src.madspark.agents.advocate import advocate_ideas_batch

        ideas_with_evaluations = [{"idea": TEST_IDEA, "evaluation": TEST_EVALUATION}]

        with patch("src.madspark.agents.advocate.advocate_client") as mock_client:
            mock_response = Mock()
            mock_response.text = json.dumps(
                [
                    {
                        "idea_index": 0,
                        "advocacy": "Strong points",
                        "key_strengths": ["Community", "Sustainability"],
                        "strengths": "Community engagement and environmental impact",
                        "opportunities": "Scalability and government support",
                        "addressing_concerns": "Maintenance through community training",
                    }
                ]
            )
            mock_client.models.generate_content.return_value = mock_response

            results, _ = advocate_ideas_batch(
                ideas_with_evaluations,
                topic=TEST_TOPIC,
                context=TEST_CONTEXT,
                temperature=0.5,
            )

            # Verify the prompt includes context
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args[1]["contents"]
            assert TEST_CONTEXT in prompt
            assert TEST_IDEA in prompt
            assert TEST_EVALUATION in prompt

    def test_batch_operations_prepare_advocacy_with_context(self):
        """Test that batch operations prepare advocacy input with context."""
        from src.madspark.core.batch_operations_base import BatchOperationsBase

        ops = BatchOperationsBase()
        candidates = [
            {"text": TEST_IDEA, "critique": TEST_EVALUATION, "context": TEST_CONTEXT}
        ]

        # Test new method that includes context
        result = ops.prepare_advocacy_input_with_context(candidates)

        assert len(result) == 1
        assert result[0]["idea"] == TEST_IDEA
        assert result[0]["evaluation"] == TEST_EVALUATION
        assert result[0]["context"] == TEST_CONTEXT


class TestSkepticInformationFlow:
    """Test that skeptic receives proper context."""

    def test_skeptic_batch_receives_context(self):
        """Test that skeptic batch function includes context."""
        from src.madspark.agents.skeptic import criticize_ideas_batch

        ideas_with_advocacy = [{"idea": TEST_IDEA, "advocacy": TEST_ADVOCACY}]

        with patch("src.madspark.agents.skeptic.skeptic_client") as mock_client:
            mock_response = Mock()
            mock_response.text = json.dumps(
                [
                    {
                        "idea_index": 0,
                        "skepticism": "Some concerns",
                        "concerns": ["Maintenance", "Scalability"],
                        "critical_flaws": "Limited initial funding sources",
                        "missing_considerations": "Weather impact on solar efficiency",
                        "risks_challenges": "Community adoption rates",
                        "questionable_assumptions": "Assuming stable maintenance costs",
                    }
                ]
            )
            mock_client.models.generate_content.return_value = mock_response

            results, _ = criticize_ideas_batch(
                ideas_with_advocacy,
                topic=TEST_TOPIC,
                context=TEST_CONTEXT,
                temperature=0.5,
            )

            # Verify the prompt includes context
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args[1]["contents"]
            assert TEST_CONTEXT in prompt
            assert TEST_IDEA in prompt
            assert TEST_ADVOCACY in prompt


class TestImprovementInformationFlow:
    """Test that improvement phase receives all information."""

    def test_improvement_batch_receives_all_context(self):
        """Test that improvement batch includes all feedback and context."""
        from src.madspark.agents.idea_generator import improve_ideas_batch

        ideas_with_feedback = [
            {
                "idea": TEST_IDEA,
                "critique": TEST_EVALUATION,
                "advocacy": TEST_ADVOCACY,
                "skepticism": TEST_SKEPTICISM,
            }
        ]

        with patch(
            "src.madspark.agents.idea_generator.idea_generator_client"
        ) as mock_client:
            mock_response = Mock()
            mock_response.text = json.dumps(
                [
                    {
                        "idea_index": 0,
                        "improved_idea": "Enhanced solar panel program",
                        "key_improvements": [
                            "Added maintenance plan",
                            "Cost sharing model",
                        ],
                    }
                ]
            )
            mock_response.usage_metadata = Mock(total_token_count=100)
            mock_client.models.generate_content.return_value = mock_response

            results, tokens = improve_ideas_batch(
                ideas_with_feedback, TEST_TOPIC, TEST_CONTEXT, temperature=0.9
            )

            # Verify the prompt includes all information
            call_args = mock_client.models.generate_content.call_args
            prompt = call_args[1]["contents"]
            assert TEST_CONTEXT in prompt
            assert TEST_IDEA in prompt
            assert TEST_EVALUATION in prompt
            assert TEST_ADVOCACY in prompt
            assert TEST_SKEPTICISM in prompt

    def test_batch_operations_prepare_improvement_with_context(self):
        """Test that batch operations prepare improvement input with all context."""
        from src.madspark.core.batch_operations_base import BatchOperationsBase

        ops = BatchOperationsBase()
        candidates = [
            {
                "text": TEST_IDEA,
                "critique": TEST_EVALUATION,
                "advocacy": TEST_ADVOCACY,
                "skepticism": TEST_SKEPTICISM,
                "context": TEST_CONTEXT,
                "logical_inference": TEST_LOGICAL_INFERENCE,
            }
        ]

        # Test new method that includes all context
        result = ops.prepare_improvement_input_with_context(candidates)

        assert len(result) == 1
        assert result[0]["idea"] == TEST_IDEA
        assert result[0]["critique"] == TEST_EVALUATION
        assert result[0]["advocacy"] == TEST_ADVOCACY
        assert result[0]["skepticism"] == TEST_SKEPTICISM
        assert result[0]["context"] == TEST_CONTEXT
        assert result[0]["logical_inference"] == TEST_LOGICAL_INFERENCE


class TestCoordinatorInformationFlow:
    """Test that coordinators pass information correctly between agents."""

    @pytest.mark.asyncio
    async def test_async_coordinator_passes_context_to_improvement(self):
        """Test that async coordinator passes context to improvement via orchestrator (Phase 3.2c)."""
        from src.madspark.core.async_coordinator import AsyncCoordinator
        from unittest.mock import AsyncMock

        coordinator = AsyncCoordinator()

        # Phase 3.2c: Mock orchestrator method to verify context passing
        context_received = None

        def mock_improvement_side_effect(_self, candidates, topic, context):
            nonlocal context_received
            context_received = context
            for candidate in candidates:
                candidate["improved_idea"] = (
                    "Enhanced idea with clear implementation plan"
                )
            return (candidates, 50)

        # Phase 3.2c: Patch orchestrator method instead of BATCH_FUNCTIONS
        with patch(
            "madspark.core.workflow_orchestrator.WorkflowOrchestrator.improve_ideas_async",
            new=AsyncMock(side_effect=mock_improvement_side_effect),
        ):
            # Create test candidates
            test_candidates = [
                {
                    "text": TEST_IDEA,
                    "critique": TEST_EVALUATION,
                    "advocacy": TEST_ADVOCACY,
                    "skepticism": TEST_SKEPTICISM,
                }
            ]

            # Call the improvement method directly
            await coordinator._process_candidates_with_batch_improvement(
                test_candidates,
                TEST_TOPIC,  # Topic parameter
                TEST_CONTEXT,  # Context parameter
                0.9,  # Temperature
            )

            # Verify context was passed to orchestrator
            assert context_received == TEST_CONTEXT


class TestIntegrationWithLogicalInference:
    """Test that logical inference is included in improvement when available."""

    def test_logical_inference_prepared_for_improvement(self):
        """Test that logical inference is included in improvement input."""
        from src.madspark.core.batch_operations_base import BatchOperationsBase

        ops = BatchOperationsBase()

        # Create candidates with logical inference
        candidates = [
            {
                "text": TEST_IDEA,
                "critique": TEST_EVALUATION,
                "advocacy": TEST_ADVOCACY,
                "skepticism": TEST_SKEPTICISM,
                "context": TEST_CONTEXT,
                "logical_inference": TEST_LOGICAL_INFERENCE,
            }
        ]

        # Prepare improvement input
        improve_input = ops.prepare_improvement_input_with_context(candidates)

        # Verify logical inference is included
        assert len(improve_input) == 1
        assert improve_input[0]["logical_inference"] == TEST_LOGICAL_INFERENCE
        assert improve_input[0]["context"] == TEST_CONTEXT
