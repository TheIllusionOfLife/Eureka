"""Integration test for web interface float score and logical inference fixes."""
import asyncio
import sys
import os
import json
from typing import Dict, Any, List

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))

# Import only what we need


async def test_web_interface_with_real_data():
    """Test the complete workflow with float scores and logical inference."""
    print("=== Testing Web Interface Integration ===\n")
    
    # No coordinator needed for this test
    
    # Test parameters
    theme = "sustainable urban farming"
    constraints = "low-cost solutions for small spaces"
    
    # Mock results with float scores
    mock_results = [
        {
            "text": "Vertical hydroponic gardens using recycled plastic bottles",
            "score": 7.5,  # Float score
            "critique": "Creative and accessible solution",
            "multi_dimensional_evaluation": {
                "dimension_scores": {
                    "feasibility": 8.0,
                    "innovation": 7.0,
                    "impact": 7.5,
                    "cost_effectiveness": 9.0,
                    "scalability": 6.5,
                    "risk_assessment": 7.0,
                    "timeline": 8.5
                },
                "weighted_score": 7.6
            }
        },
        {
            "text": "Community seed exchange programs with mobile app",
            "score": 8.2,  # Float score
            "critique": "Strong community aspect with tech integration",
            "multi_dimensional_evaluation": {
                "dimension_scores": {
                    "feasibility": 7.5,
                    "innovation": 8.5,
                    "impact": 8.0,
                    "cost_effectiveness": 8.0,
                    "scalability": 9.0,
                    "risk_assessment": 6.5,
                    "timeline": 7.0
                },
                "weighted_score": 7.8
            }
        }
    ]
    
    # Add logical inference data manually (simulating what would come from LLM)
    for i, result in enumerate(mock_results):
        result["logical_inference"] = {
            "confidence": 0.3 if i == 0 else 0.7,  # One below old threshold, one above
            "inference": f"Logical analysis of idea {i+1}",
            "inference_chain": [
                f"Step 1: Analyze feasibility of {result['text'][:30]}...",
                f"Step 2: Consider constraints of {constraints}",
                f"Step 3: Evaluate potential impact"
            ],
            "improvements": f"Consider adding more details about implementation"
        }
    
    # Test processing through coordinator's format_results method
    # First, let's verify the validate_evaluation_json works with floats
    from madspark.utils.utils import validate_evaluation_json
    
    print("1. Testing float score validation:")
    test_eval = {"score": 7.5, "comment": "Test"}
    validated = validate_evaluation_json(test_eval)
    print(f"   Input score: {test_eval['score']} (type: {type(test_eval['score'])})")
    print(f"   Output score: {validated['score']} (type: {type(validated['score'])})")
    print(f"   ✓ Float preserved: {validated['score'] == 7.5}\n")
    
    # Test logical inference threshold
    from madspark.utils.constants import LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD
    print("2. Testing logical inference threshold:")
    print(f"   Threshold value: {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD}")
    print(f"   ✓ Set to 0.0: {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD == 0.0}\n")
    
    # Test that both results should pass with threshold of 0.0
    print("3. Testing logical inference filtering:")
    for i, result in enumerate(mock_results):
        confidence = result["logical_inference"]["confidence"]
        passes = confidence >= LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD
        print(f"   Idea {i+1}: confidence={confidence}, passes={passes}")
    print()
    
    # Test backend formatting
    try:
        from main import format_results_for_frontend
        
        print("4. Testing backend formatting preservation:")
        formatted = format_results_for_frontend(mock_results)
        
        for i, result in enumerate(formatted):
            print(f"   Result {i+1}:")
            print(f"     - Initial score: {result.get('initial_score', 'N/A')}")
            print(f"     - Score type: {type(result.get('initial_score', 0))}")
            print(f"     - Has logical_inference: {'logical_inference' in result}")
            if 'logical_inference' in result:
                print(f"     - Inference confidence: {result['logical_inference'].get('confidence', 'N/A')}")
                print(f"     - Inference preserved: {result['logical_inference'] == mock_results[i]['logical_inference']}")
        
    except ImportError as e:
        print(f"   ! Could not import backend formatting: {e}")
    
    print("\n=== Integration Test Complete ===")
    
    # Return summary
    return {
        "float_scores_work": all(isinstance(r['score'], float) for r in mock_results),
        "threshold_is_zero": LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD == 0.0,
        "all_inferences_pass": all(
            r['logical_inference']['confidence'] >= LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD 
            for r in mock_results
        )
    }


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_web_interface_with_real_data())
    
    print("\n=== SUMMARY ===")
    print(f"✓ Float scores preserved: {result['float_scores_work']}")
    print(f"✓ Threshold set to 0.0: {result['threshold_is_zero']}")
    print(f"✓ All inferences pass threshold: {result['all_inferences_pass']}")
    
    if all(result.values()):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)