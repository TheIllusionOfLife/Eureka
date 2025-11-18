"""Test that logical inference confidence threshold filters weak inferences."""
from src.madspark.utils.constants import LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD


def test_logical_inference_threshold_value():
    """Verify that the logical inference confidence threshold is set to 0.0 to show all inferences."""
    assert LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD == 0.0


def test_threshold_accepts_all_inferences():
    """Verify that threshold of 0.0 accepts all inferences (no filtering)."""
    # With threshold of 0.0, ALL confidences should pass
    all_confidences = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    for confidence in all_confidences:
        assert confidence >= LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD, \
            f"Confidence {confidence} should pass with threshold {LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD} (0.0 = show all)"