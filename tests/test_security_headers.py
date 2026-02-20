import os

# Must be set before importing the FastAPI app so the mock rate-limiter is used
os.environ["MADSPARK_MODE"] = "mock"

import pytest
from fastapi.testclient import TestClient
from web.backend.main import app

client = TestClient(app)

_EXPECTED_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "connect-src 'self' ws: wss:;"
)


@pytest.fixture
def root_response():
    """Return the response from GET / (no assertions — setup only)."""
    return client.get("/")


@pytest.fixture
def https_response():
    """Return a response simulated over HTTPS via X-Forwarded-Proto."""
    return client.get("/", headers={"X-Forwarded-Proto": "https"})


def test_root_status_code(root_response):
    """Verify the root endpoint returns HTTP 200."""
    assert root_response.status_code == 200


def test_hsts_header_absent_over_http(root_response):
    """Verify HSTS header is NOT sent for plain HTTP requests."""
    assert "Strict-Transport-Security" not in root_response.headers


def test_hsts_header_present_over_https(https_response):
    """Verify HSTS header is sent for HTTPS requests (without preload by default)."""
    assert "Strict-Transport-Security" in https_response.headers
    assert https_response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"


def test_hsts_preload_enabled_by_env(monkeypatch):
    """Verify preload directive is added only when HSTS_PRELOAD=true."""
    monkeypatch.setenv("HSTS_PRELOAD", "true")
    response = client.get("/", headers={"X-Forwarded-Proto": "https"})
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains; preload"


def test_other_security_headers_present(root_response):
    """Verify all non-HSTS security headers are present with correct values."""
    assert root_response.headers["X-Content-Type-Options"] == "nosniff"
    assert root_response.headers["X-Frame-Options"] == "DENY"
    assert root_response.headers["X-XSS-Protection"] == "1; mode=block"
    assert root_response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert root_response.headers["Content-Security-Policy"] == _EXPECTED_CSP
