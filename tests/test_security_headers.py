import pytest
from fastapi.testclient import TestClient
from web.backend.main import app

client = TestClient(app)


@pytest.fixture
def root_response():
    response = client.get("/")
    assert response.status_code == 200
    return response


def test_hsts_header_present(root_response):
    """Verify that Strict-Transport-Security header is present with preload."""
    assert "Strict-Transport-Security" in root_response.headers
    assert root_response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"


def test_other_security_headers_present(root_response):
    """Verify other security headers are present."""
    assert root_response.headers["X-Content-Type-Options"] == "nosniff"
    assert root_response.headers["X-Frame-Options"] == "DENY"
    assert root_response.headers["X-XSS-Protection"] == "1; mode=block"
