"""Tests for mock language detection and response utilities."""
from madspark.utils.mock_language_utils import detect_language, get_mock_response

class TestMockLanguageUtils:
    """Test cases for mock language utilities."""

    def test_detect_language_english_default(self):
        """Test that English is detected as default."""
        assert detect_language("This is an English sentence.") == "en"
        assert detect_language("12345!@#$%") == "en"

    def test_detect_language_japanese(self):
        """Test Japanese language detection."""
        assert detect_language("こんにちは") == "ja"  # Hiragana
        assert detect_language("カタカナ") == "ja"    # Katakana
        assert detect_language("日本語") == "ja"      # Kanji
        assert detect_language("This is Japanese: 日本語") == "ja"

    def test_detect_language_french(self):
        """Test French language detection."""
        assert detect_language("C'est l'été") == "fr"
        assert detect_language("Où est le café?") == "fr"
        assert detect_language("Noël approche") == "fr"

    def test_detect_language_spanish(self):
        """Test Spanish language detection."""
        assert detect_language("¿Cómo estás?") == "es"
        assert detect_language("El niño corre") == "es"
        assert detect_language("Acción y reacción") == "es"

    def test_detect_language_german(self):
        """Test German language detection."""
        assert detect_language("Guten Übergang") == "de"
        assert detect_language("Schön, dich zu sehen") == "de"
        assert detect_language("Fußball ist toll") == "de"

    def test_detect_language_edge_cases(self):
        """Test edge cases for language detection."""
        assert detect_language("") == "en"
        assert detect_language("   ") == "en"

    def test_detect_language_priority(self):
        """Test language detection priority (German/Spanish take precedence over French)."""
        # Japanese + German characters -> should return 'ja' because it's checked first
        assert detect_language("日本語 Fußball") == "ja"
        # German + French characters -> should return 'de' because it's checked before French
        assert detect_language("Guten Übergang C'est l'été") == "de"
        # Spanish + French characters -> should return 'es' because it's checked before French
        assert detect_language("Acción C'est l'été") == "es"

    def test_get_mock_response_advocate(self):
        """Test mock response for advocate agent in different languages."""
        # English
        resp_en = get_mock_response("advocate", "Hello")
        assert "STRENGTHS" in resp_en

        # Japanese
        resp_ja = get_mock_response("advocate", "こんにちは")
        assert "強み" in resp_ja

        # French
        resp_fr = get_mock_response("advocate", "C'est l'été")
        assert "FORCES" in resp_fr

        # Spanish
        resp_es = get_mock_response("advocate", "Acción")
        assert "FORTALEZAS" in resp_es

        # German
        resp_de = get_mock_response("advocate", "Fußball")
        assert "STÄRKEN" in resp_de

    def test_get_mock_response_skeptic(self):
        """Test mock response for skeptic agent in different languages."""
        # English
        resp_en = get_mock_response("skeptic", "Hello")
        assert "CRITICAL FLAWS" in resp_en

        # Japanese
        resp_ja = get_mock_response("skeptic", "こんにちは")
        assert "重大な欠陥" in resp_ja

    def test_get_mock_response_fallback(self):
        """Test fallback behavior for get_mock_response."""
        # Unknown agent type -> should return default mock response or agent-generic default
        # Looking at implementation:
        # agent_templates = MOCK_RESPONSES.get(agent_type, {})
        # return agent_templates.get(language, agent_templates.get('en', 'Mock response'))
        resp = get_mock_response("unknown_agent", "Hello")
        assert resp == "Mock response"

        # Supported agent but unsupported language detection
        # (Though detect_language currently always returns one of the supported ones or 'en')
        # If we had a language not in MOCK_RESPONSES for an agent, it would fallback to 'en'.
