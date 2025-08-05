"""Test that logical inference data is preserved in web backend formatting."""
import sys
import os
import pytest

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'backend')
if not os.path.exists(backend_path):
    # Try from root directory (CI environment)
    backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'web', 'backend')
sys.path.insert(0, backend_path)

# Import after path setup - skip if FastAPI not available
try:
    from main import format_results_for_frontend  # noqa: E402
except ImportError:
    pytest.skip("Skipping test - FastAPI not installed", allow_module_level=True)


class TestLogicalInferencePreservation:
    """Test suite for logical inference data preservation."""
    
    def test_logical_inference_preserved_in_formatting(self):
        """Verify that logical_inference data is preserved when formatting for frontend."""
        # Create test data with logical inference
        test_results = [{
            "idea": "Test idea",
            "initial_score": 7.5,
            "improved_idea": "Improved test idea",
            "improved_score": 8.5,
            "logical_inference": {
                "reasoning_type": "full_reasoning",
                "conclusions": [
                    {
                        "statement": "This idea has strong potential",
                        "confidence": 0.8,
                        "supporting_facts": ["Fact 1", "Fact 2"]
                    }
                ],
                "causal_chain": ["A leads to B", "B leads to C"],
                "implications": ["Will improve efficiency", "May reduce costs"]
            }
        }]
        
        # Format the results
        formatted = format_results_for_frontend(test_results)
        
        # Verify logical_inference is preserved
        assert len(formatted) == 1
        assert "logical_inference" in formatted[0], "logical_inference field missing from formatted result"
        assert formatted[0]["logical_inference"] == test_results[0]["logical_inference"]
        
    def test_results_without_logical_inference(self):
        """Verify that results without logical_inference still work correctly."""
        test_results = [{
            "idea": "Test idea",
            "initial_score": 7.5,
            "improved_idea": "Improved test idea",
            "improved_score": 8.5
        }]
        
        # Format the results
        formatted = format_results_for_frontend(test_results)
        
        # Verify basic fields are preserved
        assert len(formatted) == 1
        assert formatted[0]["idea"] == "Test idea"
        assert formatted[0]["initial_score"] == 7.5
        assert "logical_inference" not in formatted[0]
        
    def test_empty_logical_inference(self):
        """Verify that empty logical_inference is handled correctly."""
        test_results = [{
            "idea": "Test idea",
            "initial_score": 7.5,
            "improved_idea": "Improved test idea", 
            "improved_score": 8.5,
            "logical_inference": None
        }]
        
        # Format the results
        formatted = format_results_for_frontend(test_results)
        
        # Verify logical_inference is preserved even if None
        assert len(formatted) == 1
        assert "logical_inference" in formatted[0]
        assert formatted[0]["logical_inference"] is None
        
    def test_multiple_results_with_mixed_logical_inference(self):
        """Test formatting multiple results with different logical inference states."""
        test_results = [
            {
                "idea": "Idea 1",
                "initial_score": 7.0,
                "logical_inference": {"conclusions": ["Test conclusion"]}
            },
            {
                "idea": "Idea 2",
                "initial_score": 8.0,
                # No logical_inference field
            },
            {
                "idea": "Idea 3",
                "initial_score": 6.5,
                "logical_inference": None
            }
        ]
        
        # Format the results
        formatted = format_results_for_frontend(test_results)
        
        # Verify each result
        assert len(formatted) == 3
        assert "logical_inference" in formatted[0]
        assert formatted[0]["logical_inference"] == {"conclusions": ["Test conclusion"]}
        assert "logical_inference" not in formatted[1]
        assert "logical_inference" in formatted[2]
        assert formatted[2]["logical_inference"] is None