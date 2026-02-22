import os
import importlib
from unittest.mock import patch
from fastapi.middleware.cors import CORSMiddleware

# We need to import the module to be able to reload it
# Assuming the python path is set up correctly to include the root of the repo
import web.backend.main

def get_cors_middleware(app):
    """Helper to find CORSMiddleware in the app."""
    for middleware in app.user_middleware:
        if middleware.cls == CORSMiddleware:
            return middleware
    return None

def test_default_cors_configuration():
    """Verify that the default CORS configuration is correct."""
    # Ensure MADSPARK_CORS_ORIGINS is not set
    with patch.dict(os.environ, {}, clear=True):
        # We need to reload because the app is created at module level
        importlib.reload(web.backend.main)
        app = web.backend.main.app

        cors_middleware = get_cors_middleware(app)
        assert cors_middleware is not None, "CORSMiddleware not found"

        # In newer Starlette/FastAPI versions, Middleware stores options in kwargs or options
        # Based on previous debug output, it's kwargs
        options = getattr(cors_middleware, "options", getattr(cors_middleware, "kwargs", {}))

        origins = options.get("allow_origins")
        assert origins is not None
        assert "http://localhost:3000" in origins
        assert "http://127.0.0.1:3000" in origins
        assert len(origins) == 2

def test_custom_cors_configuration():
    """Verify that MADSPARK_CORS_ORIGINS env var updates CORS configuration."""
    custom_origins = "https://example.com,https://api.example.com"

    with patch.dict(os.environ, {"MADSPARK_CORS_ORIGINS": custom_origins}):
        importlib.reload(web.backend.main)
        app = web.backend.main.app

        cors_middleware = get_cors_middleware(app)
        assert cors_middleware is not None, "CORSMiddleware not found"

        options = getattr(cors_middleware, "options", getattr(cors_middleware, "kwargs", {}))
        origins = options.get("allow_origins")

        assert origins is not None
        assert "https://example.com" in origins
        assert "https://api.example.com" in origins
        assert len(origins) == 2
        assert "http://localhost:3000" not in origins

def test_custom_cors_configuration_with_whitespace():
    """Verify that whitespace is stripped from MADSPARK_CORS_ORIGINS."""
    custom_origins = " https://example.com ,  https://api.example.com "

    with patch.dict(os.environ, {"MADSPARK_CORS_ORIGINS": custom_origins}):
        importlib.reload(web.backend.main)
        app = web.backend.main.app

        cors_middleware = get_cors_middleware(app)
        assert cors_middleware is not None, "CORSMiddleware not found"

        options = getattr(cors_middleware, "options", getattr(cors_middleware, "kwargs", {}))
        origins = options.get("allow_origins")

        assert origins is not None
        assert "https://example.com" in origins
        assert "https://api.example.com" in origins
        assert len(origins) == 2
