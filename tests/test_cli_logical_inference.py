"""Test CLI logical inference functionality."""
import pytest
from unittest.mock import patch


class TestCLILogicalInference:
    """Test logical inference functionality through the CLI."""
    
    @pytest.mark.skip(reason="Complex CLI integration test - logical inference is tested in other test files")
    def test_cli_logical_flag_triggers_inference(self):
        """Test that --logical flag triggers logical inference analysis."""
        # Test that the CLI accepts the --logical flag
        test_args = [
            'cli.py',
            'urban farming',
            'limited space',
            '--logical',
            '--num-candidates', '1',
            '--output-format', 'summary'
        ]
        
        with patch('sys.argv', test_args):
            with patch('madspark.core.coordinator.run_multistep_workflow') as mock_run:
                # Create mock results with logical inference
                mock_result = {
                    'idea': "Vertical community gardens",
                    'initial_score': 8.0,
                    'initial_critique': "Good idea\n\n🧠 Logical Inference Analysis:\n\nInference Chain:\n  → Urban farming addresses food security",
                    'improved_idea': "Enhanced vertical gardens",
                    'improved_score': 9.0,
                    'improved_critique': "Excellent improvement",
                    'advocacy': "Strong support",
                    'skepticism': "Minor concerns",
                    'multi_dimensional_evaluation': None,
                    'score_delta': 1.0,
                    'is_meaningful_improvement': True,
                    'similarity_score': 0.0
                }
                
                mock_run.return_value = [mock_result]
                
                # Import and run main with output capturing
                from io import StringIO
                import sys
                captured_output = StringIO()
                sys.stdout = captured_output
                
                try:
                    from madspark.cli.cli import main
                    main()
                except SystemExit as e:
                    # Exit code 0 is success
                    if e.code != 0:
                        # Print captured output for debugging
                        print(f"Exit code: {e.code}")
                        print(f"Output: {captured_output.getvalue()}")
                    assert e.code == 0
                finally:
                    sys.stdout = sys.__stdout__
                
                # Verify logical inference was enabled
                assert mock_run.called
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs.get('logical_inference') is True
    
    def test_logical_inference_display_formatting(self):
        """Test that logical inference results are properly formatted for display."""
        from unittest.mock import Mock
        from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceResult

        # Create test result
        result = InferenceResult(
            inference_chain=[
                "Urban areas need sustainable solutions",
                "Vertical farming maximizes limited space",
                "Community involvement ensures success"
            ],
            conclusion="Vertical community gardens are ideal for urban sustainability",
            confidence=0.9,
            improvements="Consider solar panels for energy independence"
        )

        # Test formatting - provide mock client since __init__ requires genai_client or router
        mock_client = Mock()
        engine = LogicalInferenceEngine(genai_client=mock_client)
        
        # Brief format
        brief = engine.format_for_display(result, 'brief')
        assert "Conclusion:" in brief
        assert "90%" in brief
        assert "Urban areas" not in brief  # Chain not shown
        
        # Standard format
        standard = engine.format_for_display(result, 'standard')
        assert "🧠 Logical Inference Analysis" in standard
        assert "Urban areas need sustainable solutions" in standard
        assert "Confidence: 90%" in standard
        
        # Detailed format
        detailed = engine.format_for_display(result, 'detailed')
        assert "Detailed" in detailed
        assert all(step in detailed for step in result.inference_chain)