
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure we can import web.backend.main
sys.path.append(os.path.join(os.getcwd(), "web", "backend"))
sys.path.append(os.path.join(os.getcwd(), "src"))

# Set environment variables BEFORE importing app to avoid mock mode
os.environ["MADSPARK_MODE"] = "production"
os.environ["GOOGLE_API_KEY"] = "valid-key-for-test"
os.environ["ENVIRONMENT"] = "production"

from web.backend.main import app, initialize_components_for_testing
from fastapi.testclient import TestClient

# Initialize components
initialize_components_for_testing()

client = TestClient(app)

SENSITIVE_INFO = "SENSITIVE_DB_PASSWORD_12345"

class TestSecurityErrorHandling:

    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_error_leak(self, MockCoordinator):
        """Test that generate_ideas endpoint does not leak sensitive exception details."""
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

    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_async_error_leak(self, MockCoordinator):
        """Test that generate_ideas_async endpoint does not leak sensitive exception details."""
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
    @patch("web.backend.main.bookmark_system") # Patch the global variable too just in case
    def test_check_bookmark_duplicates_error_leak(self, mock_global_bm, MockBookmarkManagerClass):
        """Test that check_bookmark_duplicates endpoint does not leak sensitive exception details."""

        # When BookmarkManager(...) is called, return a mock that raises exception on check_for_duplicates
        mock_instance = MockBookmarkManagerClass.return_value
        mock_instance.check_for_duplicates.side_effect = ValueError(f"DB Error: {SENSITIVE_INFO}")

        # Also configure the global one just in case code path takes 'else'
        mock_global_bm.check_for_duplicates.side_effect = ValueError(f"DB Error: {SENSITIVE_INFO}")

        response = client.post(
            "/api/bookmarks/check-duplicates",
            json={
                "idea": "test idea long enough",
                "topic": "test topic",
                # similarity_threshold is default 0.8, so it will likely instantiate new BookmarkManager
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
