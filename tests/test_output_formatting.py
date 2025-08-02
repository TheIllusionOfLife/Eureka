"""Tests for CLI output formatting with structured data."""
import pytest
from unittest.mock import Mock, patch

from madspark.cli.cli import format_results
from madspark.utils.output_processor import (
    convert_markdown_to_cli,
    format_multi_dimensional_scores,
    format_logical_inference_results,
    smart_truncate_text
)


class TestOutputFormatting:
    """Test suite for output formatting functionality."""
    
    def test_format_results_removes_text_prefix(self):
        """Test that format_results doesn't show 'Text:' prefix."""
        results = [{
            'idea': 'AI-Powered Learning Assistant',
            'initial_score': 8.5,
            'initial_critique': 'Strong concept with good potential'
        }]
        
        # Test all format types
        for format_type in ['brief', 'simple', 'detailed', 'summary']:
            output = format_results(results, format_type)
            assert 'Text:' not in output
            assert 'AI-Powered Learning Assistant' in output
    
    def test_format_results_shows_enhanced_analysis_clearly(self):
        """Test that enhanced analysis shows actual enhancements."""
        results = [{
            'idea': 'Test Idea',
            'initial_score': 7.0,
            'multi_dimensional_evaluation': {
                'overall_score': 8.3,
                'dimension_scores': {
                    'feasibility': 9.0,
                    'innovation': 8.0,
                    'impact': 7.0,
                    'cost_effectiveness': 9.5,
                    'scalability': 8.0,
                    'safety_score': 8.5,  # Renamed from risk_assessment
                    'timeline': 9.0
                },
                'evaluation_summary': 'Excellent feasibility and cost-effectiveness'
            },
            'logical_inference_results': {
                'causal_chains': ['A leads to B', 'B enables C'],
                'constraints': {'budget': 'satisfied', 'timeline': 'satisfied'},
                'contradictions': [],
                'implications': ['Scalable to enterprise level']
            }
        }]
        
        output = format_results(results, 'detailed')
        
        # Should show multi-dimensional scores clearly
        assert '📊 Multi-Dimensional Evaluation:' in output
        assert 'Overall Score: 8.3' in output
        assert 'Feasibility: 9.0' in output
        assert 'Safety Score: 8.5' in output
        assert 'Risk Assessment:' not in output  # Old name should not appear
        assert '(lower is better)' not in output  # Confusing text removed
        
        # Should show logical inference when present
        assert '🔍 Logical Inference Analysis:' in output
        assert 'Causal Chains:' in output
        assert 'A leads to B' in output
    
    def test_format_advocacy_skepticism_sections(self):
        """Test proper formatting of advocacy and skepticism sections."""
        results = [{
            'idea': 'Test Idea',
            'advocacy': {
                'strengths': [
                    {'title': 'Strong Market Fit', 'description': 'Addresses clear need'},
                    {'title': 'Technical Feasibility', 'description': 'Can be built quickly'}
                ],
                'opportunities': [
                    {'title': 'Growth Potential', 'description': 'Can expand globally'}
                ]
            },
            'skepticism': {
                'critical_flaws': [
                    {'title': 'High Competition', 'description': 'Many similar solutions'},
                    {'title': 'Funding Required', 'description': 'Needs significant investment'}
                ],
                'risks_and_challenges': [
                    {'title': 'Technical Debt', 'description': 'Quick build may cause issues'}
                ]
            }
        }]
        
        output = format_results(results, 'detailed')
        
        # Check formatting
        assert '🔷 Advocacy:' in output
        assert 'STRENGTHS:' in output
        assert '• Strong Market Fit:' in output
        assert '• Technical Feasibility:' in output
        assert 'OPPORTUNITIES:' in output
        
        assert '🔶 Skepticism:' in output
        assert 'CRITICAL FLAWS:' in output
        assert '• High Competition:' in output
    
    def test_score_improvement_display(self):
        """Test that score improvements show correctly."""
        results = [{
            'idea': 'Test Idea',
            'initial_score': 6.5,
            'improved_score': 8.8,
            'score_delta': 2.3
        }]
        
        output = format_results(results, 'detailed')
        
        # Should show proper improvement without confusing signs
        assert '⬆️  Improvement: +2.3' in output
        assert '+-2.3' not in output  # No double signs
    
    def test_improved_idea_formatting(self):
        """Test that improved ideas have proper line breaks."""
        results = [{
            'idea': 'Original Idea',
            'improved_idea': {
                'improved_title': 'Enhanced Solution',
                'improved_description': 'A much better implementation with clear benefits',
                'key_improvements': [
                    'Added AI capabilities',
                    'Improved user interface',
                    'Better scalability'
                ],
                'implementation_steps': [
                    'Phase 1: Build core features',
                    'Phase 2: Add AI integration',
                    'Phase 3: Scale to production'
                ]
            }
        }]
        
        output = format_results(results, 'detailed')
        
        # Check proper formatting
        assert '✨ Improved Idea:' in output
        assert 'Enhanced Solution' in output
        assert 'Key Improvements:' in output
        assert '• Added AI capabilities' in output
        assert 'Implementation Steps:' in output
        assert '1. Phase 1: Build core features' in output


class TestMarkdownConversion:
    """Test markdown to CLI conversion."""
    
    def test_convert_markdown_bullets(self):
        """Test conversion of markdown bullets to CLI format."""
        markdown_text = """
* First bullet point
* Second bullet point
  * Nested bullet
* Third bullet point
"""
        cli_text = convert_markdown_to_cli(markdown_text)
        
        assert '• First bullet point' in cli_text
        assert '• Second bullet point' in cli_text
        assert '  ◦ Nested bullet' in cli_text
        assert '*' not in cli_text  # No markdown bullets
    
    def test_convert_markdown_bold(self):
        """Test conversion of markdown bold text."""
        markdown_text = "This is **important** and this is **also bold**"
        cli_text = convert_markdown_to_cli(markdown_text)
        
        # Bold text should be preserved or converted to caps
        assert 'important' in cli_text or 'IMPORTANT' in cli_text
        assert '**' not in cli_text  # No markdown syntax
    
    def test_convert_numbered_lists(self):
        """Test conversion of numbered lists."""
        markdown_text = """
1. First item
2. Second item
3. Third item
"""
        cli_text = convert_markdown_to_cli(markdown_text)
        
        assert '1. First item' in cli_text
        assert '2. Second item' in cli_text
        assert '3. Third item' in cli_text


class TestSmartTruncation:
    """Test smart truncation functionality."""
    
    def test_truncate_at_terminal_width(self):
        """Test that text is truncated based on terminal width."""
        long_text = "This is a very long text " * 100
        
        # Mock terminal width
        with patch('shutil.get_terminal_size') as mock_size:
            mock_size.return_value.columns = 80
            mock_size.return_value.lines = 24
            
            truncated = smart_truncate_text(long_text, max_lines=20)
            
            # Should be truncated with continuation indicator
            assert len(truncated.split('\n')) <= 20
            assert '... [truncated]' in truncated or '(see full output in file)' in truncated
    
    def test_preserve_complete_sections(self):
        """Test that truncation preserves complete sections."""
        text_with_sections = """
## Section 1
Content for section 1

## Section 2
Content for section 2

## Section 3
Very long content that should be truncated but section boundary should be respected
""" + ("More content " * 100)
        
        truncated = smart_truncate_text(text_with_sections, max_lines=10)
        
        # Should not cut in middle of section
        assert '## Section' in truncated
        assert truncated.count('##') >= 1  # At least one complete section


class TestIntegrationFormatting:
    """Integration tests for complete formatting pipeline."""
    
    @pytest.mark.integration
    def test_complete_formatting_pipeline(self):
        """Test the complete formatting pipeline with structured data."""
        # Simulate structured response from agents
        structured_results = [{
            'idea': 'Smart Urban Garden',
            'initial_score': 7.5,
            'initial_critique': 'Good concept, needs refinement',
            'advocacy': {
                'strengths': [
                    {'title': 'Sustainability', 'description': 'Promotes local food production'},
                    {'title': 'Technology Integration', 'description': 'Uses IoT effectively'}
                ]
            },
            'skepticism': {
                'critical_flaws': [
                    {'title': 'Initial Cost', 'description': 'High setup expenses'}
                ]
            },
            'improved_idea': {
                'improved_title': 'Community Smart Garden Network',
                'improved_description': 'Shared urban gardening with IoT monitoring',
                'key_improvements': ['Cost sharing', 'Community engagement']
            },
            'improved_score': 8.9,
            'score_delta': 1.4,
            'multi_dimensional_evaluation': {
                'overall_score': 8.5,
                'dimension_scores': {
                    'feasibility': 8.0,
                    'innovation': 9.0,
                    'impact': 8.5,
                    'cost_effectiveness': 7.5,
                    'scalability': 9.0,
                    'safety_score': 9.5,
                    'timeline': 8.0
                }
            }
        }]
        
        # Format for different output types
        for format_type in ['brief', 'detailed']:
            output = format_results(structured_results, format_type)
            
            # Verify key elements are present and properly formatted
            assert 'Smart Urban Garden' in output
            assert 'Community Smart Garden Network' in output
            assert '8.9' in output  # Improved score
            
            if format_type == 'detailed':
                assert '🔷 Advocacy:' in output
                assert '🔶 Skepticism:' in output
                assert '✨ Improved Idea:' in output
                assert '📊 Multi-Dimensional Evaluation:' in output
                assert '+1.4' in output  # Proper score delta
                assert 'Safety Score: 9.5' in output
                assert '(lower is better)' not in output