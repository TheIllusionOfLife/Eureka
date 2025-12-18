"""
Test constants for consistent model naming across tests.

This module provides constants that can be imported by test files.
Use these instead of hardcoding model names to make tests resilient to model upgrades.
"""

# Generic test model name - use for mocks where the exact name doesn't matter
TEST_MODEL_NAME = "gemini-test-model"

# Import the actual default model for tests that need it
try:
    from madspark.llm.models import GEMINI_MODEL_DEFAULT
except ImportError:
    GEMINI_MODEL_DEFAULT = "gemini-3-flash-preview"
