"""Debug bookmark field alias issue."""
from fastapi.testclient import TestClient
import os
import sys
import json

# Add web backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web', 'backend'))

# Force mock mode
os.environ["MADSPARK_MODE"] = "mock"

# Import after setting env
from main import app, initialize_components_for_testing

# Initialize components
initialize_components_for_testing()

client = TestClient(app)

# Test with new field names
bookmark_data_new = {
    "idea": "Test idea",
    "topic": "test topic",  # New field name
    "context": "test context",  # New field name
    "initial_score": 7.0
}

print("Testing bookmark creation with new field names (topic/context)...")
response = client.post("/api/bookmarks", json=bookmark_data_new)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error details: {json.dumps(response.json(), indent=2)}")
else:
    print(f"Success: {response.json()}")

# Test mixed field names
bookmark_data_mixed = {
    "idea": "Test idea 3",
    "topic": "test topic",  # New field name
    "constraints": "test constraints",  # Old field name 
    "initial_score": 7.2
}

print("\nTesting bookmark creation with mixed field names...")
response = client.post("/api/bookmarks", json=bookmark_data_mixed)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error details: {json.dumps(response.json(), indent=2)}")
else:
    print(f"Success: {response.json()}")