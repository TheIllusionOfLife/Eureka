"""
Integration tests for CLI flags --enhanced and --logical.

Tests verify that flags produce expected output sections and properly invoke
the correct agent methods.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.core.enhanced_reasoning import ReasoningEngine

# Guard import of LogicalInferenceEngine which requires optional google.genai dependency
LogicalInferenceEngine = pytest.importorskip(
    "madspark.utils.logical_inference_engine",
    reason="LogicalInferenceEngine requires google.genai"
).LogicalInferenceEngine

InferenceType = pytest.importorskip(
    "madspark.utils.logical_inference_engine",
    reason="InferenceType requires google.genai"
).InferenceType

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestEnhancedFlagCoordinator:
    """Test --enhanced flag at coordinator level."""

    def test_enable_reasoning_triggers_advocacy_and_skepticism(self):
        """Test that enable_reasoning=True calls advocacy and skepticism processing."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_engine.logical_inference_engine = None

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods to return proper structure
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                None  # monitor result
            )
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                 0)
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                 0)

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            # Call coordinator with enable_reasoning=True
            run_multistep_workflow_batch(
                topic="test",
                context="test context",
                enable_reasoning=True,
                reasoning_engine=mock_engine
            )

            # Verify advocacy and skepticism were called
            assert mock_orch.process_advocacy_with_monitoring.called, \
                "Advocacy should be called when enable_reasoning=True"
            assert mock_orch.process_skepticism_with_monitoring.called, \
                "Skepticism should be called when enable_reasoning=True"

    def test_disable_reasoning_skips_advocacy_and_skepticism(self):
        """Test that enable_reasoning=False skips advocacy and skepticism."""
        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock minimal workflow
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            # Call coordinator with enable_reasoning=False
            run_multistep_workflow_batch(
                topic="test",
                context="test context",
                enable_reasoning=False
            )

            # Verify advocacy and skepticism were NOT called
            assert not mock_orch.process_advocacy_with_monitoring.called, \
                "Advocacy should NOT be called when enable_reasoning=False"
            assert not mock_orch.process_skepticism_with_monitoring.called, \
                "Skepticism should NOT be called when enable_reasoning=False"


class TestLogicalFlagCoordinator:
    """Test --logical flag at coordinator level."""

    def test_logical_inference_parameter_exists(self):
        """Test that batch coordinator accepts logical_inference parameter."""
        import inspect

        sig = inspect.signature(run_multistep_workflow_batch)
        params = sig.parameters

        assert 'logical_inference' in params, \
            "Batch coordinator should accept logical_inference parameter"

    def test_logical_inference_enabled_calls_engine(self):
        """Test that logical_inference=True calls the logical inference engine."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock inference results
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.8
        mock_inference_result.conclusion = "Test conclusion"
        mock_inference_result.inference_chain = ["step1", "step2"]
        mock_inference_result.improvements = None

        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                0
            )
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                0
            )
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                0
            )
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                0
            )

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            # Call with logical_inference=True
            result = run_multistep_workflow_batch(
                topic="test",
                context="test context",
                logical_inference=True,
                reasoning_engine=mock_engine
            )

            # Verify logical inference engine was called
            assert mock_logical_engine.analyze_batch.called, \
                "Logical inference engine should be called when logical_inference=True"

            # Verify it was called with correct parameters
            call_args = mock_logical_engine.analyze_batch.call_args
            assert call_args[0][0] == ["test idea"], "Should pass idea texts"
            assert call_args[0][1] == "test", "Should pass topic"
            assert call_args[0][2] == "test context", "Should pass context"
            assert call_args[0][3] == InferenceType.FULL, "Should use FULL inference type"

            # Verify results include logical_inference field
            assert len(result) > 0, "Should return results"
            assert "logical_inference" in result[0], "Results should include logical_inference field"

    def test_logical_inference_disabled_skips_engine(self):
        """Test that logical_inference=False skips logical inference engine."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                0
            )
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                0
            )
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                0
            )
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                0
            )

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            # Call with logical_inference=False (default)
            run_multistep_workflow_batch(
                topic="test",
                context="test context",
                logical_inference=False,
                reasoning_engine=mock_engine
            )

            # Verify logical inference engine was NOT called
            assert not mock_logical_engine.analyze_batch.called, \
                "Logical inference engine should NOT be called when logical_inference=False"

    def test_logical_inference_adds_data_to_candidates(self):
        """Test that logical inference adds proper data structure to candidates."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock high-confidence inference result
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.9
        mock_inference_result.conclusion = "Strong conclusion"
        mock_inference_result.inference_chain = ["premise1", "premise2", "conclusion"]
        mock_inference_result.improvements = ["improvement1", "improvement2"]

        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                 0)
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                 0)

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            result = run_multistep_workflow_batch(
                topic="test",
                context="test context",
                logical_inference=True,
                reasoning_engine=mock_engine
            )

            # Verify logical_inference data structure
            logical_data = result[0]["logical_inference"]
            assert logical_data is not None, "High-confidence result should be included"
            assert logical_data["confidence"] == 0.9
            assert logical_data["conclusion"] == "Strong conclusion"
            assert logical_data["inference_chain"] == ["premise1", "premise2", "conclusion"]
            assert logical_data["improvements"] == ["improvement1", "improvement2"]

    def test_low_confidence_logical_inference_excluded(self):
        """Test that low-confidence inference results are excluded."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock low-confidence inference result
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.3  # Below 0.5 threshold
        mock_inference_result.conclusion = "Weak conclusion"
        mock_inference_result.inference_chain = []
        mock_inference_result.improvements = None

        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                 0)
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                 0)

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            result = run_multistep_workflow_batch(
                topic="test",
                context="test context",
                logical_inference=True,
                reasoning_engine=mock_engine
            )

            # Verify low-confidence result is excluded
            assert result[0]["logical_inference"] is None, \
                "Low-confidence inference (<0.5) should be excluded"


class TestCombinedFlags:
    """Test --enhanced and --logical flags working together."""

    def test_both_flags_together(self):
        """Test that both enhanced and logical inference can be enabled simultaneously."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock inference results
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.8
        mock_inference_result.conclusion = "Test"
        mock_inference_result.inference_chain = []
        mock_inference_result.improvements = None
        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator_class:
            mock_orch = MagicMock()
            mock_orchestrator_class.return_value = mock_orch

            # Mock workflow methods
            mock_orch.generate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.evaluate_ideas_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good"}],
                 0)
            mock_orch.process_advocacy_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "advocacy": {}}],
                 0)
            mock_orch.process_skepticism_with_monitoring.return_value = (
                [{"text": "test idea", "score": 8.0, "critique": "good", "skepticism": {}}],
                 0)

            # Mock improve/reevaluate to preserve existing fields
            def mock_improve(candidates, topic, context, monitor):
                for c in candidates:
                    c.setdefault("improved_idea", "improved")
                    c.setdefault("improved_score", c.get("score", 0.0))
                return candidates, 0

            def mock_reevaluate(candidates, topic, context, monitor):
                return candidates, 0

            mock_orch.improve_ideas_with_monitoring.side_effect = mock_improve
            mock_orch.reevaluate_ideas_with_monitoring.side_effect = mock_reevaluate

            # Call with both flags enabled
            result = run_multistep_workflow_batch(
                topic="test",
                context="test context",
                enable_reasoning=True,
                logical_inference=True,
                reasoning_engine=mock_engine
            )

            # Both should be called
            assert mock_orch.process_advocacy_with_monitoring.called, \
                "Advocacy should be called when enable_reasoning=True"
            assert mock_orch.process_skepticism_with_monitoring.called, \
                "Skepticism should be called when enable_reasoning=True"
            assert mock_logical_engine.analyze_batch.called, \
                "Logical inference should be called when logical_inference=True"

            # Verify result includes both types of data
            assert "advocacy" in result[0] or "skepticism" in result[0], \
                "Result should include advocacy/skepticism data"
            assert "logical_inference" in result[0], \
                "Result should include logical inference data"
