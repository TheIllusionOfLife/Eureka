#!/usr/bin/env python3
"""
Test script to verify OpenAPI documentation is working correctly
"""
import requests
import sys

def test_openapi_docs():
    """Test that OpenAPI documentation endpoints are accessible"""
    base_url = "http://localhost:8000"
    
    print("Testing OpenAPI documentation endpoints...")
    
    # Test OpenAPI JSON endpoint
    print("\n1. Testing OpenAPI JSON endpoint...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            print("✅ OpenAPI JSON endpoint is accessible")
            openapi_spec = response.json()
            print(f"   - API Title: {openapi_spec.get('info', {}).get('title', 'N/A')}")
            print(f"   - API Version: {openapi_spec.get('info', {}).get('version', 'N/A')}")
            print(f"   - Number of endpoints: {len(openapi_spec.get('paths', {}))}")
            print(f"   - Tags: {[tag['name'] for tag in openapi_spec.get('tags', [])]}")
        else:
            print(f"❌ OpenAPI JSON endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing OpenAPI JSON: {e}")
        return False
    
    # Test Swagger UI
    print("\n2. Testing Swagger UI...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ Swagger UI is accessible at /docs")
        else:
            print(f"❌ Swagger UI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing Swagger UI: {e}")
        return False
    
    # Test ReDoc
    print("\n3. Testing ReDoc...")
    try:
        response = requests.get(f"{base_url}/redoc")
        if response.status_code == 200:
            print("✅ ReDoc is accessible at /redoc")
        else:
            print(f"❌ ReDoc returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing ReDoc: {e}")
        return False
    
    print("\n✅ All OpenAPI documentation endpoints are working correctly!")
    print("\nYou can access:")
    print(f"  - Swagger UI: {base_url}/docs")
    print(f"  - ReDoc: {base_url}/redoc")
    print(f"  - OpenAPI JSON: {base_url}/openapi.json")
    
    return True

if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("You can start it with: cd web/backend && python main.py")
    print()
    
    success = test_openapi_docs()
    sys.exit(0 if success else 1)