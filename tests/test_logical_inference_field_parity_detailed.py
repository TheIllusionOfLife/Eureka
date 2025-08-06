"""Detailed test to identify exact field differences between mock and production modes.

This test will help us understand what fields need to be added for parity.
"""
import pytest
from unittest.mock import Mock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.core.enhanced_reasoning import LogicalInference
from madspark.utils.logical_inference_engine import InferenceType


def test_detailed_field_comparison():
    """Compare fields in detail between mock and production modes."""
    # Production mode with LLM
    mock_client = Mock()
    mock_response = Mock()
    mock_response.text = """INFERENCE_CHAIN:
- [Step 1]: Initial premise leads to intermediate conclusion
- [Step 2]: Intermediate conclusion combined with second premise
- [Step 3]: Final logical deduction reached

CONCLUSION: The logical analysis shows that the premises lead to a valid conclusion through proper reasoning steps.

CONFIDENCE: 0.85

IMPROVEMENTS: Consider adding more specific evidence to strengthen the logical chain."""
    
    mock_client.models.generate_content.return_value = mock_response
    
    prod_inference = LogicalInference(genai_client=mock_client)
    prod_result = prod_inference.build_inference_chain(
        premises=["All humans are mortal", "Socrates is human", "Therefore, Socrates is mortal"],
        theme="Classical logic",
        context="Syllogism demonstration"
    )
    
    # Mock mode without LLM (fallback to rule-based)
    mock_inference = LogicalInference(genai_client=None)
    mock_result = mock_inference.build_inference_chain(
        premises=["All humans are mortal", "Socrates is human", "Therefore, Socrates is mortal"],
        theme="Classical logic",
        context="Syllogism demonstration"
    )
    
    print("\n=== PRODUCTION MODE FIELDS ===")
    for key, value in prod_result.items():
        if key == 'inference_result' and hasattr(value, 'to_dict'):
            print(f"  {key}: InferenceResult object with fields:")
            for field, val in value.to_dict().items():
                print(f"    - {field}: {type(val).__name__} = {str(val)[:50]}...")
        else:
            print(f"  {key}: {type(value).__name__} = {str(value)[:50]}...")
    
    print("\n=== MOCK MODE FIELDS ===")
    for key, value in mock_result.items():
        print(f"  {key}: {type(value).__name__} = {str(value)[:50]}...")
    
    print("\n=== FIELD DIFFERENCES ===")
    prod_fields = set(prod_result.keys())
    mock_fields = set(mock_result.keys())
    
    print(f"Fields only in production: {prod_fields - mock_fields}")
    print(f"Fields only in mock: {mock_fields - prod_fields}")
    print(f"Common fields: {prod_fields & mock_fields}")
    
    # Check if production has rich InferenceResult
    if 'inference_result' in prod_result:
        result_obj = prod_result['inference_result']
        if hasattr(result_obj, 'to_dict'):
            result_fields = set(result_obj.to_dict().keys())
            print(f"\nInferenceResult object fields in production: {result_fields}")
            
            # These are the rich fields that mock mode is missing
            expected_rich_fields = {
                'inference_chain', 'conclusion', 'confidence', 'improvements',
                'causal_chain', 'feedback_loops', 'root_cause',
                'constraint_satisfaction', 'overall_satisfaction', 'trade_offs',
                'contradictions', 'resolution', 'implications', 'second_order_effects'
            }
            
            available_rich_fields = result_fields & expected_rich_fields
            print(f"Rich fields available in production: {available_rich_fields}")
            print(f"Rich fields that could be added: {expected_rich_fields - result_fields}")


if __name__ == "__main__":
    test_detailed_field_comparison()