"""
Pytest configuration and shared fixtures.

This module provides common test configuration and fixtures used across the test suite.
"""
import os
import pytest


def pytest_configure(config):
    """
    Called at the start of the test session to configure pytest.

    Sets environment variables for consistent test behavior.
    """
    # Disable LLM Router by default to maintain backward compatibility with existing tests.
    # Router-specific tests should explicitly enable router via monkeypatch or environment override.
    # This ensures tests that expect direct Gemini API calls continue to work as before.
    if "MADSPARK_NO_ROUTER" not in os.environ:
        os.environ["MADSPARK_NO_ROUTER"] = "true"


@pytest.fixture
def enable_router(monkeypatch):
    """
    Fixture to enable LLM Router for specific tests.

    Usage:
        def test_router_integration(enable_router):
            # Router is enabled for this test
            pass
    """
    monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
    yield
    # Cleanup happens automatically via monkeypatch


@pytest.fixture
def disable_router(monkeypatch):
    """
    Fixture to explicitly disable LLM Router.

    Usage:
        def test_direct_api(disable_router):
            # Router is disabled for this test
            pass
    """
    monkeypatch.setenv("MADSPARK_NO_ROUTER", "true")
    yield


@pytest.fixture
def set_router_provider(monkeypatch):
    """
    Fixture factory to set specific LLM provider.

    Usage:
        def test_ollama_provider(set_router_provider):
            set_router_provider("ollama")
            # Test with Ollama provider
    """
    def _set_provider(provider: str):
        monkeypatch.delenv("MADSPARK_NO_ROUTER", raising=False)
        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", provider)

    return _set_provider
