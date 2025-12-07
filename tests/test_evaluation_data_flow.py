"""Tests for Issue #219: Feed evaluations into improvement step.

TDD tests for the data flow enhancements that pass:
- initial_score
- dimension_scores (multi-dimensional evaluation)
- logical_inference

to the improvement step for better-informed improvements.
"""
from unittest.mock import Mock, patch


class TestFormatLogicalInferenceForPrompt:
    """Test the helper method for formatting logical inference data."""

    def test_format_logical_inference_none_input(self):
        """Should return None when logical_inference is None."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        result = orchestrator._format_logical_inference_for_prompt(None)

        assert result is None

    def test_format_logical_inference_empty_dict(self):
        """Should return None when logical_inference is empty dict."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        result = orchestrator._format_logical_inference_for_prompt({})

        assert result is None

    def test_format_logical_inference_with_confidence(self):
        """Should format confidence as percentage."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        logical_inference = {"confidence": 0.85}

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        assert "Confidence: 85%" in result

    def test_format_logical_inference_with_conclusion(self):
        """Should include conclusion text."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        logical_inference = {"conclusion": "This idea is feasible."}

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        assert "Conclusion: This idea is feasible." in result

    def test_format_logical_inference_with_chain(self):
        """Should format inference chain as arrows."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        logical_inference = {
            "inference_chain": ["Premise A", "Implies B", "Therefore C"]
        }

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        assert "Logical Steps:" in result
        assert "Premise A -> Implies B -> Therefore C" in result

    def test_format_logical_inference_chain_limited_to_5(self):
        """Should limit inference chain to 5 steps max."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        logical_inference = {
            "inference_chain": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6", "Step 7"]
        }

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        # Should only include first 5 steps
        assert "Step 5" in result
        assert "Step 6" not in result
        assert "Step 7" not in result

    def test_format_logical_inference_with_improvements(self):
        """Should include improvements section if present."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        # improvements should be a string per InferenceResult schema
        logical_inference = {
            "improvements": "Add more detail to the implementation plan"
        }

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        assert "Suggested Improvements:" in result

    def test_format_logical_inference_full_data(self):
        """Should format complete logical inference data."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)
        logical_inference = {
            "confidence": 0.92,
            "conclusion": "The approach is sound.",
            "inference_chain": ["Given premise", "We can infer", "Therefore"],
            "improvements": {"optimize": "resource usage"}
        }

        result = orchestrator._format_logical_inference_for_prompt(logical_inference)

        assert result is not None
        assert "Confidence: 92%" in result
        assert "Conclusion: The approach is sound." in result
        assert "Logical Steps:" in result
        assert "Suggested Improvements:" in result


class TestImproveInputDataFlow:
    """Test that improve_input includes all evaluation data."""

    def test_improve_input_includes_initial_score(self):
        """Verify initial_score is passed to improve_input."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{
            "idea": "Test idea",
            "text": "Test idea",
            "initial_critique": "Good critique",
            "initial_score": 7.5,
            "advocacy": "Strong points",
            "skepticism": "Some concerns"
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Better idea"}], 100)

            orchestrator.improve_ideas(
                candidates=candidates,
                topic="Test",
                context="Test context"
            )

            # Verify improve_ideas_batch was called with initial_score
            call_args = mock_improve.call_args[0][0]  # First positional arg
            assert call_args[0].get("initial_score") == 7.5

    def test_improve_input_includes_dimension_scores(self):
        """Verify dimension_scores are passed when multi_dimensional_evaluation exists."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)

        dimension_scores = {
            "feasibility": 8.0,
            "innovation": 7.0,
            "impact": 9.0,
            "cost_effectiveness": 6.5,
            "scalability": 7.5
        }

        candidates = [{
            "idea": "Test idea",
            "text": "Test idea",
            "initial_critique": "Good critique",
            "advocacy": "Strong points",
            "skepticism": "Some concerns",
            "multi_dimensional_evaluation": {
                "dimension_scores": dimension_scores,
                "overall_score": 7.6
            }
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Better idea"}], 100)

            orchestrator.improve_ideas(
                candidates=candidates,
                topic="Test",
                context="Test context"
            )

            # Verify improve_ideas_batch was called with dimension_scores
            call_args = mock_improve.call_args[0][0]
            assert call_args[0].get("dimension_scores") == dimension_scores

    def test_improve_input_includes_logical_inference(self):
        """Verify logical_inference is formatted and passed."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{
            "idea": "Test idea",
            "text": "Test idea",
            "initial_critique": "Good critique",
            "advocacy": "Strong points",
            "skepticism": "Some concerns",
            "logical_inference": {
                "confidence": 0.88,
                "conclusion": "Sound approach",
                "inference_chain": ["Step 1", "Step 2"]
            }
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Better idea"}], 100)

            orchestrator.improve_ideas(
                candidates=candidates,
                topic="Test",
                context="Test context"
            )

            # Verify improve_ideas_batch was called with formatted logical_inference
            call_args = mock_improve.call_args[0][0]
            logical = call_args[0].get("logical_inference")
            assert logical is not None
            assert "Confidence: 88%" in logical
            assert "Sound approach" in logical

    def test_improve_input_handles_missing_optional_fields(self):
        """Verify graceful handling when optional fields are missing."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)

        # Minimal candidate - only required fields
        candidates = [{
            "idea": "Test idea",
            "text": "Test idea",
            "critique": "Basic critique",
            "advocacy": "N/A",
            "skepticism": "N/A"
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Better idea"}], 100)

            # Should not raise exception
            orchestrator.improve_ideas(
                candidates=candidates,
                topic="Test",
                context="Test context"
            )

            # Verify call was made with None for missing fields
            call_args = mock_improve.call_args[0][0]
            assert call_args[0].get("initial_score") is None
            assert call_args[0].get("dimension_scores") is None
            assert call_args[0].get("logical_inference") is None


class TestBuildImprovementPromptEnhancements:
    """Test prompt building with new score parameters."""

    def test_prompt_includes_initial_score(self):
        """Verify initial score is included in prompt."""
        from madspark.agents.prompts import build_improvement_prompt

        prompt = build_improvement_prompt(
            original_idea="Test idea",
            critique="Good but needs work",
            advocacy_points="Strong innovation",
            skeptic_points="Cost concerns",
            topic="Technology",
            context="Business context",
            initial_score=7.5
        )

        assert "INITIAL SCORE: 7.5/10" in prompt

    def test_prompt_includes_dimension_scores(self):
        """Verify dimension scores are included in prompt."""
        from madspark.agents.prompts import build_improvement_prompt

        dimension_scores = {
            "feasibility": 8.0,
            "innovation": 6.0,  # Low - should be marked PRIORITY
            "impact": 9.0,
            "cost_effectiveness": 5.5,  # Low - should be marked PRIORITY
            "scalability": 7.0
        }

        prompt = build_improvement_prompt(
            original_idea="Test idea",
            critique="Needs improvement",
            advocacy_points="Good potential",
            skeptic_points="Implementation risks",
            topic="Technology",
            context="Startup context",
            initial_score=7.0,
            dimension_scores=dimension_scores
        )

        assert "DIMENSION SCORES:" in prompt
        assert "Feasibility: 8.0/10" in prompt
        assert "Innovation: 6.0/10" in prompt
        # Low scoring dimensions should be marked as priority
        assert "[PRIORITY]" in prompt

    def test_prompt_without_scores_still_works(self):
        """Verify prompt works without optional score params."""
        from madspark.agents.prompts import build_improvement_prompt

        # Original signature without new params
        prompt = build_improvement_prompt(
            original_idea="Test idea",
            critique="Good but needs work",
            advocacy_points="Strong innovation",
            skeptic_points="Cost concerns",
            topic="Technology",
            context="Business context"
        )

        # Should still have core sections
        assert "ORIGINAL IDEA:" in prompt
        assert "EVALUATION CRITERIA AND FEEDBACK:" in prompt
        assert "STRENGTHS TO PRESERVE" in prompt
        assert "CONCERNS TO ADDRESS" in prompt
        # Should not have score sections
        assert "INITIAL SCORE:" not in prompt
        assert "DIMENSION SCORES:" not in prompt

    def test_prompt_with_logical_and_scores(self):
        """Verify prompt integrates all evaluation data."""
        from madspark.agents.prompts import build_improvement_prompt

        prompt = build_improvement_prompt(
            original_idea="AI tutoring system",
            critique="Innovative but complex",
            advocacy_points="Strong market potential",
            skeptic_points="Technical complexity",
            topic="EdTech",
            context="Online learning",
            logical_inference="The approach is logically sound.",
            initial_score=7.5,
            dimension_scores={"feasibility": 6.0, "innovation": 9.0}
        )

        # All sections present
        assert "INITIAL SCORE: 7.5/10" in prompt
        assert "DIMENSION SCORES:" in prompt
        assert "LOGICAL INFERENCE ANALYSIS:" in prompt
        assert "ORIGINAL IDEA:" in prompt


class TestImproveBatchWithNewFields:
    """Test improve_ideas_batch handles new evaluation fields."""

    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_batch_prompt_includes_initial_score(self, mock_model_name, mock_client):
        """Verify batch prompt includes initial_score when provided."""
        from madspark.agents.idea_generator import improve_ideas_batch

        mock_model_name.return_value = "gemini-2.5-flash"
        mock_response = Mock()
        mock_response.text = '[{"idea_index": 0, "improved_idea": "Better idea", "key_improvements": []}]'
        mock_client.models.generate_content.return_value = mock_response

        ideas_with_feedback = [{
            "idea": "Test idea",
            "critique": "Needs work",
            "advocacy": "Good potential",
            "skepticism": "Some risks",
            "initial_score": 7.5
        }]

        improve_ideas_batch(ideas_with_feedback, "Test", "Test context", 0.9)

        # Verify the prompt contains the score
        call_args = mock_client.models.generate_content.call_args
        prompt_content = str(call_args)
        assert "7.5/10" in prompt_content or "INITIAL SCORE" in prompt_content

    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_batch_prompt_includes_dimension_scores(self, mock_model_name, mock_client):
        """Verify batch prompt includes dimension_scores when provided."""
        from madspark.agents.idea_generator import improve_ideas_batch

        mock_model_name.return_value = "gemini-2.5-flash"
        mock_response = Mock()
        mock_response.text = '[{"idea_index": 0, "improved_idea": "Better idea", "key_improvements": []}]'
        mock_client.models.generate_content.return_value = mock_response

        ideas_with_feedback = [{
            "idea": "Test idea",
            "critique": "Needs work",
            "advocacy": "Good potential",
            "skepticism": "Some risks",
            "initial_score": 7.0,  # Required for dimension_scores to be displayed
            "dimension_scores": {
                "feasibility": 8.0,
                "innovation": 6.0
            }
        }]

        improve_ideas_batch(ideas_with_feedback, "Test", "Test context", 0.9)

        # Verify the prompt contains dimension scores
        call_args = mock_client.models.generate_content.call_args
        prompt_content = str(call_args)
        assert "Feasibility" in prompt_content or "DIMENSION SCORES" in prompt_content

    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.get_model_name')
    def test_batch_prompt_includes_logical_inference(self, mock_model_name, mock_client):
        """Verify batch prompt includes logical_inference when provided."""
        from madspark.agents.idea_generator import improve_ideas_batch

        mock_model_name.return_value = "gemini-2.5-flash"
        mock_response = Mock()
        mock_response.text = '[{"idea_index": 0, "improved_idea": "Better idea", "key_improvements": []}]'
        mock_client.models.generate_content.return_value = mock_response

        ideas_with_feedback = [{
            "idea": "Test idea",
            "critique": "Needs work",
            "advocacy": "Good potential",
            "skepticism": "Some risks",
            "logical_inference": "The approach is logically sound with high confidence."
        }]

        improve_ideas_batch(ideas_with_feedback, "Test", "Test context", 0.9)

        # Verify the prompt contains logical inference
        call_args = mock_client.models.generate_content.call_args
        prompt_content = str(call_args)
        assert "LOGICAL INFERENCE" in prompt_content or "logically sound" in prompt_content


class TestSummaryFormatterNoNA:
    """Test that N/A values are not displayed unnecessarily."""

    def test_no_na_when_multi_dim_eval_missing(self):
        """Verify no N/A shown when multi-dim eval is None."""
        from madspark.cli.formatters.summary import SummaryFormatter
        from argparse import Namespace

        formatter = SummaryFormatter()
        args = Namespace()

        results = [{
            "improved_idea": "Test improved idea",
            "improved_score": 8.5,
            # No multi_dimensional_evaluation
        }]

        output = formatter.format(results, args)

        # Should not contain "N/A" for dimension scores
        assert "Feasibility: N/A" not in output
        assert "Innovation: N/A" not in output

    def test_dimension_scores_shown_when_present(self):
        """Verify dimension scores are shown when they have values."""
        from madspark.cli.formatters.summary import SummaryFormatter
        from argparse import Namespace

        formatter = SummaryFormatter()
        args = Namespace()

        results = [{
            "improved_idea": "Test improved idea",
            "improved_score": 8.5,
            "multi_dimensional_evaluation": {
                "overall_score": 8.0,
                "dimension_scores": {
                    "feasibility": 8.5,
                    "innovation": 9.0,
                    "impact": 7.5
                }
            }
        }]

        output = formatter.format(results, args)

        # Should show actual values, not N/A
        assert "Feasibility: 8.5" in output or "feasibility" in output.lower()
        assert "Innovation: 9.0" in output or "innovation" in output.lower()

    def test_partial_dimension_scores_only_show_available(self):
        """Only show dimensions that have actual values."""
        from madspark.cli.formatters.summary import SummaryFormatter
        from argparse import Namespace

        formatter = SummaryFormatter()
        args = Namespace()

        results = [{
            "improved_idea": "Test improved idea",
            "improved_score": 8.5,
            "multi_dimensional_evaluation": {
                "overall_score": 8.0,
                "dimension_scores": {
                    "feasibility": 8.5,
                    # Other dimensions not present
                }
            }
        }]

        output = formatter.format(results, args)

        # Should show feasibility
        assert "Feasibility" in output or "feasibility" in output.lower()
        # Should not show N/A for missing dimensions
        lines = output.split('\n')
        na_count = sum(1 for line in lines if 'N/A' in line and any(dim in line.lower() for dim in ['innovation', 'impact', 'scalability']))
        assert na_count == 0, f"Found N/A for missing dimensions in output: {output}"


class TestIntegrationEvaluationDataFlow:
    """Integration tests for complete evaluation data flow."""

    def test_full_workflow_passes_evaluations_to_improvement(self):
        """Run workflow and verify evaluations reach improvement step."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator
        from madspark.utils.batch_monitor import BatchMonitor

        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        # Candidate with all evaluation data
        candidates = [{
            "idea": "AI-powered tutoring",
            "text": "AI-powered tutoring",
            "initial_score": 7.5,
            "initial_critique": "Good concept, needs refinement",
            "advocacy": "Strong market potential",
            "skepticism": "Technical complexity",
            "multi_dimensional_evaluation": {
                "dimension_scores": {
                    "feasibility": 7.0,
                    "innovation": 8.5,
                    "impact": 8.0
                },
                "overall_score": 7.8
            },
            "logical_inference": {
                "confidence": 0.85,
                "conclusion": "Approach is sound",
                "inference_chain": ["Given market need", "AI capability", "Therefore viable"]
            }
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Enhanced AI tutoring with personalization"}], 150)

            updated, tokens = orchestrator.improve_ideas_with_monitoring(
                candidates=candidates,
                topic="EdTech",
                context="Online learning",
                monitor=monitor
            )

            # Verify all data was passed
            call_args = mock_improve.call_args[0][0][0]  # First item of first positional arg

            assert call_args.get("initial_score") == 7.5
            assert call_args.get("dimension_scores") is not None
            assert call_args.get("dimension_scores").get("innovation") == 8.5
            assert call_args.get("logical_inference") is not None
            assert "85%" in call_args.get("logical_inference")

    def test_backward_compatibility_without_new_fields(self):
        """Verify existing code works without new fields."""
        from madspark.core.workflow_orchestrator import WorkflowOrchestrator

        orchestrator = WorkflowOrchestrator(verbose=False)

        # Legacy candidate format without new fields
        candidates = [{
            "idea": "Test idea",
            "text": "Test idea",
            "critique": "Basic critique",
            "advocacy": "Advocacy points",
            "skepticism": "Skeptic concerns"
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Better idea"}], 100)

            # Should not raise exception
            updated, tokens = orchestrator.improve_ideas(
                candidates=candidates,
                topic="Test",
                context="Test"
            )

            assert updated[0]["improved_idea"] == "Better idea"
            assert tokens == 100
