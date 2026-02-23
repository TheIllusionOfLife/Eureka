import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure we can import web.backend.main
sys.path.append(os.path.join(os.getcwd(), "web", "backend"))
sys.path.append(os.path.join(os.getcwd(), "src"))

from web.backend.main import app, error_tracker, initialize_components_for_testing

SENSITIVE_INFO = "SENSITIVE_DB_PASSWORD_12345"


@pytest.fixture
def test_client():
    initialize_components_for_testing()
    with patch.dict(
        os.environ,
        {
            "MADSPARK_MODE": "mock",
            "ENVIRONMENT": "test",
            "GOOGLE_API_KEY": "test-key",
        },
        clear=False,
    ):
        yield TestClient(app)


class TestSecurityErrorHandling:
    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_error_leak(self, MockCoordinator, test_client):
        """Test that generate_ideas endpoint does not leak sensitive exception details."""
        mock_instance = MockCoordinator.return_value
        mock_instance.run_workflow = AsyncMock(
            side_effect=ValueError(f"Connection failed: {SENSITIVE_INFO}")
        )

        with patch("web.backend.main._is_mock_mode", return_value=False):
            response = test_client.post(
                "/api/generate-ideas",
                json={
                    "topic": "test",
                    "context": "test context",
                    "num_top_candidates": 1,
                },
            )

        assert response.status_code == 500
        detail = response.json().get("detail", {})
        assert isinstance(detail, dict)
        assert detail.get("error") == "An internal error occurred during idea generation."
        assert detail.get("type") == "InternalServerError"
        assert SENSITIVE_INFO not in str(detail)

    @patch("web.backend.main.AsyncCoordinator")
    def test_generate_ideas_async_error_leak(self, MockCoordinator, test_client):
        """Test that generate_ideas_async endpoint does not leak sensitive exception details."""
        mock_instance = MockCoordinator.return_value
        mock_instance.run_workflow = AsyncMock(
            side_effect=ValueError(f"Connection failed: {SENSITIVE_INFO}")
        )

        with patch("web.backend.main._is_mock_mode", return_value=False):
            response = test_client.post(
                "/api/generate-ideas-async",
                json={
                    "topic": "test",
                    "context": "test context",
                    "num_top_candidates": 1,
                },
            )

        assert response.status_code == 500
        detail = response.json().get("detail", "")
        assert detail == "An internal error occurred."
        assert SENSITIVE_INFO not in detail

    @patch("web.backend.main.BookmarkManager")
    def test_check_bookmark_duplicates_error_leak(
        self, MockBookmarkManagerClass, test_client
    ):
        """Test that check_bookmark_duplicates endpoint does not leak sensitive exception details."""
        mock_instance = MockBookmarkManagerClass.return_value
        mock_instance.check_for_duplicates.side_effect = ValueError(
            f"DB Error: {SENSITIVE_INFO}"
        )

        response = test_client.post(
            "/api/bookmarks/check-duplicates",
            json={"idea": "test idea long enough", "topic": "test topic"},
        )

        assert response.status_code == 500
        detail = response.json().get("detail", "")
        assert detail == "Internal server error"
        assert SENSITIVE_INFO not in detail

    @patch("web.backend.main.TemperatureManager")
    def test_get_temperature_presets_error_leak(self, MockTempManager, test_client):
        """Test that get_temperature_presets endpoint does not leak sensitive exception details."""
        mock_presets = MagicMock()
        mock_presets.items.side_effect = ValueError(f"Config Error: {SENSITIVE_INFO}")
        MockTempManager.PRESETS = mock_presets

        response = test_client.get("/api/temperature-presets")

        assert response.status_code == 500
        detail = response.json().get("detail", "")
        assert detail == "Internal server error"
        assert SENSITIVE_INFO not in detail

    @patch("web.backend.main.bookmark_system")
    def test_delete_bookmark_not_found_stays_404(self, mock_bookmark_system, test_client):
        """Test that missing bookmarks return 404 rather than being converted to 500."""
        mock_bookmark_system.remove_bookmark.return_value = False

        response = test_client.delete("/api/bookmarks/non-existent-id")

        assert response.status_code == 404
        detail = response.json().get("detail", "")
        assert "not found" in detail.lower()

    def test_error_stats_redacts_sensitive_messages(self, test_client):
        """Test that /api/system/errors redacts exception message content."""
        original_errors = list(error_tracker.errors)
        try:
            error_tracker.errors = []
            error_tracker.track_error(
                "test_security_error",
                f"Connection string leaked: {SENSITIVE_INFO}",
                {"source": "test"},
            )

            response = test_client.get("/api/system/errors")

            assert response.status_code == 200
            payload = response.json()
            recent_errors = payload["error_stats"]["recent_errors"]
            assert recent_errors
            assert recent_errors[0]["message"] == "[REDACTED]"
            assert SENSITIVE_INFO not in str(recent_errors[0])
        finally:
            error_tracker.errors = original_errors
