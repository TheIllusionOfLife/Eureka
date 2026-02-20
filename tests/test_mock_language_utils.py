"""Tests for mock language detection and response utilities."""
import os
import pytest

os.environ.setdefault("MADSPARK_MODE", "mock")

try:
    from madspark.utils.mock_language_utils import detect_language, get_mock_response
except ImportError:
    from utils.mock_language_utils import detect_language, get_mock_response  # type: ignore[no-redef]


class TestMockLanguageUtils:
    """Test cases for mock language utilities."""

    @pytest.fixture(autouse=True)
    def set_mock_mode(self, monkeypatch):
        """Ensure MADSPARK_MODE=mock for every test in this class."""
        monkeypatch.setenv("MADSPARK_MODE", "mock")

    @pytest.mark.parametrize("text, expected_lang", [
        # English (default)
        ("This is an English sentence.", "en"),
        ("12345!@#$%", "en"),
        # Japanese
        ("こんにちは", "ja"),                    # Hiragana
        ("カタカナ", "ja"),                      # Katakana
        ("日本語", "ja"),                        # Kanji
        ("This is Japanese: 日本語", "ja"),
        # French
        ("C'est l'été", "fr"),
        ("Où est le café?", "fr"),
        ("Noël approche", "fr"),
        # Spanish
        ("¿Cómo estás?", "es"),
        ("El niño corre", "es"),
        ("Acción y reacción", "es"),
        # German
        ("Guten Übergang", "de"),
        ("Schön, dich zu sehen", "de"),
        ("Fußball ist toll", "de"),
        # Edge cases
        ("", "en"),
        ("   ", "en"),
    ])
    def test_detect_language(self, text, expected_lang):
        """Test language detection for various texts.

        Detection priority: Japanese > German > Spanish > French > English.
        """
        assert detect_language(text) == expected_lang

    def test_detect_language_priority(self):
        """Test that higher-priority languages win in mixed-language text."""
        # Japanese outranks German
        assert detect_language("日本語 Fußball") == "ja"
        # German outranks French
        assert detect_language("Guten Übergang C'est l'été") == "de"
        # Spanish outranks French
        assert detect_language("Acción C'est l'été") == "es"

    def test_get_mock_response_advocate(self):
        """Test mock response for advocate agent in all supported languages."""
        assert "STRENGTHS" in get_mock_response("advocate", "Hello")
        assert "強み" in get_mock_response("advocate", "こんにちは")
        assert "FORCES" in get_mock_response("advocate", "C'est l'été")
        assert "FORTALEZAS" in get_mock_response("advocate", "Acción")
        assert "STÄRKEN" in get_mock_response("advocate", "Fußball")

    def test_get_mock_response_skeptic(self):
        """Test mock response for skeptic agent in all supported languages."""
        assert "CRITICAL FLAWS" in get_mock_response("skeptic", "Hello")
        assert "重大な欠陥" in get_mock_response("skeptic", "こんにちは")
        assert "DÉFAUTS CRITIQUES" in get_mock_response("skeptic", "C'est l'été")
        assert "DEFECTOS CRÍTICOS" in get_mock_response("skeptic", "Acción")
        assert "KRITISCHE MÄNGEL" in get_mock_response("skeptic", "Fußball")

    def test_get_mock_response_fallback(self):
        """Test that unknown agent type returns the generic fallback string."""
        assert get_mock_response("unknown_agent", "Hello") == "Mock response"
