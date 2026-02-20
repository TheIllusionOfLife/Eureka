"""Comprehensive tests for WorkflowOrchestrator.

This test suite validates the WorkflowOrchestrator class that centralizes
workflow logic from coordinator.py, coordinator_batch.py, and async_coordinator.py.
"""
import pytest
from unittest.mock import Mock, patch

# Test will fail until we implement the orchestrator
try:
    from madspark.core.workflow_orchestrator import WorkflowOrchestrator
    from madspark.config.workflow_constants import (
        FALLBACK_ADVOCACY,
        FALLBACK_SKEPTICISM,
        FALLBACK_CRITIQUE,
        FALLBACK_SCORE
    )
except ImportError:
    pytest.skip("WorkflowOrchestrator not yet implemented", allow_module_level=True)

from madspark.utils.temperature_control import TemperatureManager


class TestWorkflowOrchestratorInit:
    """Test WorkflowOrchestrator initialization and setup."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        orchestrator = WorkflowOrchestrator()

        assert orchestrator is not None
        assert orchestrator.temperature_manager is not None
        # Reasoning engine is created on-demand, not at init
        assert orchestrator.verbose is False

    def test_init_with_custom_temperature_manager(self):
        """Test initialization with custom TemperatureManager."""
        temp_manager = TemperatureManager.from_base_temperature(0.9)
        orchestrator = WorkflowOrchestrator(temperature_manager=temp_manager)

        assert orchestrator.temperature_manager is temp_manager

    def test_init_with_custom_reasoning_engine(self):
        """Test initialization with custom ReasoningEngine."""
        mock_reasoning_engine = Mock()
        orchestrator = WorkflowOrchestrator(reasoning_engine=mock_reasoning_engine)

        assert orchestrator.reasoning_engine is mock_reasoning_engine

    def test_init_with_verbose(self):
        """Test initialization with verbose logging enabled."""
        orchestrator = WorkflowOrchestrator(verbose=True)

        assert orchestrator.verbose is True


class TestWorkflowOrchestratorGenerateIdeas:
    """Test the generate_ideas workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry')
    def test_generate_ideas_success(self, mock_generator, orchestrator):
        """Test successful idea generation."""
        mock_generator.return_value = "Idea 1: First idea\nIdea 2: Second idea\nIdea 3: Third idea"

        ideas, token_count = orchestrator.generate_ideas(
            topic="AI automation",
            context="Cost-effective solutions",
            num_ideas=3
        )

        assert len(ideas) == 3
        assert "First idea" in ideas[0]
        assert "Second idea" in ideas[1]
        assert "Third idea" in ideas[2]
        assert isinstance(token_count, int)
        assert token_count > 0

        # Verify generator was called with correct parameters
        mock_generator.assert_called_once()
        call_args = mock_generator.call_args
        assert "AI automation" in str(call_args)
        assert "Cost-effective solutions" in str(call_args)

    @patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry')
    def test_generate_ideas_with_temperature(self, mock_generator, orchestrator):
        """Test idea generation uses temperature from manager."""
        mock_generator.return_value = "Idea 1: Test idea"

        ideas, token_count = orchestrator.generate_ideas(
            topic="Test topic",
            context="Test context",
            num_ideas=1
        )

        # Verify temperature was extracted from manager
        call_args = mock_generator.call_args
        assert 'temperature' in call_args[1] or len(call_args[0]) > 2

    @patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry')
    def test_generate_ideas_handles_errors(self, mock_generator, orchestrator):
        """Test idea generation handles errors gracefully."""
        mock_generator.side_effect = Exception("API error")

        with pytest.raises(Exception):
            orchestrator.generate_ideas(
                topic="Test topic",
                context="Test context",
                num_ideas=3
            )


class TestWorkflowOrchestratorEvaluateIdeas:
    """Test the evaluate_ideas workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_ideas(self):
        """Sample ideas for testing."""
        return [
            "Smart traffic management system",
            "AI-powered energy optimization",
            "Blockchain supply chain tracking"
        ]

    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    @patch('madspark.core.workflow_orchestrator.parse_json_with_fallback')
    def test_evaluate_ideas_success(self, mock_parse, mock_critic, orchestrator, sample_ideas):
        """Test successful idea evaluation."""
        mock_critic.return_value = ('[{"score": 8, "comment": "Good"}, {"score": 7, "comment": "OK"}, {"score": 9, "comment": "Great"}]', 100)
        mock_parse.return_value = [
            {"score": 8, "comment": "Good feasibility"},
            {"score": 7, "comment": "Needs work"},
            {"score": 9, "comment": "Excellent potential"}
        ]

        evaluated_ideas, token_count = orchestrator.evaluate_ideas(
            ideas=sample_ideas,
            topic="Urban innovation",
            context="Budget constraints"
        )

        assert len(evaluated_ideas) == 3
        assert all(isinstance(idea, dict) for idea in evaluated_ideas)
        assert all("text" in idea for idea in evaluated_ideas)
        assert all("score" in idea for idea in evaluated_ideas)
        assert all("critique" in idea for idea in evaluated_ideas)

        # Check scores
        assert evaluated_ideas[0]["score"] == 8
        assert evaluated_ideas[1]["score"] == 7
        assert evaluated_ideas[2]["score"] == 9

        # Verify critic was called
        mock_critic.assert_called_once()

    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    def test_evaluate_ideas_with_fallback(self, mock_critic, orchestrator, sample_ideas):
        """Test evaluation with fallback on error."""
        mock_critic.side_effect = Exception("Evaluation failed")

        evaluated_ideas, token_count = orchestrator.evaluate_ideas(
            ideas=sample_ideas,
            topic="Test topic",
            context="Test context"
        )

        # Should return ideas with fallback values
        assert len(evaluated_ideas) == 3
        for idea in evaluated_ideas:
            assert idea["score"] == FALLBACK_SCORE
            assert FALLBACK_CRITIQUE in idea["critique"] or "failed" in idea["critique"].lower()


class TestWorkflowOrchestratorProcessAdvocacy:
    """Test the process_advocacy workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_candidates(self):
        """Sample candidates for testing."""
        return [
            {
                "idea": "Smart traffic system",
                "initial_score": 8.0,
                "initial_critique": "Good feasibility",
                "multi_dimensional_evaluation": None
            },
            {
                "idea": "AI energy optimization",
                "initial_score": 7.0,
                "initial_critique": "Needs refinement",
                "multi_dimensional_evaluation": None
            }
        ]

    @patch('madspark.core.workflow_orchestrator.advocate_ideas_batch')
    def test_process_advocacy_success(self, mock_advocate, orchestrator, sample_candidates):
        """Test successful advocacy processing."""
        mock_advocate.return_value = ([
            {
                "idea_index": 0,
                "strengths": ["Innovative", "Scalable"],
                "opportunities": ["Market demand"],
                "addressing_concerns": ["Phased rollout"],
                "formatted": "STRENGTHS:\n• Innovative\n• Scalable"
            },
            {
                "idea_index": 1,
                "strengths": ["Cost-effective"],
                "opportunities": ["Energy savings"],
                "addressing_concerns": ["Pilot program"],
                "formatted": "STRENGTHS:\n• Cost-effective"
            }
        ], 1200)

        updated_candidates, token_count = orchestrator.process_advocacy(
            candidates=sample_candidates,
            topic="Urban innovation",
            context="Budget-friendly"
        )

        assert len(updated_candidates) == 2
        assert "advocacy" in updated_candidates[0]
        assert "advocacy" in updated_candidates[1]
        assert "Innovative" in updated_candidates[0]["advocacy"]
        assert "Cost-effective" in updated_candidates[1]["advocacy"]
        assert token_count == 1200

        # Verify batch function was called
        mock_advocate.assert_called_once()

    @patch('madspark.core.workflow_orchestrator.advocate_ideas_batch')
    def test_process_advocacy_with_fallback(self, mock_advocate, orchestrator, sample_candidates):
        """Test advocacy processing with error fallback."""
        mock_advocate.side_effect = Exception("Advocacy failed")

        updated_candidates, token_count = orchestrator.process_advocacy(
            candidates=sample_candidates,
            topic="Test topic",
            context="Test context"
        )

        # Should have fallback advocacy values
        assert len(updated_candidates) == 2
        for candidate in updated_candidates:
            assert "advocacy" in candidate
            assert FALLBACK_ADVOCACY in candidate["advocacy"] or "failed" in candidate["advocacy"].lower()


class TestWorkflowOrchestratorProcessSkepticism:
    """Test the process_skepticism workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_candidates(self):
        """Sample candidates for testing."""
        return [
            {
                "idea": "Smart traffic system",
                "initial_score": 8.0,
                "initial_critique": "Good feasibility",
                "advocacy": "Strong market demand",
                "multi_dimensional_evaluation": None
            }
        ]

    @patch('madspark.core.workflow_orchestrator.criticize_ideas_batch')
    def test_process_skepticism_success(self, mock_skeptic, orchestrator, sample_candidates):
        """Test successful skepticism processing."""
        mock_skeptic.return_value = ([
            {
                "idea_index": 0,
                "critical_flaws": ["High cost"],
                "risks_challenges": ["Maintenance"],
                "questionable_assumptions": ["Full adoption"],
                "missing_considerations": ["Privacy"],
                "formatted": "CRITICAL FLAWS:\n• High cost"
            }
        ], 1000)

        updated_candidates, token_count = orchestrator.process_skepticism(
            candidates=sample_candidates,
            topic="Urban innovation",
            context="Budget-friendly"
        )

        assert len(updated_candidates) == 1
        assert "skepticism" in updated_candidates[0]
        assert "High cost" in updated_candidates[0]["skepticism"]
        assert token_count == 1000

    @patch('madspark.core.workflow_orchestrator.criticize_ideas_batch')
    def test_process_skepticism_with_fallback(self, mock_skeptic, orchestrator, sample_candidates):
        """Test skepticism processing with error fallback."""
        mock_skeptic.side_effect = Exception("Skepticism failed")

        updated_candidates, token_count = orchestrator.process_skepticism(
            candidates=sample_candidates,
            topic="Test topic",
            context="Test context"
        )

        assert len(updated_candidates) == 1
        assert "skepticism" in updated_candidates[0]
        assert FALLBACK_SKEPTICISM in updated_candidates[0]["skepticism"] or "failed" in updated_candidates[0]["skepticism"].lower()


class TestWorkflowOrchestratorImproveIdeas:
    """Test the improve_ideas workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_candidates(self):
        """Sample candidates with advocacy and skepticism."""
        return [
            {
                "idea": "Smart traffic system",
                "initial_score": 8.0,
                "initial_critique": "Good feasibility",
                "advocacy": "Strong market demand and scalability",
                "skepticism": "High implementation costs and privacy concerns",
                "multi_dimensional_evaluation": None
            }
        ]

    @patch('madspark.core.workflow_orchestrator.improve_ideas_batch')
    def test_improve_ideas_success(self, mock_improve, orchestrator, sample_candidates):
        """Test successful idea improvement."""
        mock_improve.return_value = ([
            {
                "idea_index": 0,
                "improved_idea": "Smart traffic system with phased rollout and privacy-first design",
                "key_improvements": ["Phased rollout", "Privacy safeguards"]
            }
        ], 1500)

        updated_candidates, token_count = orchestrator.improve_ideas(
            candidates=sample_candidates,
            topic="Urban innovation",
            context="Budget-friendly"
        )

        assert len(updated_candidates) == 1
        assert "improved_idea" in updated_candidates[0]
        assert "phased rollout" in updated_candidates[0]["improved_idea"].lower()
        assert "privacy" in updated_candidates[0]["improved_idea"].lower()
        assert token_count == 1500

    @patch('madspark.core.workflow_orchestrator.improve_ideas_batch')
    def test_improve_ideas_uses_original_on_failure(self, mock_improve, orchestrator, sample_candidates):
        """Test improvement falls back to original idea on failure."""
        mock_improve.side_effect = Exception("Improvement failed")

        updated_candidates, token_count = orchestrator.improve_ideas(
            candidates=sample_candidates,
            topic="Test topic",
            context="Test context"
        )

        # Should fallback to original idea
        assert len(updated_candidates) == 1
        assert "improved_idea" in updated_candidates[0]
        assert updated_candidates[0]["improved_idea"] == sample_candidates[0]["idea"]


class TestWorkflowOrchestratorReevaluateIdeas:
    """Test the reevaluate_ideas workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_candidates(self):
        """Sample candidates with improved ideas."""
        return [
            {
                "idea": "Smart traffic system",
                "initial_score": 8.0,
                "initial_critique": "Good feasibility",
                "improved_idea": "Smart traffic system with privacy-first design",
                "context": "Budget-friendly"  # Original context for re-evaluation
            }
        ]

    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    @patch('madspark.core.workflow_orchestrator.parse_json_with_fallback')
    def test_reevaluate_ideas_success(self, mock_parse, mock_critic, orchestrator, sample_candidates):
        """Test successful re-evaluation."""
        mock_critic.return_value = ('[{"score": 9, "comment": "Much improved"}]', 100)
        mock_parse.return_value = [
            {"score": 9, "comment": "Excellent improvements address concerns"}
        ]

        updated_candidates, token_count = orchestrator.reevaluate_ideas(
            candidates=sample_candidates,
            topic="Urban innovation",
            context="Budget-friendly"  # Original context
        )

        assert len(updated_candidates) == 1
        assert "improved_score" in updated_candidates[0]
        assert "improved_critique" in updated_candidates[0]
        assert updated_candidates[0]["improved_score"] == 9.0
        # Check that critique contains meaningful content (not fallback)
        assert len(updated_candidates[0]["improved_critique"]) > 10
        assert "excellent" in updated_candidates[0]["improved_critique"].lower() or "improvement" in updated_candidates[0]["improved_critique"].lower()

    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    def test_reevaluate_uses_original_context(self, mock_critic, orchestrator, sample_candidates):
        """Test re-evaluation uses original context to avoid bias."""
        mock_critic.return_value = ('[{"score": 8, "comment": "Good"}]', 100)

        # Call with different context than stored in candidate
        updated_candidates, token_count = orchestrator.reevaluate_ideas(
            candidates=sample_candidates,
            topic="Urban innovation",
            context="Different context"
        )

        # Should use context parameter (original), not from candidate
        call_args = mock_critic.call_args
        assert "Different context" in str(call_args) or "Budget-friendly" not in str(call_args)

    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    def test_reevaluate_ideas_with_fallback(self, mock_critic, orchestrator, sample_candidates):
        """Test re-evaluation with error fallback."""
        mock_critic.side_effect = Exception("Re-evaluation failed")

        updated_candidates, token_count = orchestrator.reevaluate_ideas(
            candidates=sample_candidates,
            topic="Test topic",
            context="Test context"
        )

        # Should use original scores on failure
        assert len(updated_candidates) == 1
        assert "improved_score" in updated_candidates[0]
        assert updated_candidates[0]["improved_score"] == sample_candidates[0]["initial_score"]


class TestWorkflowOrchestratorBuildFinalResults:
    """Test the build_final_results workflow step."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(verbose=False)

    @pytest.fixture
    def sample_candidates(self):
        """Sample candidates ready for final results."""
        return [
            {
                "idea": "Smart traffic system",
                "initial_score": 8.0,
                "initial_critique": "Good feasibility",
                "advocacy": "Strong market demand",
                "skepticism": "High costs",
                "improved_idea": "Smart traffic system with phased rollout",
                "improved_score": 9.0,
                "improved_critique": "Excellent improvements",
                "multi_dimensional_evaluation": None
            }
        ]

    @patch('madspark.core.workflow_orchestrator.is_meaningful_improvement')
    def test_build_final_results_with_improvement(self, mock_improvement, orchestrator, sample_candidates):
        """Test building final results with meaningful improvement."""
        mock_improvement.return_value = (True, 0.75)

        final_results = orchestrator.build_final_results(sample_candidates)

        assert len(final_results) == 1
        result = final_results[0]

        # Check all required fields
        assert "idea" in result
        assert "initial_score" in result
        assert "initial_critique" in result
        assert "advocacy" in result
        assert "skepticism" in result
        assert "improved_idea" in result
        assert "improved_score" in result
        assert "improved_critique" in result
        assert "score_delta" in result
        assert "is_meaningful_improvement" in result
        assert "similarity_score" in result

        # Check calculated fields
        assert result["score_delta"] == 1.0  # 9.0 - 8.0
        assert result["is_meaningful_improvement"] is True
        assert result["similarity_score"] == 0.75

    @patch('madspark.core.workflow_orchestrator.is_meaningful_improvement')
    def test_build_final_results_no_improvement(self, mock_improvement, orchestrator, sample_candidates):
        """Test building final results with no meaningful improvement."""
        mock_improvement.return_value = (False, 0.95)

        final_results = orchestrator.build_final_results(sample_candidates)

        assert len(final_results) == 1
        result = final_results[0]
        assert result["is_meaningful_improvement"] is False
        assert result["similarity_score"] == 0.95


class TestWorkflowOrchestratorIntegration:
    """Integration tests for complete workflow execution."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing."""
        temp_manager = TemperatureManager.from_base_temperature(0.8)
        return WorkflowOrchestrator(
            temperature_manager=temp_manager,
            verbose=False
        )

    @patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry')
    @patch('madspark.core.workflow_orchestrator.call_critic_with_retry')
    @patch('madspark.core.workflow_orchestrator.advocate_ideas_batch')
    @patch('madspark.core.workflow_orchestrator.criticize_ideas_batch')
    @patch('madspark.core.workflow_orchestrator.improve_ideas_batch')
    @patch('madspark.core.workflow_orchestrator.is_meaningful_improvement')
    def test_full_workflow_execution(self, mock_improvement, mock_improve, mock_skeptic,
                                    mock_advocate, mock_critic, mock_generator, orchestrator):
        """Test complete workflow execution through all steps."""
        # Mock all workflow steps
        mock_generator.return_value = "Idea 1: Smart traffic\nIdea 2: AI energy"
        mock_critic.return_value = ('[{"score": 8, "comment": "Good"}, {"score": 7, "comment": "OK"}]', 100)

        mock_advocate.return_value = ([
            {"idea_index": 0, "formatted": "Strong advocacy"},
            {"idea_index": 1, "formatted": "Moderate advocacy"}
        ], 1000)

        mock_skeptic.return_value = ([
            {"idea_index": 0, "formatted": "Some concerns"},
            {"idea_index": 1, "formatted": "Major concerns"}
        ], 800)

        mock_improve.return_value = ([
            {"idea_index": 0, "improved_idea": "Enhanced smart traffic"},
            {"idea_index": 1, "improved_idea": "Enhanced AI energy"}
        ], 1200)

        mock_improvement.return_value = (True, 0.75)

        # Execute complete workflow
        ideas, _ = orchestrator.generate_ideas("AI innovation", "Cost-effective", 2)
        evaluated, _ = orchestrator.evaluate_ideas(ideas, "AI innovation", "Cost-effective")

        candidates = [
            {
                "idea": idea["text"],
                "initial_score": float(idea["score"]),
                "initial_critique": idea["critique"],
                "multi_dimensional_evaluation": None
            }
            for idea in evaluated
        ]

        candidates, _ = orchestrator.process_advocacy(candidates, "AI innovation", "Cost-effective")
        candidates, _ = orchestrator.process_skepticism(candidates, "AI innovation", "Cost-effective")
        candidates, _ = orchestrator.improve_ideas(candidates, "AI innovation", "Cost-effective")
        candidates, _ = orchestrator.reevaluate_ideas(candidates, "AI innovation", "Cost-effective")
        final_results = orchestrator.build_final_results(candidates)

        # Verify complete results
        assert len(final_results) == 2
        for result in final_results:
            assert all(key in result for key in [
                "idea", "initial_score", "initial_critique",
                "advocacy", "skepticism",
                "improved_idea", "improved_score", "improved_critique",
                "score_delta", "is_meaningful_improvement", "similarity_score"
            ])

        # Verify all mocks were called
        mock_generator.assert_called_once()
        assert mock_critic.call_count == 2  # Initial eval + re-eval
        mock_advocate.assert_called_once()
        mock_skeptic.assert_called_once()
        mock_improve.assert_called_once()
