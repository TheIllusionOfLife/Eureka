
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure we can import web.backend.main
sys.path.append(os.path.join(os.getcwd(), "web", "backend"))
sys.path.append(os.path.join(os.getcwd(), "src"))

from web.backend.main import app, initialize_components_for_testing
from fastapi.testclient import TestClient

# Initialize components (this might log errors about missing files, ignore them)
initialize_components_for_testing()

client = TestClient(app)

SENSITIVE_INFO = "SENSITIVE_DB_PASSWORD_12345"

class TestSecurityErrorHandling:

    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_error_leak(self, MockCoordinator):
        """Test that generate_ideas endpoint does not leak sensitive exception details."""
        # Force production mode to ensure we don't hit the mock path
        # We need to set these env vars so parse_idea_request doesn't trigger mock mode
        env_vars = {
            "MADSPARK_MODE": "production",
            "ENVIRONMENT": "production",
            "GOOGLE_API_KEY": "valid-key-for-test"
        }

        with patch.dict(os.environ, env_vars):
            mock_instance = MockCoordinator.return_value

            async def side_effect(*args, **kwargs):
                raise ValueError(f"Connection failed: {SENSITIVE_INFO}")

            mock_instance.run_workflow.side_effect = side_effect

            response = client.post(
                "/api/generate-ideas",
                json={
                    "topic": "test",
                    "context": "test context",
                    "num_top_candidates": 1
                }
            )

            assert response.status_code == 500
            data = response.json()

            detail = data.get("detail", {})
            if isinstance(detail, dict):
                error_msg = detail.get("error", "")
                assert SENSITIVE_INFO not in error_msg
                assert error_msg == "An internal error occurred during idea generation."
                assert detail.get("type") == "InternalServerError"
            else:
                pytest.fail(f"Unexpected detail format: {detail}")

    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_async_error_leak(self, MockCoordinator):
        """Test that generate_ideas_async endpoint does not leak sensitive exception details."""
        env_vars = {
            "MADSPARK_MODE": "production",
            "ENVIRONMENT": "production",
            "GOOGLE_API_KEY": "valid-key-for-test"
        }

        with patch.dict(os.environ, env_vars):
            mock_instance = MockCoordinator.return_value

            async def side_effect(*args, **kwargs):
                raise ValueError(f"Connection failed: {SENSITIVE_INFO}")

            mock_instance.run_workflow.side_effect = side_effect

            response = client.post(
                "/api/generate-ideas-async",
                json={
                    "topic": "test",
                    "context": "test context",
                    "num_top_candidates": 1
                }
            )

            assert response.status_code == 500
            data = response.json()

            detail = data.get("detail", "")
            assert SENSITIVE_INFO not in str(detail)
            assert detail == "An internal error occurred."

    @patch("web.backend.main.BookmarkManager")
    def test_check_bookmark_duplicates_error_leak(self, MockBookmarkManagerClass):
        """Test that check_bookmark_duplicates endpoint does not leak sensitive exception details."""

        # Configure the mock instance returned by the class constructor
        mock_instance = MockBookmarkManagerClass.return_value
        # Configure the method to raise exception
        mock_instance.check_for_duplicates.side_effect = ValueError(f"DB Error: {SENSITIVE_INFO}")

        # Ensure we are using the patched class.
        # Note: If duplicate_request.similarity_threshold is set (default 0.8),
        # main.py instantiates BookmarkManager().

        response = client.post(
            "/api/bookmarks/check-duplicates",
            json={
                "idea": "test idea long enough",
                "topic": "test topic"
            }
        )

        assert response.status_code == 500
        data = response.json()

        detail = data.get("detail", "")
        assert SENSITIVE_INFO not in str(detail)
        assert detail == "Internal server error"

    @patch("web.backend.main.TemperatureManager")
    def test_get_temperature_presets_error_leak(self, MockTempManager):
        """Test that get_temperature_presets endpoint does not leak sensitive exception details."""
        # Mocking items on the class attribute PRESETS
        mock_presets = MagicMock()
        mock_presets.items.side_effect = ValueError(f"Config Error: {SENSITIVE_INFO}")
        MockTempManager.PRESETS = mock_presets

        response = client.get("/api/temperature-presets")

        assert response.status_code == 500
        data = response.json()

        detail = data.get("detail", "")
        assert SENSITIVE_INFO not in str(detail)
        assert detail == "Internal server error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
