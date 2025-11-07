from argparse import Namespace

"""Test brief output formatting improvements."""
import os  # noqa: E402
import sys  # noqa: E402

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.cli.cli import format_results  # noqa: E402


class TestBriefOutputFormatting:
    """Test that brief output is solution-focused and well-formatted."""
    
    def test_brief_mode_has_proper_headers(self):
        """Brief mode should have markdown headers."""
        results = [{
            'idea': 'Solar panel installation program',
            'initial_score': 6.0,
            'improved_idea': 'Community solar panel installation program with financing',
            'improved_score': 8.0,
            'score_delta': 2.0
        }]
        
        output = format_results(results, 'brief', Namespace())
        
        # Should have markdown headers
        assert '## ' in output or '### ' in output, "Brief output should have markdown headers"
    
    def test_brief_mode_focuses_on_solution(self):
        """Brief mode should emphasize the solution, not metrics."""
        results = [{
            'idea': 'Solar panel installation program',
            'initial_score': 6.0,
            'improved_idea': 'Community solar panel installation program with financing options',
            'improved_score': 8.0,
            'score_delta': 2.0
        }]
        
        output = format_results(results, 'brief', Namespace())
        
        # The improved idea should be prominently featured
        assert 'Community solar panel installation program with financing options' in output
        
        # Should not start with confusing text like "version of"
        assert not output.startswith('version of')
        assert 'version of:' not in output
        
        # Should focus on solution, not metrics
        lines = output.split('\n')
        solution_lines = [line for line in lines if 'solar panel' in line.lower()]
        metric_lines = [line for line in lines if 'score' in line.lower() or 'improvement' in line.lower()]
        
        # Solution content should appear before metrics
        if solution_lines and metric_lines:
            solution_pos = min(lines.index(line) for line in solution_lines)
            metric_pos = min(lines.index(line) for line in metric_lines)
            assert solution_pos < metric_pos, "Solution should appear before metrics"
    
    def test_brief_mode_clean_presentation(self):
        """Brief mode should have clean, user-friendly presentation."""
        results = [{
            'idea': 'Original idea text',
            'improved_idea': 'Solar-powered community garden with shared workspace',
            'improved_score': 8.5
        }]
        
        output = format_results(results, 'brief', Namespace())
        
        # Should not have confusing technical terms
        assert 'Enhancements based on feedback:' not in output
        assert 'Addressed critique points' not in output
        assert 'Incorporated advocacy strengths' not in output
        
        # Should be clean and direct
        assert 'Solar-powered community garden with shared workspace' in output
    
    def test_brief_mode_is_default(self):
        """Brief mode should be the default output format."""
        # This will be tested by checking CLI argument parsing
        # For now, just ensure brief mode works properly
        results = [{'idea': 'Basic concept', 'improved_idea': 'Smart recycling system for urban areas', 'improved_score': 7.0}]
        output = format_results(results, 'brief', Namespace())
        assert len(output) > 0
        assert 'Smart recycling system for urban areas' in output