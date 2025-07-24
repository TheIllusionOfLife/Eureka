"""
Test CLI Output Formatting Requirements

This test file defines the expected behavior for CLI output formatting.
These tests should FAIL initially and then pass after implementation.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.cli.cli import format_results, main


class TestOutputFormatting:
    """Test suite for CLI output formatting requirements."""
    
    def test_simple_mode_output_structure(self):
        """Test that simple mode has clean, user-friendly output structure."""
        # Mock result data similar to what we get from the system
        mock_results = [{
            'idea': 'Create vertical farms with air purification systems',
            'initial_score': 7.5,
            'initial_critique': 'Good feasibility but needs cost analysis',
            'advocacy': 'Strong environmental benefits and urban integration potential',
            'skepticism': 'High initial costs and maintenance complexity',
            'improved_idea': 'Enhanced vertical farming network with distributed air purification and community integration',
            'improved_score': 9.0,
            'score_delta': 1.5,
            'multi_dimensional_evaluation': {
                'overall_score': 8.2,
                'evaluation_summary': 'Strong idea with good feasibility and high impact'
            }
        }]
        
        # Test simple format (should be default)
        output = format_results(mock_results, 'simple')
        
        # Should NOT contain debugging info
        assert 'Enhanced Analysis' not in output
        assert '🧠' not in output
        assert 'INFO' not in output
        assert 'WARNING' not in output
        
        # Should have proper structure order
        lines = output.split('\n')
        original_line_idx = None
        initial_score_line_idx = None
        improved_line_idx = None
        
        for i, line in enumerate(lines):
            if '💭 Original:' in line or 'Create vertical farms' in line:
                original_line_idx = i
            elif '📊 Initial Score:' in line:
                initial_score_line_idx = i
            elif '✨ Improved:' in line or 'farming network' in line:
                improved_line_idx = i
        
        # Check order: Original should come before improved
        assert original_line_idx is not None, "Should contain the original idea"
        assert improved_line_idx is not None, "Should contain improved idea"
        assert original_line_idx < improved_line_idx, "Original should come before improved"
        
        # Should be clean and readable
        assert not any(line.startswith('2025-') for line in lines), "Should not contain timestamps"
        
    def test_no_content_truncation(self):
        """Test that important content is not truncated."""
        # Create a result with long content
        long_idea = "A" * 1000  # Long idea text
        long_improved = "B" * 1000  # Long improved idea
        
        mock_results = [{
            'idea': long_idea,
            'initial_score': 7.0,
            'initial_critique': 'Test critique',
            'improved_idea': long_improved,
            'improved_score': 8.5
        }]
        
        output = format_results(mock_results, 'text')
        
        # Should contain full content, not truncated
        assert long_idea in output, "Should not truncate main idea"
        assert long_improved in output, "Should not truncate improved idea"
        assert '...' not in output or output.count('...') <= 1, "Should minimize truncation"
        
    def test_no_duplicate_content(self):
        """Test that content is not repeated unnecessarily."""
        mock_results = [{
            'idea': 'Unique idea content',
            'initial_score': 7.0,
            'initial_critique': 'Unique critique',
            'improved_idea': 'Unique improved content',
            'improved_score': 8.0
        }]
        
        output = format_results(mock_results, 'text')
        
        # Check for duplicate content
        unique_phrases = ['Unique idea content', 'Unique critique', 'Unique improved content']
        for phrase in unique_phrases:
            count = output.count(phrase)
            assert count <= 1, f"'{phrase}' appears {count} times - should appear only once"
    
    def test_clean_markdown_rendering(self):
        """Test that markdown is properly formatted for terminal."""
        mock_results = [{
            'idea': 'Test idea with **bold** and *italic* text',
            'initial_score': 7.0,
            'initial_critique': 'Contains ## headers and - lists',
            'improved_idea': '### Improved Idea\n- Point 1\n- Point 2',
            'improved_score': 8.0
        }]
        
        output = format_results(mock_results, 'text')
        
        # Should handle markdown gracefully (either render or clean)
        # At minimum, should not break formatting
        lines = output.split('\n')
        assert all(len(line) < 200 for line in lines), "Lines should not be excessively long"
        
    def test_brief_mode_output(self):
        """Test that brief mode shows only essential information."""
        mock_results = [{
            'idea': 'Original idea',
            'initial_score': 6.0,
            'initial_critique': 'Long critique that should be hidden',
            'advocacy': 'Long advocacy that should be hidden',
            'skepticism': 'Long skepticism that should be hidden',
            'improved_idea': 'Final idea',
            'improved_score': 8.5
        }]
        
        # Brief mode should exist and work
        output = format_results(mock_results, 'brief')
        
        # Should contain final result
        assert 'Final idea' in output
        assert '8.5' in str(output)
        
        # Should NOT contain verbose agent interactions
        assert 'Long critique that should be hidden' not in output
        assert 'Long advocacy that should be hidden' not in output
        assert 'Long skepticism that should be hidden' not in output
        
    def test_coordinator_output_formatting(self):
        """Test that coordinator output is properly formatted."""
        # This will test the coordinator output structure
        # For now, we'll test that it produces structured output
        
        mock_coordinator_result = [{
            'idea': 'Community resilience hub',
            'initial_score': 6.2,
            'improved_idea': 'Enhanced resilience network',
            'improved_score': 9.0,
            'multi_dimensional_evaluation': {
                'overall_score': 8.5,
                'dimension_scores': {
                    'feasibility': 7.5,
                    'impact': 9.0,
                    'innovation': 8.0
                }
            }
        }]
        
        output = format_results(mock_coordinator_result, 'text')
        
        # Should be structured and readable
        assert 'Community resilience hub' in output
        assert 'Enhanced resilience network' in output
        assert '9.0' in output
        
        # Should not contain debugging artifacts
        assert 'WARNING' not in output
        assert 'HTTP Request' not in output
        assert 'AFC remote call' not in output


class TestCLIOptions:
    """Test suite for CLI options that should exist."""
    
    def test_help_option_exists(self):
        """Test that --help option works properly."""
        # This should pass after implementation
        with patch('sys.argv', ['mad_spark', '--help']):
            with patch('sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Should have printed help information
                    help_output = ' '.join([str(call) for call in mock_print.call_args_list])
                    assert '--verbose' in help_output or '-v' in help_output
                    assert 'usage' in help_output.lower()
    
    def test_verbose_option_exists(self):
        """Test that --verbose option is available."""
        # Test that the option can be parsed without error
        with patch('sys.argv', ['mad_spark', 'test topic', '--verbose']):
            with patch('madspark.cli.cli.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                try:
                    main()
                except SystemExit:
                    pass
                # Should not raise argument parsing error
    
    def test_brief_option_exists(self):
        """Test that --brief option is available."""
        with patch('sys.argv', ['mad_spark', 'test topic', '--brief']):
            with patch('madspark.cli.cli.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                try:
                    main()
                except SystemExit:
                    pass
                # Should not raise argument parsing error
    
    def test_top_ideas_option_exists(self):
        """Test that --top-ideas option is available."""
        with patch('sys.argv', ['mad_spark', 'test topic', '--top-ideas', '3']):
            with patch('madspark.cli.cli.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                try:
                    main()
                except SystemExit:
                    pass
                # Should not raise argument parsing error


if __name__ == '__main__':
    # Run these tests to see current failures
    pytest.main([__file__, '-v'])