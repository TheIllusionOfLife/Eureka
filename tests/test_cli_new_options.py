"""
Test New CLI Options Requirements

Tests for new CLI options that should match web interface functionality.
These tests should FAIL initially and pass after implementation.
"""
from argparse import Namespace
import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.cli.cli import create_parser


class TestNewCLIOptions:
    """Test suite for new CLI options that should be implemented."""
    
    def test_creativity_preset_option(self):
        """Test --temperature-preset option with presets."""
        parser = create_parser()
        
        # Test valid presets
        valid_presets = ['conservative', 'balanced', 'creative', 'wild']
        for preset in valid_presets:
            args = parser.parse_args(['test topic', '--temperature-preset', preset])
            assert hasattr(args, 'temperature_preset'), "Should have temperature_preset attribute"
            assert args.temperature_preset == preset, f"Should parse {preset} correctly"
    
    def test_top_ideas_option(self):
        """Test --top-ideas option for controlling number of ideas."""
        parser = create_parser()
        
        # Import determine_num_candidates to test default behavior
        from madspark.cli.cli import determine_num_candidates
        
        # Test default
        args = parser.parse_args(['test topic'])
        assert hasattr(args, 'top_ideas'), "Should have top_ideas attribute"
        # The attribute defaults to None, but determine_num_candidates should return 1
        assert args.top_ideas is None, "Attribute should default to None"
        assert determine_num_candidates(args) == 1, "Should default to 1 for faster execution through determine_num_candidates"
        
        # Test custom values
        for num in [1, 3, 5]:
            args = parser.parse_args(['test topic', '--top-ideas', str(num)])
            assert args.top_ideas == num, f"Should parse --top-ideas {num}"
            assert determine_num_candidates(args) == num, f"Should return {num} through determine_num_candidates"
    
    def test_num_candidates_backward_compatibility(self):
        """Test that deprecated --num-candidates still works for backward compatibility."""
        parser = create_parser()
        from madspark.cli.cli import determine_num_candidates
        
        # Test that --num-candidates still works
        args = parser.parse_args(['test topic', '--num-candidates', '5'])
        assert hasattr(args, 'num_candidates'), "Should have num_candidates attribute"
        assert args.num_candidates == 5, "Should parse --num-candidates 5"
        
        # Should use the value from --num-candidates (clamped to 1-5 range)
        assert determine_num_candidates(args) == 5, "Should use num_candidates value"
        
        # Test that --num-candidates takes precedence when both are specified (current behavior)
        args = parser.parse_args(['test topic', '--num-candidates', '5', '--top-ideas', '3'])
        assert determine_num_candidates(args) == 5, "Currently --num-candidates takes precedence when both are specified"
    
    def test_temperature_option(self):
        """Test --temperature option for custom temperature values."""
        parser = create_parser()
        
        # Test valid temperature range (using existing temperature system)
        for temp in [0.1, 0.5, 1.0]:
            args = parser.parse_args(['test topic', '--temperature', str(temp)])
            assert hasattr(args, 'temperature'), "Should have temperature attribute"
            assert args.temperature == temp, f"Should parse temperature {temp}"
    
    def test_brief_and_detailed_modes(self):
        """Test --brief and --detailed output modes."""
        parser = create_parser()
        
        # Test brief mode
        args = parser.parse_args(['test topic', '--brief'])
        assert hasattr(args, 'output_mode'), "Should have output_mode attribute"
        assert args.output_mode == 'brief', "Should set brief mode"
        
        # Test detailed mode
        args = parser.parse_args(['test topic', '--detailed'])
        assert args.output_mode == 'detailed', "Should set detailed mode"
        
        # Test they are mutually exclusive
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--brief', '--detailed'])
    
    def test_simple_mode_default(self):
        """Test that brief mode is the default."""
        parser = create_parser()
        args = parser.parse_args(['test topic'])
        
        # Should default to brief mode (changed from simple to brief as default)
        assert hasattr(args, 'output_mode'), "Should have output_mode attribute"
        assert args.output_mode == 'brief', "Should default to brief mode"
    
    def test_enhanced_reasoning_option(self):
        """Test --enhanced option for enhanced reasoning."""
        parser = create_parser()
        
        args = parser.parse_args(['test topic', '--enhanced'])
        assert hasattr(args, 'enhanced_reasoning'), "Should have enhanced_reasoning attribute"
        assert args.enhanced_reasoning is True, "Should enable enhanced reasoning"
    
    def test_logical_inference_option(self):
        """Test --logical option for logical inference."""
        parser = create_parser()
        
        args = parser.parse_args(['test topic', '--logical'])
        assert hasattr(args, 'logical_inference'), "Should have logical_inference attribute"
        assert args.logical_inference is True, "Should enable logical inference"
    
    def test_no_logs_option(self):
        """Test --no-logs option to suppress log output."""
        parser = create_parser()
        
        args = parser.parse_args(['test topic', '--no-logs'])
        assert hasattr(args, 'no_logs'), "Should have no_logs attribute"
        assert args.no_logs is True, "Should suppress logs"
    
    def test_save_bookmark_option(self):
        """Test --no-bookmark option for disabling automatic bookmarking."""
        parser = create_parser()
        
        args = parser.parse_args(['test topic', '--no-bookmark'])
        assert hasattr(args, 'no_bookmark'), "Should have no_bookmark attribute"
        assert args.no_bookmark is True, "Should disable automatic bookmarking"
    
    def test_list_bookmarks_option(self):
        """Test --list-bookmarks standalone option."""
        parser = create_parser()
        
        args = parser.parse_args(['--list-bookmarks'])
        assert hasattr(args, 'list_bookmarks'), "Should have list_bookmarks attribute"
        assert args.list_bookmarks is True, "Should list bookmarks"
    
    def test_remix_bookmarks_option(self):
        """Test --remix-bookmarks option."""
        parser = create_parser()
        
        args = parser.parse_args(['test topic', '--remix-bookmarks', 'id1,id2'])
        assert hasattr(args, 'remix_bookmarks'), "Should have remix_bookmarks attribute"
        assert args.remix_bookmarks == 'id1,id2', "Should parse bookmark IDs"
    
    def test_similarity_threshold_option(self):
        """Test --similarity option for controlling novelty filter."""
        parser = create_parser()
        
        for threshold in [0.0, 0.5, 0.8, 1.0]:
            args = parser.parse_args(['test topic', '--similarity', str(threshold)])
            assert hasattr(args, 'similarity_threshold'), "Should have similarity_threshold attribute"
            assert args.similarity_threshold == threshold, f"Should parse similarity {threshold}"


class TestArgumentValidation:
    """Test argument validation for new options."""
    
    def test_temperature_range_validation(self):
        """Test that temperature is validated within acceptable range."""
        parser = create_parser()
        
        # Should accept valid temperatures (existing system has its own validation)
        # Just test that parsing doesn't fail
        try:
            args = parser.parse_args(['test topic', '--temperature', '0.5'])
            assert hasattr(args, 'temperature')
        except SystemExit:
            pytest.fail("Valid temperature should not cause SystemExit")
    
    def test_top_ideas_validation(self):
        """Test that top-ideas is validated."""
        parser = create_parser()
        
        # Should reject invalid numbers
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--top-ideas', '0'])  # Too low
        
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--top-ideas', '11'])  # Too high
    
    def test_similarity_range_validation(self):
        """Test that similarity threshold is validated."""
        parser = create_parser()
        
        # Should reject out-of-range values
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--similarity', '-0.1'])  # Too low
        
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--similarity', '1.1'])  # Too high


class TestHelpSystem:
    """Test that help system works properly."""
    
    def test_help_command_shows_options(self):
        """Test that help shows all new options."""
        parser = create_parser()
        help_text = parser.format_help()
        
        # Should contain all new options
        expected_options = [
            '--temperature-preset', '--top-ideas', '--temperature', '--brief', 
            '--detailed', '--enhanced', '--logical', '--no-logs',
            '--no-bookmark', '--list-bookmarks', '--remix-bookmarks',
            '--similarity'
        ]
        
        for option in expected_options:
            assert option in help_text, f"Help should contain {option} option"
    
    def test_help_shows_usage_examples(self):
        """Test that help includes usage examples."""
        parser = create_parser()
        help_text = parser.format_help()
        
        # Should show different input formats
        assert 'how to' in help_text.lower(), "Should show question format example"
        assert 'come up with' in help_text.lower(), "Should show request format example"
    
    def test_version_option(self):
        """Test that --version option exists."""
        parser = create_parser()
        
        # --version causes SystemExit(0) which is expected
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])
        assert exc_info.value.code == 0


class TestOutputModeIntegration:
    """Test that output modes integrate properly with format_results."""
    
    def test_simple_mode_integration(self):
        """Test that simple mode produces clean output."""
        # This will test the integration after implementation
        mock_results = [{
            'idea': 'Test idea',
            'initial_score': 7.0,
            'improved_idea': 'Improved test idea',
            'improved_score': 8.5
        }]
        
        from madspark.cli.cli import format_results
        
        # Should not fail and should produce clean output
        output = format_results(mock_results, 'simple', Namespace())
        assert isinstance(output, str), "Should return string output"
        assert len(output) > 0, "Should produce non-empty output"
    
    def test_brief_mode_integration(self):
        """Test that brief mode produces minimal output."""
        mock_results = [{
            'idea': 'Test idea',
            'initial_score': 7.0,
            'improved_idea': 'Improved test idea',
            'improved_score': 8.5,
            'advocacy': 'Should be hidden',
            'skepticism': 'Should be hidden'
        }]
        
        from madspark.cli.cli import format_results
        
        output = format_results(mock_results, 'brief', Namespace())
        
        # Should contain the idea text (cleaner may simplify it) but not agent feedback
        assert 'test idea' in output.lower()
        assert 'Should be hidden' not in output
    
    def test_detailed_mode_integration(self):
        """Test that detailed mode shows all information."""
        mock_results = [{
            'idea': 'Test idea',
            'initial_score': 7.0,
            'improved_idea': 'Improved test idea',
            'improved_score': 8.5,
            'advocacy': 'Should be visible',
            'skepticism': 'Should be visible',
            'initial_critique': 'Should be visible'
        }]
        
        from madspark.cli.cli import format_results
        
        output = format_results(mock_results, 'detailed', Namespace())
        
        # Should contain all information
        assert 'Test idea' in output
        assert 'test idea' in output.lower()  # Improved idea may be cleaned
        assert 'Should be visible' in output


if __name__ == '__main__':
    # Run these tests to see current failures
    pytest.main([__file__, '-v'])