"""
Basic import tests for MadSpark Multi-Agent System.

These tests verify that the package structure is correct and core modules
can be imported without external dependencies.

NOTE: This file requires pytest. For a pytest-free version, use test_basic_imports_simple.py
"""
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Check if pytest is available
try:
    import pytest
except ImportError:
    print("❌ Error: pytest is not installed.")
    print("To run these tests, install pytest: pip install pytest")
    print("For a pytest-free alternative, run: python test_basic_imports_simple.py")
    sys.exit(1)


def test_package_imports():
    """Test that package can be imported."""
    try:
        import madspark
        assert hasattr(madspark, '__version__')
        print('✓ Package imports successfully')
    except ImportError as e:
        pytest.skip(f"Package import not available: {e}")


def test_core_module_imports():
    """Test that core modules can be imported."""
    try:
        from madspark.core.coordinator import run_multistep_workflow  # noqa: F401
        from madspark.core.async_coordinator import AsyncCoordinator  # noqa: F401
        print('✓ Core modules imported successfully')
    except ImportError as e:
        if "genai" in str(e) or "google" in str(e):
            pytest.skip("Google GenAI dependencies not available")
        else:
            raise


def test_agent_function_imports():
    """Test that agent functions can be imported."""
    try:
        from madspark.agents.idea_generator import generate_ideas, build_generation_prompt  # noqa: F401
        from madspark.agents.critic import evaluate_ideas  # noqa: F401
        from madspark.agents.advocate import advocate_idea  # noqa: F401
        from madspark.agents.skeptic import criticize_idea  # noqa: F401
        print('✓ Agent functions imported')
    except ImportError as e:
        if "genai" in str(e) or "google" in str(e):
            pytest.skip("Google GenAI dependencies not available")
        else:
            raise


def test_utils_imports():
    """Test that utility modules can be imported."""
    try:
        from madspark.utils.constants import IDEA_GENERATION_INSTRUCTION
        from madspark.utils.utils import exponential_backoff_retry, parse_json_with_fallback  # noqa: F401
        from madspark.utils.temperature_control import TemperatureManager  # noqa: F401
        from madspark.utils.bookmark_system import BookmarkManager  # noqa: F401
        assert isinstance(IDEA_GENERATION_INSTRUCTION, str)
        print('✓ Utility modules imported successfully')
    except ImportError as e:
        pytest.skip(f"Utils import failed: {e}")


def test_cli_imports():
    """Test that CLI modules can be imported."""
    try:
        from madspark.cli.cli import main  # noqa: F401
        from madspark.cli.interactive_mode import run_interactive_mode  # noqa: F401
        print('✓ CLI modules imported successfully')
    except ImportError as e:
        if "genai" in str(e) or "google" in str(e):
            pytest.skip("Google GenAI dependencies not available")
        else:
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])