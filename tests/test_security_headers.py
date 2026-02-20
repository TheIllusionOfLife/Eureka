
from fastapi.testclient import TestClient
from web.backend.main import app

client = TestClient(app)

def test_security_headers_present():
    """Test that all required security headers are present in the response."""
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers

    # Check for HSTS (verified fix with preload directive)
    assert "Strict-Transport-Security" in headers, "HSTS header is missing"
    assert headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"

    # Check other headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-XSS-Protection"] == "1; mode=block"
    assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in headers
