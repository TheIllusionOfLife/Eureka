"""Tests for logical inference formatting bug fix."""
from madspark.utils.output_processor import format_logical_inference_results


class TestLogicalInferenceFormatting:
    """Test cases for logical inference formatting."""
    
    def test_recommendations_as_string_single_line(self):
        """Test handling when improvements is a string (single line)."""
        inference_results = {
            "inference_chain": ["Step 1", "Step 2"],
            "improvements": "**Clarify Single-Button Mechanic:** Provide a concrete example"
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should NOT have character-by-character output
        # Check that we don't have single character lines
        lines = result.split('\n')
        for line in lines:
            if line.strip().startswith('• ') and len(line.strip()) == 3:
                # Found a single character recommendation, which is the bug
                assert False, f"Found single character recommendation: {line}"
        
        # Should have the full recommendation
        assert "• **Clarify Single-Button Mechanic:** Provide a concrete example" in result
    
    def test_recommendations_as_string_multiline(self):
        """Test handling when improvements is a multiline string."""
        inference_results = {
            "inference_chain": ["Step 1", "Step 2"],
            "improvements": """**Clarify Single-Button Mechanic:** Provide a concrete example of how the single button controls both movement and attack timing.
**Specify Procedural Generation:** Suggest a simplified method for procedural generation.
**Define Strategic Depth:** Elaborate on how strategy is achieved with one button."""
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should have properly formatted recommendations
        assert "└─ Recommendations:" in result
        assert "   • **Clarify Single-Button Mechanic:** Provide a concrete example" in result
        assert "   • **Specify Procedural Generation:** Suggest a simplified method" in result
        assert "   • **Define Strategic Depth:** Elaborate on how strategy is achieved" in result
        
        # Should NOT have character-by-character output  
        # Check for single character lines which indicate the bug
        lines = result.split('\n')
        for line in lines:
            if line.strip().startswith('• ') and len(line.strip()) == 3:
                # Found a single character recommendation, which is the bug
                assert False, f"Found single character recommendation: {line}"
    
    def test_recommendations_as_list(self):
        """Test handling when improvements is already a list (backward compatibility)."""
        inference_results = {
            "inference_chain": ["Step 1", "Step 2"],
            "improvements": [
                "**Clarify Single-Button Mechanic:** Provide a concrete example",
                "**Specify Procedural Generation:** Suggest a simplified method",
                "**Define Strategic Depth:** Elaborate on how strategy is achieved"
            ]
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should work correctly with list format
        assert "└─ Recommendations:" in result
        assert "   • **Clarify Single-Button Mechanic:** Provide a concrete example" in result
        assert "   • **Specify Procedural Generation:** Suggest a simplified method" in result
        assert "   • **Define Strategic Depth:** Elaborate on how strategy is achieved" in result
    
    def test_empty_improvements_string(self):
        """Test handling empty improvements string."""
        inference_results = {
            "inference_chain": ["Step 1"],
            "improvements": ""
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should not show recommendations section for empty string
        assert "└─ Recommendations:" not in result
    
    def test_whitespace_only_improvements(self):
        """Test handling whitespace-only improvements."""
        inference_results = {
            "inference_chain": ["Step 1"],
            "improvements": "   \n   \n   "
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should not show recommendations section for whitespace-only
        assert "└─ Recommendations:" not in result
    
    def test_improvements_with_bullet_points(self):
        """Test handling improvements that already have bullet points."""
        inference_results = {
            "inference_chain": ["Step 1"],
            "improvements": """• First improvement
• Second improvement
• Third improvement"""
        }
        
        result = format_logical_inference_results(inference_results)
        
        # Should handle existing bullet points gracefully
        assert "└─ Recommendations:" in result
        assert "   • First improvement" in result
        assert "   • Second improvement" in result
        assert "   • Third improvement" in result
        
    def test_conclusion_fallback(self):
        """Test that conclusion is shown when no improvements."""
        inference_results = {
            "inference_chain": ["Step 1", "Step 2"],
            "conclusion": "The idea is logically sound and feasible."
        }
        
        result = format_logical_inference_results(inference_results)
        
        assert "└─ Conclusion:" in result
        assert "   The idea is logically sound and feasible." in result