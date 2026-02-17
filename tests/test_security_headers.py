
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add web/backend to sys.path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../web/backend')))
# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from main import app

client = TestClient(app)

def test_security_headers_present():
    """Test that all required security headers are present in the response."""
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers

    # Check for HSTS (currently missing, expecting this to fail)
    assert "Strict-Transport-Security" in headers, "HSTS header is missing"
    assert headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"

    # Check other headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in headers
