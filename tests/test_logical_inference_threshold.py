"""Test that logical inference confidence threshold is set to 0.0."""
from src.madspark.utils.constants import LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD


def test_logical_inference_threshold_is_zero():
    """Verify that the logical inference confidence threshold is set to 0.0."""
    assert LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD == 0.0
    
    
def test_threshold_allows_all_inferences():
    """Verify that threshold of 0.0 allows all confidence levels."""
    # Test various confidence levels
    test_confidences = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    
    for confidence in test_confidences:
        # With threshold of 0.0, all confidences should pass
        assert confidence >= LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD, \
            f"Confidence {confidence} should pass with threshold {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD}"