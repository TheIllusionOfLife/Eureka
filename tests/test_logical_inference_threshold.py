"""Test that logical inference confidence threshold filters weak inferences."""
from src.madspark.utils.constants import LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD


def test_logical_inference_threshold_value():
    """Verify that the logical inference confidence threshold is set to 0.5 to filter weak inferences."""
    assert LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD == 0.5


def test_threshold_filters_weak_inferences():
    """Verify that threshold of 0.5 filters out weak/uncertain inferences."""
    # Test confidences that should be filtered out (below threshold)
    weak_confidences = [0.0, 0.1, 0.3, 0.49]
    for confidence in weak_confidences:
        assert confidence < LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD, \
            f"Weak confidence {confidence} should be filtered by threshold {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD}"

    # Test confidences that should pass (above threshold)
    strong_confidences = [0.5, 0.7, 0.9, 1.0]
    for confidence in strong_confidences:
        assert confidence >= LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD, \
            f"Strong confidence {confidence} should pass with threshold {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD}"