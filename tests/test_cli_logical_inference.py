"""Test CLI logical inference functionality."""
from unittest.mock import Mock, patch
from io import StringIO

from madspark.cli.cli import main


class TestCLILogicalInference:
    """Test logical inference functionality through the CLI."""
    
    @patch('madspark.agents.genai_client.get_genai_client')
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_logical_flag_triggers_inference(self, mock_stdout, mock_get_client):
        """Test that --logical flag triggers logical inference analysis."""
        # Setup mock GenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = """INFERENCE_CHAIN:
- Urban farming addresses food security
- Limited space requires innovative solutions
- Vertical gardens maximize space efficiency
- Community involvement ensures sustainability

CONCLUSION: Vertical community gardens are an optimal urban farming solution.

CONFIDENCE: 0.85

IMPROVEMENTS: Consider incorporating hydroponic systems for higher yields."""
        
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Run CLI with logical inference
        test_args = [
            'cli.py',
            'urban farming',
            'limited space',
            '--logical',
            '--num-candidates', '1',
            '--no-async'
        ]
        
        with patch('sys.argv', test_args):
            with patch('madspark.core.async_coordinator.AsyncCoordinator') as mock_async_class:
                # Mock the async coordinator to avoid actual API calls
                mock_async_instance = Mock()
                mock_async_instance.run_workflow.return_value = []
                mock_async_class.return_value = mock_async_instance
                
                # For synchronous mode, patch the run_multistep_workflow
                with patch('madspark.core.coordinator.run_multistep_workflow') as mock_run:
                    # Create mock results
                    mock_result = Mock()
                    mock_result.idea = "Vertical community gardens"
                    mock_result.initial_score = 8.0
                    mock_result.initial_critique = "Good idea\n\n🧠 Logical Inference Analysis:\n\nInference Chain:\n  → Urban farming addresses food security"
                    mock_result.improved_idea = "Enhanced vertical gardens"
                    mock_result.improved_score = 9.0
                    mock_result.improved_critique = "Excellent improvement"
                    
                    mock_run.return_value = [mock_result]
                    
                    # Run main
                    try:
                        main()
                    except SystemExit as e:
                        assert e.code == 0
                    
                    # Verify logical inference was enabled
                    assert mock_run.called
                    call_kwargs = mock_run.call_args[1]
                    assert call_kwargs.get('logical_inference') is True
                    
                    # Check output contains logical inference
                    output = mock_stdout.getvalue()
                    assert "Logical Inference Analysis" in output or "🧠" in output
    
    def test_logical_inference_display_formatting(self):
        """Test that logical inference results are properly formatted for display."""
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
        
        # Test formatting
        engine = LogicalInferenceEngine(None)
        
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