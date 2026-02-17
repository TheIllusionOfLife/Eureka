import pytest
from fastapi.testclient import TestClient
from web.backend.main import app

client = TestClient(app)

def test_hsts_header_present():
    """Verify that Strict-Transport-Security header is present."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Strict-Transport-Security" in response.headers
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"

def test_other_security_headers_present():
    """Verify other security headers are present."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
