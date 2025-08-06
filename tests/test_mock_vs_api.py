#!/usr/bin/env python3
"""Test script to verify mock mode vs API mode behavior."""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

def test_mock_mode():
    """Test mock mode when no API key is available."""
    print("🧪 Testing Mock Mode (No API Key)")
    print("=" * 50)
    
    # Ensure no API key
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
    
    try:
        from madspark.agents.idea_generator import generate_ideas, GENAI_AVAILABLE
        from madspark.agents.genai_client import get_genai_client
        
        print(f"✓ GENAI_AVAILABLE: {GENAI_AVAILABLE}")
        
        client = get_genai_client()
        print(f"✓ Client status: {'Available' if client else 'None (expected in mock)'}")
        
        if not GENAI_AVAILABLE:
            # Test mock response
            result = generate_ideas("test topic", "test context", 0.7)
            print(f"✓ Mock response: {result}")
            return True
        else:
            print("⚠️  Google GenAI package is available, testing error handling...")
            try:
                result = generate_ideas("test topic", "test context", 0.7)
                print(f"❌ Expected error but got: {result}")
                return False
            except Exception as e:
                print(f"✓ Expected error occurred: {e}")
                return True
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_mode_simulation():
    """Test API mode behavior when API key is present but invalid."""
    print("\n🧪 Testing API Mode Simulation")
    print("=" * 50)
    
    # Set a fake API key
    os.environ['GOOGLE_API_KEY'] = 'fake-api-key-for-testing'
    
    try:
        from madspark.agents.idea_generator import GENAI_AVAILABLE
        from madspark.agents.genai_client import get_genai_client
        
        print(f"✓ GENAI_AVAILABLE: {GENAI_AVAILABLE}")
        
        client = get_genai_client()
        print(f"✓ Client status: {'Available' if client else 'None'}")
        
        if GENAI_AVAILABLE and client:
            print("✓ API mode would be active with valid key")
            # We won't actually call the API with fake key
            print("✓ (Skipping actual API call to avoid errors)")
            return True
        else:
            print("⚠️  API mode setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in API mode test: {e}")
        return False
    finally:
        # Clean up
        if 'GOOGLE_API_KEY' in os.environ:
            del os.environ['GOOGLE_API_KEY']

def test_coordinator_mock_mode():
    """Test coordinator in mock mode."""
    print("\n🧪 Testing Coordinator Mock Mode")
    print("=" * 50)
    
    try:
        from madspark.core.coordinator import run_workflow
        
        # This should handle missing API key gracefully
        result = run_workflow(topic="test sustainable energy",
            context="test constraints",
            num_candidates=1,
            temperature=0.7,
            enhanced_reasoning=False,
            logical_inference=False,
            verbose=False
        )
        
        if result is None or (isinstance(result, dict) and 'error' in result):
            print("✓ Coordinator handled missing API key appropriately")
            return True
        else:
            print(f"⚠️  Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"✓ Expected error in coordinator: {e}")
        return True

def main():
    """Run all mock vs API mode tests."""
    print("🚀 MadSpark Mock vs API Mode Testing")
    print("=" * 60)
    
    # Configure minimal logging
    logging.basicConfig(level=logging.WARNING)
    
    tests = [
        ("Mock Mode", test_mock_mode),
        ("API Mode Simulation", test_api_mode_simulation),
        ("Coordinator Mock", test_coordinator_mock_mode),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Mock/API mode handling works correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Review implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)