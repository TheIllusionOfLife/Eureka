"""
Comprehensive tests for Formatter Strategy Pattern.

Tests all formatters with various data scenarios to ensure correct behavior.
"""

import json
import pytest
from typing import Any, Dict, List
from argparse import Namespace

# Import formatters (these don't exist yet - TDD approach)
from madspark.cli.formatters import (
    ResultFormatter,
    BriefFormatter,
    SimpleFormatter,
    DetailedFormatter,
    SummaryFormatter,
    JsonFormatter,
    FormatterFactory,
)


# Test Fixtures
@pytest.fixture
def minimal_result() -> List[Dict[str, Any]]:
    """Minimal valid result with only required fields."""
    return [
        {
            "idea": "Test idea",
            "initial_score": 7.5,
        }
    ]


@pytest.fixture
def basic_result() -> List[Dict[str, Any]]:
    """Basic result with common fields."""
    return [
        {
            "idea": "Original test idea",
            "initial_score": 7.5,
            "initial_critique": "Good but needs improvement",
            "improved_idea": "Improved test idea with enhancements",
            "improved_score": 8.5,
            "score_delta": 1.0,
            "is_meaningful_improvement": True,
        }
    ]


@pytest.fixture
def structured_improved_result() -> List[Dict[str, Any]]:
    """Result with structured improved idea (dict format)."""
    return [
        {
            "idea": "Original idea",
            "initial_score": 7.0,
            "improved_idea": {
                "improved_title": "Enhanced Solution Title",
                "improved_description": "Detailed description of the improved solution.",
                "key_improvements": [
                    "Better performance",
                    "More scalable",
                    "Easier maintenance"
                ],
                "implementation_steps": [
                    "Step 1: Analysis",
                    "Step 2: Design",
                    "Step 3: Implementation"
                ]
            },
            "improved_score": 8.5,
            "score_delta": 1.5,
        }
    ]


@pytest.fixture
def full_result() -> List[Dict[str, Any]]:
    """Complete result with all possible fields."""
    return [
        {
            "idea": "1. Original comprehensive idea",
            "initial_score": 7.0,
            "initial_critique": "Solid foundation but needs refinement",
            "advocacy": json.dumps({
                "strengths": ["Strong market potential", "Innovative approach"],
                "opportunities": ["Growing demand", "Limited competition"],
                "concerns_addressed": ["Cost can be managed", "Timeline is feasible"]
            }),
            "skepticism": json.dumps({
                "flaws": ["Unclear value proposition", "High initial cost"],
                "risks": ["Market uncertainty", "Technical complexity"],
                "assumptions": ["User adoption", "Resource availability"],
                "considerations": ["Regulatory compliance", "Scalability challenges"]
            }),
            "improved_idea": "Refined comprehensive idea with strategic improvements",
            "improved_score": 8.8,
            "score_delta": 1.8,
            "is_meaningful_improvement": True,
            "multi_dimensional_evaluation": {
                "overall_score": 8.5,
                "dimension_scores": {
                    "feasibility": 0.85,
                    "innovation": 0.90,
                    "impact": 0.88,
                    "cost_effectiveness": 0.75,
                    "scalability": 0.82,
                    "risk_assessment": 0.30,
                    "timeline": 0.80
                },
                "evaluation_summary": "Strong innovation with good market fit"
            },
            "logical_inference": {
                "causal_chains": [
                    "Innovation → Market differentiation → Revenue growth",
                    "User adoption → Network effects → Platform value"
                ],
                "constraints": {
                    "Budget limit: $500K": "satisfied",
                    "Timeline: 6 months": "satisfied"
                },
                "contradictions": [],
                "implications": ["Requires dedicated team", "Potential for scaling"]
            }
        }
    ]


@pytest.fixture
def multiple_results() -> List[Dict[str, Any]]:
    """Multiple results to test iteration logic."""
    return [
        {
            "idea": "First idea",
            "initial_score": 6.5,
            "improved_idea": "Improved first idea",
            "improved_score": 7.8,
            "score_delta": 1.3,
        },
        {
            "idea": "Second idea",
            "initial_score": 8.0,
            "improved_idea": "Improved second idea",
            "improved_score": 8.2,
            "score_delta": 0.2,
            "is_meaningful_improvement": False,
        },
        {
            "idea": "Third idea",
            "initial_score": 5.5,
            "improved_idea": "Improved third idea",
            "improved_score": 8.9,
            "score_delta": 3.4,
            "is_meaningful_improvement": True,
        }
    ]


@pytest.fixture
def mock_args() -> Namespace:
    """Mock argparse.Namespace for testing."""
    return Namespace(
        output_format='brief',
        output_mode='brief',
    )


# Test Base Formatter Abstract Class
class TestResultFormatter:
    """Test the abstract base formatter class."""

    def test_cannot_instantiate_abstract_class(self):
        """ResultFormatter is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            ResultFormatter()

    def test_subclass_must_implement_format(self):
        """Subclasses must implement the format method."""
        class IncompleteFormatter(ResultFormatter):
            pass

        with pytest.raises(TypeError):
            IncompleteFormatter()


# Test JSON Formatter
class TestJsonFormatter:
    """Test JSON formatter."""

    def test_json_format_basic(self, basic_result):
        """JSON formatter should return valid JSON string."""
        formatter = JsonFormatter()
        output = formatter.format(basic_result, Namespace())

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["idea"] == "Original test idea"

    def test_json_format_preserves_all_fields(self, full_result):
        """JSON formatter should preserve all fields."""
        formatter = JsonFormatter()
        output = formatter.format(full_result, Namespace())

        parsed = json.loads(output)
        assert "advocacy" in parsed[0]
        assert "skepticism" in parsed[0]
        assert "multi_dimensional_evaluation" in parsed[0]
        assert "logical_inference" in parsed[0]

    def test_json_format_handles_empty_results(self):
        """JSON formatter should handle empty results list."""
        formatter = JsonFormatter()
        output = formatter.format([], Namespace())

        parsed = json.loads(output)
        assert parsed == []

    def test_json_format_unicode(self):
        """JSON formatter should handle unicode characters."""
        results = [{"idea": "Test with émojis 🚀 and spëcial çhars", "initial_score": 8.0}]
        formatter = JsonFormatter()
        output = formatter.format(results, Namespace())

        parsed = json.loads(output)
        assert "émojis 🚀" in parsed[0]["idea"]


# Test Brief Formatter
class TestBriefFormatter:
    """Test brief formatter."""

    def test_brief_single_result_header(self, basic_result):
        """Brief format should use 'Solution' header for single result."""
        formatter = BriefFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "## Solution" in output
        assert "## Idea 1" not in output

    def test_brief_multiple_results_headers(self, multiple_results):
        """Brief format should use 'Idea N' headers for multiple results."""
        formatter = BriefFormatter()
        output = formatter.format(multiple_results, Namespace())

        assert "## Idea 1" in output
        assert "## Idea 2" in output
        assert "## Idea 3" in output
        assert "## Solution" not in output

    def test_brief_shows_improved_idea(self, basic_result):
        """Brief format should show improved idea when available."""
        formatter = BriefFormatter()
        output = formatter.format(basic_result, Namespace())

        # Note: "Improved" prefix may be cleaned by improved_idea_cleaner
        assert "test idea with enhancements" in output

    def test_brief_shows_score(self, basic_result):
        """Brief format should show score information."""
        formatter = BriefFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "**Score:** 8.5/10" in output

    def test_brief_structured_improved_idea(self, structured_improved_result):
        """Brief format should handle structured improved idea."""
        formatter = BriefFormatter()
        output = formatter.format(structured_improved_result, Namespace())

        assert "Enhanced Solution Title" in output
        assert "Detailed description" in output

    def test_brief_fallback_to_original(self, minimal_result):
        """Brief format should fallback to original idea if no improved."""
        formatter = BriefFormatter()
        output = formatter.format(minimal_result, Namespace())

        assert "Test idea" in output
        assert "**Score:** 7.5/10" in output


# Test Simple Formatter
class TestSimpleFormatter:
    """Test simple formatter."""

    def test_simple_has_emojis(self, basic_result):
        """Simple format should include emoji indicators."""
        formatter = SimpleFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "💭" in output  # Original idea emoji
        assert "📊" in output  # Initial score emoji
        assert "✨" in output  # Improved emoji
        assert "📈" in output  # Final score emoji

    def test_simple_shows_score_delta(self, basic_result):
        """Simple format should show score improvement."""
        formatter = SimpleFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "⬆️  Improvement: +1.0" in output

    def test_simple_meaningful_improvement(self, multiple_results):
        """Simple format should distinguish meaningful improvements."""
        formatter = SimpleFormatter()
        output = formatter.format(multiple_results, Namespace())

        # First and third should show improvements (note: "Improved" prefix cleaned)
        assert "✨ Improved: first idea" in output or "✨ Improved: Improved first idea" in output
        assert "✨ Improved: third idea" in output or "✨ Improved: Improved third idea" in output

        # Second should show "already well-developed" message
        assert "✅ Already well-developed" in output

    def test_simple_separator_for_multiple(self, multiple_results):
        """Simple format should use separators for multiple ideas."""
        formatter = SimpleFormatter()
        output = formatter.format(multiple_results, Namespace())

        assert "━━━ Idea 1 ━━━" in output
        assert "━━━ Idea 2 ━━━" in output
        assert "━━━ Idea 3 ━━━" in output

    def test_simple_no_separator_for_single(self, basic_result):
        """Simple format should not use separator for single idea."""
        formatter = SimpleFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "━━━" not in output

    def test_simple_evaluation_summary(self, full_result):
        """Simple format should include evaluation summary."""
        formatter = SimpleFormatter()
        output = formatter.format(full_result, Namespace())

        assert "📋 Analysis:" in output
        assert "Strong innovation" in output


# Test Detailed Formatter
class TestDetailedFormatter:
    """Test detailed formatter."""

    def test_detailed_has_header(self, basic_result):
        """Detailed format should have prominent header."""
        formatter = DetailedFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "MADSPARK MULTI-AGENT IDEA GENERATION RESULTS" in output
        assert "=" * 80 in output

    def test_detailed_strips_numbering_from_idea(self, full_result):
        """Detailed format should strip leading numbers from ideas."""
        formatter = DetailedFormatter()
        output = formatter.format(full_result, Namespace())

        # Original has "1. Original..." but output should strip it
        assert "--- IDEA 1 ---" in output
        assert "Original comprehensive idea" in output
        assert "1. Original comprehensive idea" not in output

    def test_detailed_shows_critique(self, basic_result):
        """Detailed format should show initial critique."""
        formatter = DetailedFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "Initial Critique: Good but needs improvement" in output

    def test_detailed_shows_advocacy(self, full_result):
        """Detailed format should show formatted advocacy section."""
        formatter = DetailedFormatter()
        output = formatter.format(full_result, Namespace())

        # Should contain advocacy data (formatted by output_processor)
        assert "Strong market potential" in output or "Advocacy" in output

    def test_detailed_shows_skepticism(self, full_result):
        """Detailed format should show formatted skepticism section."""
        formatter = DetailedFormatter()
        output = formatter.format(full_result, Namespace())

        # Should contain skepticism data (formatted by output_processor)
        assert "Unclear value proposition" in output or "Skepticism" in output

    def test_detailed_shows_improved_section(self, basic_result):
        """Detailed format should show improved idea section."""
        formatter = DetailedFormatter()
        output = formatter.format(basic_result, Namespace())

        assert "✨ Improved Idea:" in output
        # Note: "Improved" prefix may be cleaned by improved_idea_cleaner
        assert "test idea with enhancements" in output

    def test_detailed_structured_improved_idea(self, structured_improved_result):
        """Detailed format should handle structured improved idea."""
        formatter = DetailedFormatter()
        output = formatter.format(structured_improved_result, Namespace())

        assert "Enhanced Solution Title" in output
        assert "Key Improvements:" in output or "Better performance" in output
        assert "Implementation Steps:" in output or "Step 1: Analysis" in output

    def test_detailed_score_delta_indicators(self, multiple_results):
        """Detailed format should show score delta with arrows."""
        import copy
        # Create a deep copy to avoid modifying the shared fixture
        test_results = copy.deepcopy(multiple_results)
        test_results[1]["score_delta"] = -0.5
        test_results[2]["score_delta"] = 0.0

        formatter = DetailedFormatter()
        output = formatter.format(test_results, Namespace())

        # Should have different indicators for positive, negative, zero
        assert "⬆️  Improvement:" in output or "⬇️  Change:" in output or "➡️  No significant change" in output

    def test_detailed_multi_dimensional_eval(self, full_result):
        """Detailed format should show multi-dimensional evaluation."""
        formatter = DetailedFormatter()
        output = formatter.format(full_result, Namespace())

        # Should show overall score and dimensions
        assert "8.5" in output  # Overall score
        assert "feasibility" in output.lower() or "innovation" in output.lower()

    def test_detailed_logical_inference(self, full_result):
        """Detailed format should show logical inference analysis."""
        formatter = DetailedFormatter()
        output = formatter.format(full_result, Namespace())

        # Should show causal chains or inference header
        assert "Innovation → Market differentiation" in output or "Logical Inference" in output.lower()


# Test Summary Formatter
class TestSummaryFormatter:
    """Test summary formatter."""

    def test_summary_count_header(self, multiple_results):
        """Summary format should show count in header."""
        formatter = SummaryFormatter()
        output = formatter.format(multiple_results, Namespace())

        assert "Generated 3 improved ideas:" in output

    def test_summary_idea_headers(self, multiple_results):
        """Summary format should have headers for each idea."""
        formatter = SummaryFormatter()
        output = formatter.format(multiple_results, Namespace())

        assert "--- IMPROVED IDEA 1 ---" in output
        assert "--- IMPROVED IDEA 2 ---" in output
        assert "--- IMPROVED IDEA 3 ---" in output

    def test_summary_truncates_long_ideas(self):
        """Summary format should truncate ideas longer than 500 chars."""
        long_idea = "A" * 600
        results = [{
            "idea": "Short",
            "improved_idea": long_idea,
            "improved_score": 8.5
        }]

        formatter = SummaryFormatter()
        output = formatter.format(results, Namespace())

        assert "..." in output
        assert "[Note: Full improved idea available in text or JSON format]" in output
        # The output will have additional formatting text, so just check it's truncated
        assert long_idea not in output  # Full idea should not be in output

    def test_summary_shows_dimension_scores(self, full_result):
        """Summary format should show all 7 dimension scores."""
        formatter = SummaryFormatter()
        output = formatter.format(full_result, Namespace())

        # Check for dimension scores (format may vary slightly)
        assert "Feasibility: 0.85" in output
        assert "Innovation: 0.9" in output  # May not have trailing zero
        assert "Impact: 0.88" in output
        assert "Cost-Effectiveness: 0.75" in output
        assert "Scalability: 0.82" in output
        assert "Risk Assessment: 0.3" in output  # May not have trailing zero
        assert "Timeline: 0.8" in output  # May not have trailing zero

    def test_summary_shows_evaluation_summary(self, full_result):
        """Summary format should show evaluation summary."""
        formatter = SummaryFormatter()
        output = formatter.format(full_result, Namespace())

        assert "Summary: Strong innovation with good market fit" in output

    def test_summary_fallback_to_original(self):
        """Summary format should fallback to original if no improved idea."""
        results = [{
            "idea": "Original idea without improvement",
            "initial_score": 7.0
        }]

        formatter = SummaryFormatter()
        output = formatter.format(results, Namespace())

        assert "Original idea without improvement" in output


# Test Formatter Factory
class TestFormatterFactory:
    """Test formatter factory pattern."""

    def test_factory_creates_brief_formatter(self):
        """Factory should create BriefFormatter for 'brief'."""
        formatter = FormatterFactory.create('brief')
        assert isinstance(formatter, BriefFormatter)

    def test_factory_creates_simple_formatter(self):
        """Factory should create SimpleFormatter for 'simple'."""
        formatter = FormatterFactory.create('simple')
        assert isinstance(formatter, SimpleFormatter)

    def test_factory_creates_detailed_formatter(self):
        """Factory should create DetailedFormatter for 'detailed'."""
        formatter = FormatterFactory.create('detailed')
        assert isinstance(formatter, DetailedFormatter)

    def test_factory_creates_summary_formatter(self):
        """Factory should create SummaryFormatter for 'summary'."""
        formatter = FormatterFactory.create('summary')
        assert isinstance(formatter, SummaryFormatter)

    def test_factory_creates_json_formatter(self):
        """Factory should create JsonFormatter for 'json'."""
        formatter = FormatterFactory.create('json')
        assert isinstance(formatter, JsonFormatter)

    def test_factory_handles_text_alias(self):
        """Factory should treat 'text' as alias for detailed."""
        formatter = FormatterFactory.create('text')
        assert isinstance(formatter, DetailedFormatter)

    def test_factory_defaults_to_brief(self):
        """Factory should default to BriefFormatter for unknown formats."""
        formatter = FormatterFactory.create('unknown_format')
        assert isinstance(formatter, BriefFormatter)

    def test_factory_handles_none(self):
        """Factory should default to BriefFormatter for None."""
        formatter = FormatterFactory.create(None)
        assert isinstance(formatter, BriefFormatter)


# Integration Tests
class TestFormatterIntegration:
    """Integration tests for formatter behavior."""

    def test_all_formatters_handle_empty_results(self):
        """All formatters should gracefully handle empty results."""
        formatters = [
            JsonFormatter(),
            BriefFormatter(),
            SimpleFormatter(),
            DetailedFormatter(),
            SummaryFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format([], Namespace())
            assert output is not None
            assert isinstance(output, str)

    def test_all_formatters_handle_minimal_data(self, minimal_result):
        """All formatters should work with minimal data."""
        formatters = [
            JsonFormatter(),
            BriefFormatter(),
            SimpleFormatter(),
            DetailedFormatter(),
            SummaryFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format(minimal_result, Namespace())
            assert output is not None
            assert len(output) > 0
            assert "Test idea" in output or "test idea" in json.loads(output)[0]["idea"]

    def test_formatter_output_consistency(self, basic_result):
        """Formatters should produce consistent output for same input."""
        formatter = BriefFormatter()

        output1 = formatter.format(basic_result, Namespace())
        output2 = formatter.format(basic_result, Namespace())

        assert output1 == output2

    def test_formatters_preserve_unicode(self):
        """All formatters should preserve unicode characters."""
        results = [{
            "idea": "Test émoji 🚀 and spëcial çhars",
            "initial_score": 8.0,
            "improved_idea": "Improved émoji 🎉 text",
            "improved_score": 8.5
        }]

        formatters = [
            BriefFormatter(),
            SimpleFormatter(),
            DetailedFormatter(),
            SummaryFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format(results, Namespace())
            assert "🚀" in output or "🎉" in output
            assert "émoji" in output


# Edge Case Tests
class TestFormatterEdgeCases:
    """Test edge cases and error conditions."""

    def test_missing_optional_fields(self):
        """Formatters should handle missing optional fields gracefully."""
        results = [{"idea": "Minimal", "initial_score": 7.0}]

        formatters = [
            BriefFormatter(),
            SimpleFormatter(),
            DetailedFormatter(),
            SummaryFormatter(),
        ]

        for formatter in formatters:
            output = formatter.format(results, Namespace())
            assert "Minimal" in output
            assert output is not None

    def test_malformed_multi_dimensional_eval(self):
        """Formatters should handle malformed evaluation data."""
        results = [{
            "idea": "Test",
            "initial_score": 7.0,
            "multi_dimensional_evaluation": {
                # Missing dimension_scores
                "overall_score": 8.0
            }
        }]

        formatter = DetailedFormatter()
        output = formatter.format(results, Namespace())
        assert "8.0" in output

    def test_none_values_in_result(self):
        """Formatters should handle None values gracefully."""
        results = [{
            "idea": "Test",
            "initial_score": None,
            "improved_idea": None,
            "improved_score": None
        }]

        formatter = BriefFormatter()
        output = formatter.format(results, Namespace())
        # Check that we show "Test" OR fallback message
        assert "Test" in output or "No idea available" in output

    def test_empty_string_values(self):
        """Formatters should handle empty string values."""
        results = [{
            "idea": "",
            "initial_score": 7.0,
            "improved_idea": "",
            "initial_critique": ""
        }]

        formatter = DetailedFormatter()
        output = formatter.format(results, Namespace())
        assert output is not None


# Section Ordering Tests (regression tests for workflow order)
class TestSectionOrdering:
    """Test that formatters display sections in correct workflow order.

    The workflow executes: Logical Inference (Step 4.5) -> Improvement (Step 5)
    So logical inference should appear BEFORE improved idea in output.
    """

    @pytest.fixture
    def result_with_logical_inference(self) -> List[Dict[str, Any]]:
        """Result with logical inference data for ordering tests."""
        return [{
            "idea": "Original test idea",
            "initial_score": 7.0,
            "initial_critique": "Needs improvement",
            "logical_inference": {
                "causal_chains": ["Step A leads to B", "B enables C"],
                "conclusion": "Therefore the approach is valid"
            },
            "improved_idea": "Improved idea based on logical analysis",
            "improved_score": 8.5,
            "score_delta": 1.5,
        }]

    def test_detailed_logical_before_improved(self, result_with_logical_inference):
        """DetailedFormatter: Logical inference should appear before improved idea."""
        formatter = DetailedFormatter()
        output = formatter.format(result_with_logical_inference, Namespace())

        # Find positions of key sections
        logical_pos = output.find("Logical Inference") if "Logical Inference" in output else output.find("🔍")
        improved_pos = output.find("✨ Improved") if "✨ Improved" in output else output.find("Improved Idea")

        # Both sections should be present
        assert logical_pos != -1, "Logical inference section not found in detailed output"
        assert improved_pos != -1, "Improved idea section not found in detailed output"

        # Logical inference should come before improved idea
        assert logical_pos < improved_pos, \
            f"Logical inference (pos {logical_pos}) should appear before improved idea (pos {improved_pos})"

    def test_simple_logical_before_improved(self, result_with_logical_inference):
        """SimpleFormatter: Logical inference should appear before improved idea."""
        formatter = SimpleFormatter()
        output = formatter.format(result_with_logical_inference, Namespace())

        # Find positions of key sections
        logical_pos = output.find("Logical Reasoning") if "Logical Reasoning" in output else output.find("🧠")
        improved_pos = output.find("✨ Improved") if "✨ Improved" in output else output.find("Improved:")

        # Both sections should be present
        assert logical_pos != -1, "Logical reasoning section not found in simple output"
        assert improved_pos != -1, "Improved idea section not found in simple output"

        # Logical inference should come before improved idea
        assert logical_pos < improved_pos, \
            f"Logical reasoning (pos {logical_pos}) should appear before improved idea (pos {improved_pos})"

    def test_brief_logical_before_solution(self, result_with_logical_inference):
        """BriefFormatter: Logical insight should appear before solution."""
        formatter = BriefFormatter()
        output = formatter.format(result_with_logical_inference, Namespace())

        # Find positions of key sections
        logical_pos = output.find("Logical Insight") if "Logical Insight" in output else output.find("🔍")
        solution_pos = output.find("**Solution:**") if "**Solution:**" in output else output.find("Solution")

        # Both sections should be present
        assert logical_pos != -1, "Logical insight section not found in brief output"
        assert solution_pos != -1, "Solution section not found in brief output"

        # Logical insight should come before solution
        assert logical_pos < solution_pos, \
            f"Logical insight (pos {logical_pos}) should appear before solution (pos {solution_pos})"

    def test_summary_logical_before_improved(self, result_with_logical_inference):
        """SummaryFormatter: Logical inference should appear before improved idea."""
        formatter = SummaryFormatter()
        output = formatter.format(result_with_logical_inference, Namespace())

        # Find positions of key sections
        logical_pos = output.find("Logical Inference") if "Logical Inference" in output else output.find("🔍")
        # In summary, look for the improved idea text or fallback markers
        improved_idea_text = result_with_logical_inference[0]["improved_idea"]
        improved_pos = output.find(improved_idea_text)
        if improved_pos == -1:
            # Try finding partial text
            improved_pos = output.find("Improved idea")
        if improved_pos == -1:
            # Try the Improved Score line which comes after the idea
            improved_pos = output.find("Improved Score:")

        # Both sections should be present
        assert logical_pos != -1, "Logical inference section not found in summary output"
        assert improved_pos != -1, f"Improved idea not found in summary output. Output: {output[:500]}"

        # Logical inference should come before improved idea
        assert logical_pos < improved_pos, \
            f"Logical inference (pos {logical_pos}) should appear before improved idea (pos {improved_pos})"

    def test_all_formatters_include_logical_when_present(self, result_with_logical_inference):
        """All formatters should include logical inference when present in results."""
        formatters = {
            "brief": BriefFormatter(),
            "simple": SimpleFormatter(),
            "detailed": DetailedFormatter(),
            "summary": SummaryFormatter(),
        }

        for name, formatter in formatters.items():
            output = formatter.format(result_with_logical_inference, Namespace())
            # Check that some form of logical inference is present
            has_logical = (
                "Logical" in output or
                "🔍" in output or
                "🧠" in output or
                "causal" in output.lower()
            )
            assert has_logical, f"{name} formatter should include logical inference content"
