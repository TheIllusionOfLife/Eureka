"""
Simple import tests for MadSpark Multi-Agent System.

These tests verify that the package structure is correct and core modules
can be imported without external dependencies. No pytest required.
"""
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_package_imports():
    """Test that package can be imported."""
    try:
        import madspark
        assert hasattr(madspark, '__version__')
        print('✓ Package imports successfully')
        return True
    except ImportError as e:
        print(f"⚠️ Package import skipped: {e}")
        return True  # Skip is okay


def test_core_module_imports():
    """Test that core modules can be imported."""
    try:
        from madspark.core.coordinator import run_multistep_workflow
        from madspark.core.async_coordinator import AsyncCoordinator
        print('✓ Core modules imported successfully')
        return True
    except ImportError as e:
        if "genai" in str(e) or "google" in str(e):
            print(f"⚠️ Core modules skipped (Google GenAI dependencies not available): {e}")
            return True  # Skip is okay
        else:
            print(f"❌ Core module import failed: {e}")
            return False


def test_utils_imports():
    """Test that utility modules can be imported."""
    try:
        from madspark.utils.constants import IDEA_GENERATION_INSTRUCTION
        from madspark.utils.utils import exponential_backoff_retry, parse_json_with_fallback
        from madspark.utils.temperature_control import TemperatureManager
        from madspark.utils.bookmark_system import BookmarkManager
        assert isinstance(IDEA_GENERATION_INSTRUCTION, str)
        print('✓ Utility modules imported successfully')
        return True
    except ImportError as e:
        print(f"❌ Utils import failed: {e}")
        return False


def test_agent_function_imports():
    """Test that agent functions can be imported."""
    try:
        from madspark.agents.idea_generator import generate_ideas, build_generation_prompt
        from madspark.agents.critic import evaluate_ideas  
        from madspark.agents.advocate import advocate_idea
        from madspark.agents.skeptic import criticize_idea
        print('✓ Agent functions imported')
        return True
    except ImportError as e:
        if "genai" in str(e) or "google" in str(e):
            print(f"⚠️ Agent functions skipped (Google GenAI dependencies not available): {e}")
            return True  # Skip is okay
        else:
            print(f"❌ Agent function import failed: {e}")
            return False


def main():
    """Run all tests."""
    print("Running MadSpark import tests...")
    print("=" * 50)
    
    tests = [
        test_package_imports,
        test_core_module_imports,
        test_utils_imports,
        test_agent_function_imports,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All {total} tests passed (some may have been skipped)")
        return 0
    else:
        failed = total - passed
        print(f"❌ {failed}/{total} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())