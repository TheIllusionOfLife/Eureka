"""Debug bookmark API issues."""
from fastapi.testclient import TestClient
import os

# Force mock mode
os.environ["MADSPARK_MODE"] = "mock"

# Import after setting env
import sys
sys.path.insert(0, 'web/backend')
from main import app

client = TestClient(app)

# Test minimal bookmark creation
bookmark_data = {
    "idea": "Test idea for bookmarking",
    "topic": "test topic",  # Using new field name
    "context": "test context",  # Using new field name
    "initial_score": 7.5
}

print("Testing bookmark creation with minimal data and new field names...")
response = client.post("/api/bookmarks", json=bookmark_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Try with old field names
bookmark_data_old = {
    "idea": "Test idea for bookmarking 2",
    "theme": "test theme",  # Using old field name
    "constraints": "test constraints",  # Using old field name  
    "initial_score": 7.5
}

print("\nTesting bookmark creation with minimal data and old field names...")
response = client.post("/api/bookmarks", json=bookmark_data_old)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")