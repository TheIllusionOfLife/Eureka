"""Tests for constants module."""
from mad_spark_multiagent.constants import (
    ADVOCATE_EMPTY_RESPONSE,
    SKEPTIC_EMPTY_RESPONSE,
    ADVOCATE_FAILED_PLACEHOLDER,
    SKEPTIC_FAILED_PLACEHOLDER,
)


def test_constants_defined():
    """Test that all constants are properly defined."""
    assert ADVOCATE_EMPTY_RESPONSE == "Advocate agent returned no content."
    assert SKEPTIC_EMPTY_RESPONSE == "Skeptic agent returned no content."
    assert ADVOCATE_FAILED_PLACEHOLDER == "AdvocateAgent returned no content."
    assert SKEPTIC_FAILED_PLACEHOLDER == "SkepticAgent returned no content."


def test_constants_different():
    """Test that constants have different values where expected."""
    # Agent response vs coordinator placeholder should be different
    assert ADVOCATE_EMPTY_RESPONSE != ADVOCATE_FAILED_PLACEHOLDER
    assert SKEPTIC_EMPTY_RESPONSE != SKEPTIC_FAILED_PLACEHOLDER
    
    # Different agents should have different messages
    assert ADVOCATE_EMPTY_RESPONSE != SKEPTIC_EMPTY_RESPONSE
    assert ADVOCATE_FAILED_PLACEHOLDER != SKEPTIC_FAILED_PLACEHOLDER