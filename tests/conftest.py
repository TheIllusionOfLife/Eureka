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
    # Enable mock mode for all tests to prevent actual API calls in CI.
    # Individual tests can override via monkeypatch if needed.
    if "MADSPARK_MODE" not in os.environ:
        os.environ["MADSPARK_MODE"] = "mock"

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


@pytest.fixture
def mock_mode(monkeypatch):
    """
    Fixture to explicitly enable mock mode.

    Usage:
        def test_with_mocks(mock_mode):
            # MADSPARK_MODE=mock is set for this test
            pass
    """
    monkeypatch.setenv("MADSPARK_MODE", "mock")
    yield


@pytest.fixture
def real_mode(monkeypatch):
    """
    Fixture to disable mock mode for integration tests.

    Usage:
        @pytest.mark.integration
        def test_real_api(real_mode):
            # MADSPARK_MODE is unset/not mock for this test
            pass
    """
    monkeypatch.delenv("MADSPARK_MODE", raising=False)
    yield
