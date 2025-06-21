"""Tests for constants module."""
from mad_spark_multiagent.constants import (
    ADVOCATE_EMPTY_RESPONSE,
    SKEPTIC_EMPTY_RESPONSE,
)


def test_constants_defined():
    """Test that all constants are properly defined."""
    assert ADVOCATE_EMPTY_RESPONSE == "Advocate agent returned no content."
    assert SKEPTIC_EMPTY_RESPONSE == "Skeptic agent returned no content."


def test_constants_different():
    """Test that constants have different values where expected."""
    # Different agents should have different messages
    assert ADVOCATE_EMPTY_RESPONSE != SKEPTIC_EMPTY_RESPONSE