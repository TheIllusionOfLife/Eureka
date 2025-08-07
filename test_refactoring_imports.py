#!/usr/bin/env python3
"""Test script to verify refactoring changes work correctly."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_new_modules():
    """Test that new refactoring modules can be imported."""
    try:
        from madspark.utils.import_manager import ImportManager
        from madspark.utils.environment_manager import EnvironmentManager
        from madspark.utils.logging_manager import LoggingManager
        from madspark.utils.validation_decorators import validate_agent_inputs
        print("✓ All new refactoring modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ New module import failed: {e}")
        return False

def test_enhanced_genai_client():
    """Test that enhanced genai_client works with fallback."""
    try:
        from madspark.agents.genai_client import GenAIClientManager, get_genai_client
        print("✓ Enhanced genai_client imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Enhanced genai_client import failed: {e}")
        return False

def test_enhanced_batch_operations():
    """Test that enhanced batch operations work."""
    try:
        from madspark.core.batch_operations_base import BatchOperationsBase
        print("✓ Enhanced batch operations imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Enhanced batch operations import failed: {e}")
        return False

def test_centralized_functionality():
    """Test that centralized functionality works."""
    try:
        from madspark.utils.import_manager import ImportManager
        from madspark.utils.environment_manager import get_environment_manager
        
        # Test import manager
        genai, types, available = ImportManager.get_genai_modules()
        print(f"✓ GenAI available: {available}")
        
        # Test environment manager
        env_manager = get_environment_manager()
        mode = env_manager.get_mode()
        print(f"✓ Operating mode: {mode}")
        
        print("✓ Centralized functionality works")
        return True
    except Exception as e:
        print(f"❌ Centralized functionality test failed: {e}")
        return False

def main():
    """Run all refactoring tests."""
    print("Testing MadSpark Refactoring Changes...")
    print("=" * 50)
    
    tests = [
        test_new_modules,
        test_enhanced_genai_client,
        test_enhanced_batch_operations,
        test_centralized_functionality,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All {total} refactoring tests passed")
        return 0
    else:
        failed = total - passed
        print(f"❌ {failed}/{total} refactoring tests failed")
        return 1

if __name__ == "__main__":
    exit(main())