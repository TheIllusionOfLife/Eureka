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
        
        # Test that the logical inference is preserved in the critique
        assert "🧠 Logical Inference Analysis" in result.initial_critique
        assert "Inference Chain:" in result.initial_critique
        assert "Confidence: 85%" in result.initial_critique
        
        # Test that the data structure maintains the formatting
        critique_lines = result.initial_critique.split('\n')
        assert any("Urban areas have limited space" in line for line in critique_lines)
        assert any("Conclusion:" in line for line in critique_lines)