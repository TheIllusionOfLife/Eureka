"""
Integration tests for CLI flags --enhanced and --logical.

Tests verify that flags produce expected output sections in various formatters.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys
import json

from madspark.cli.cli import main as cli_main
from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType


class TestEnhancedFlag:
    """Test --enhanced flag produces advocacy and skepticism sections."""

    def test_enhanced_flag_adds_advocacy_section(self):
        """Test that --enhanced flag triggers advocacy analysis."""
        # This test should FAIL initially because advocacy data may not be in output
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--enhanced', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Run CLI
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # Verify advocacy section exists
                assert 'Advocacy' in output or 'Strengths' in output, \
                    "Enhanced flag should produce advocacy section with strengths"
                assert 'Opportunities' in output, \
                    "Enhanced flag should include opportunities in advocacy section"

    def test_enhanced_flag_adds_skepticism_section(self):
        """Test that --enhanced flag triggers skepticism analysis."""
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--enhanced', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # Verify skepticism section exists
                assert 'Skepticism' in output or 'Flaws' in output, \
                    "Enhanced flag should produce skepticism section with flaws"
                assert 'Risks' in output, \
                    "Enhanced flag should include risks in skepticism section"

    def test_enhanced_flag_in_batch_coordinator(self):
        """Test that enhanced reasoning parameter flows to batch coordinator."""
        mock_engine = Mock(spec=ReasoningEngine)

        # Call batch coordinator with enhanced reasoning
        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator:
            mock_orch_instance = MagicMock()
            mock_orchestrator.return_value = mock_orch_instance

            # Mock orchestrator methods to return basic data
            mock_orch_instance.generate_ideas.return_value = (
                [{"text": "test idea", "score": 8.0}],
                []
            )
            mock_orch_instance.evaluate_ideas.return_value = [
                {"text": "test idea", "score": 8.0, "critique": "good"}
            ]
            mock_orch_instance.process_advocacy.return_value = None  # Modifies in place
            mock_orch_instance.process_skepticism.return_value = None  # Modifies in place

            result = run_multistep_workflow_batch(
                topic="test",
                context="test context",
                enable_reasoning=True,  # This maps to enhanced_reasoning
                reasoning_engine=mock_engine
            )

            # Verify advocacy and skepticism were called
            assert mock_orch_instance.process_advocacy.called, \
                "Advocacy should be called when enable_reasoning=True"
            assert mock_orch_instance.process_skepticism.called, \
                "Skepticism should be called when enable_reasoning=True"


class TestLogicalFlag:
    """Test --logical flag produces logical inference sections."""

    def test_logical_flag_adds_causal_chains(self):
        """Test that --logical flag produces causal chain analysis."""
        # This test should FAIL initially because logical inference not implemented in batch coordinator
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--logical', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # Verify logical inference sections exist
                assert 'Logical Inference' in output or 'Causal' in output, \
                    "Logical flag should produce causal chain analysis"

    def test_logical_flag_adds_constraints(self):
        """Test that --logical flag includes constraint analysis."""
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--logical', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                assert 'Constraint' in output, \
                    "Logical flag should include constraint analysis"

    def test_logical_flag_adds_contradictions(self):
        """Test that --logical flag includes contradiction detection."""
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--logical', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                assert 'Contradiction' in output, \
                    "Logical flag should include contradiction detection"

    def test_logical_flag_parameter_passed_to_coordinator(self):
        """Test that logical_inference parameter is passed to batch coordinator."""
        # This test should FAIL because logical_inference param doesn't exist in batch coordinator
        import inspect

        sig = inspect.signature(run_multistep_workflow_batch)
        params = sig.parameters

        assert 'logical_inference' in params, \
            "Batch coordinator should accept logical_inference parameter"

    def test_logical_inference_engine_called_when_flag_enabled(self):
        """Test that LogicalInferenceEngine is called when --logical flag is set."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock inference results
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.8
        mock_inference_result.conclusion = "Test conclusion"
        mock_inference_result.inference_chain = ["step1", "step2"]
        mock_inference_result.improvements = []

        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator:
            mock_orch_instance = MagicMock()
            mock_orchestrator.return_value = mock_orch_instance

            # Mock orchestrator methods
            mock_orch_instance.generate_ideas.return_value = (
                [{"text": "test idea", "score": 8.0}],
                []
            )
            mock_orch_instance.evaluate_ideas.return_value = [
                {"text": "test idea", "score": 8.0, "critique": "good"}
            ]

            # This should fail if logical_inference param doesn't exist
            try:
                result = run_multistep_workflow_batch(
                    topic="test",
                    context="test context",
                    logical_inference=True,
                    reasoning_engine=mock_engine
                )

                # Verify logical inference engine was called
                assert mock_logical_engine.analyze_batch.called, \
                    "Logical inference engine should be called when logical_inference=True"
            except TypeError as e:
                # Expected to fail initially
                pytest.fail(f"logical_inference parameter not supported: {e}")


class TestCombinedFlags:
    """Test --enhanced and --logical flags working together."""

    def test_both_flags_together(self):
        """Test that both flags can be used simultaneously."""
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--enhanced', '--logical', '--format', 'detailed']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # Should have both enhanced and logical sections
                assert ('Advocacy' in output or 'Strengths' in output), \
                    "Combined flags should include advocacy section"
                assert ('Skepticism' in output or 'Flaws' in output), \
                    "Combined flags should include skepticism section"
                assert ('Logical Inference' in output or 'Causal' in output), \
                    "Combined flags should include logical inference section"

    def test_both_flags_in_coordinator(self):
        """Test that both parameters are passed to coordinator correctly."""
        mock_engine = Mock(spec=ReasoningEngine)
        mock_logical_engine = Mock(spec=LogicalInferenceEngine)
        mock_engine.logical_inference_engine = mock_logical_engine

        # Mock inference results
        mock_inference_result = Mock()
        mock_inference_result.confidence = 0.8
        mock_inference_result.conclusion = "Test"
        mock_inference_result.inference_chain = []
        mock_inference_result.improvements = []
        mock_logical_engine.analyze_batch.return_value = [mock_inference_result]

        with patch('madspark.core.coordinator_batch.WorkflowOrchestrator') as mock_orchestrator:
            mock_orch_instance = MagicMock()
            mock_orchestrator.return_value = mock_orch_instance

            mock_orch_instance.generate_ideas.return_value = (
                [{"text": "test idea", "score": 8.0}],
                []
            )
            mock_orch_instance.evaluate_ideas.return_value = [
                {"text": "test idea", "score": 8.0}
            ]
            mock_orch_instance.process_advocacy.return_value = None
            mock_orch_instance.process_skepticism.return_value = None

            try:
                result = run_multistep_workflow_batch(
                    topic="test",
                    context="test context",
                    enable_reasoning=True,
                    logical_inference=True,
                    reasoning_engine=mock_engine
                )

                # Both should be called
                assert mock_orch_instance.process_advocacy.called
                assert mock_orch_instance.process_skepticism.called
                assert mock_logical_engine.analyze_batch.called
            except TypeError:
                pytest.fail("Both flags should be supported together")


class TestOutputFormats:
    """Test that flags work with different output formats."""

    @pytest.mark.parametrize("format_type", ["detailed", "simple", "brief"])
    def test_enhanced_flag_with_formats(self, format_type):
        """Test --enhanced flag with different output formats."""
        with patch('sys.argv', ['cli', 'test', 'context', '--enhanced', '--format', format_type]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # At minimum should have some output
                assert len(output) > 0, f"Enhanced flag should produce output in {format_type} format"

    @pytest.mark.parametrize("format_type", ["detailed", "simple", "brief"])
    def test_logical_flag_with_formats(self, format_type):
        """Test --logical flag with different output formats."""
        with patch('sys.argv', ['cli', 'test', 'context', '--logical', '--format', format_type]):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                try:
                    cli_main()
                except SystemExit:
                    pass

                output = mock_stdout.getvalue()

                # At minimum should have some output
                assert len(output) > 0, f"Logical flag should produce output in {format_type} format"
