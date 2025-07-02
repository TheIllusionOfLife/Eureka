"""Test configuration and fixtures for MadSpark tests."""
import pytest
import os
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_genai_model():
    """Mock Google GenerativeAI model for testing."""
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Test response from mocked model"
    mock_model.generate_content.return_value = mock_response
    return mock_model


@pytest.fixture
def mock_adk_agent():
    """Mock ADK agent for testing."""
    mock_agent = Mock()
    mock_response = Mock()
    mock_response.content = "Test response from mocked ADK agent"
    mock_agent.invoke.return_value = mock_response
    return mock_agent


@pytest.fixture
def sample_theme():
    """Sample theme for testing."""
    return "未来の移動手段"


@pytest.fixture
def sample_constraints():
    """Sample constraints for testing."""
    return {"mode": "逆転", "random_words": ["猫", "宇宙船"]}


@pytest.fixture
def sample_ideas():
    """Sample ideas for testing."""
    return [
        "猫型宇宙船で空を飛ぶ移動手段",
        "宇宙船の中で猫と一緒に移動するシステム", 
        "猫の動きを真似た逆転発想の宇宙船",
        "重力を逆転させて猫のように軽やかに移動",
        "猫の感覚を使った宇宙船ナビゲーション"
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
    monkeypatch.setenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")


@pytest.fixture(autouse=True)
def clean_imports():
    """Clean imports to avoid module caching issues."""
    import sys
    modules_to_remove = [
        'agent_defs.idea_generator',
        'agent_defs.critic', 
        'agent_defs.advocate',
        'agent_defs.skeptic',
        'coordinator'
    ]
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    yield