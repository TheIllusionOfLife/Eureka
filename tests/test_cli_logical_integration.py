"""Integration test for CLI logical inference."""
import pytest
import subprocess
import sys
import os


class TestCLILogicalIntegration:
    """Test CLI logical inference integration."""
    
    @pytest.mark.integration
    def test_cli_logical_flag_mock_mode(self):
        """Test that --logical flag works in mock mode."""
        # Run CLI in mock mode with logical inference
        env = os.environ.copy()
        env['MADSPARK_MODE'] = 'mock'
        env['PYTHONPATH'] = 'src'
        
        result = subprocess.run(
            [sys.executable, '-m', 'madspark.cli.cli',
             'sustainable farming',
             'urban environment',
             '--logical',
             '--num-candidates', '1',
             '--output-format', 'summary'],
            capture_output=True,
            text=True,
            env=env
        )
        
        # Should complete successfully
        assert result.returncode == 0
        
        # Output should contain some indication of completion
        assert 'sustainable' in result.stdout.lower() or 'farming' in result.stdout.lower()
        
        # Should not have errors about logical inference
        assert 'logical inference failed' not in result.stderr.lower()
    
    def test_logical_inference_formatting_in_output(self):
        """Test that logical inference results appear in formatted output."""
        from madspark.cli.output_formatter import OutputFormatter
        from madspark.core.coordinator import CandidateData
        
        # Create mock result with logical inference in critique
        result = CandidateData(
            idea="Vertical urban farms",
            initial_score=8.0,
            initial_critique="""Good idea for urban farming.

🧠 Logical Inference Analysis:

Inference Chain:
  → Urban areas have limited space
  → Vertical solutions maximize space usage
  → Community involvement ensures sustainability

Conclusion: Vertical farms are optimal for urban agriculture

Confidence: 85%""",
            advocacy="Strong benefits",
            skepticism="Some concerns",
            improved_idea="Enhanced vertical farms with solar",
            improved_score=9.0,
            improved_critique="Excellent improvement"
        )
        
        # Format output
        formatter = OutputFormatter()
        output = formatter.format_results([result], format_type='detailed')
        
        # Should contain logical inference
        assert "🧠 Logical Inference Analysis" in output
        assert "Inference Chain:" in output
        assert "Confidence: 85%" in output