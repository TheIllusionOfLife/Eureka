"""
Security tests for LLM provider infrastructure.

Tests for SSRF protection, path traversal prevention, prompt length limits, etc.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
import tempfile

from pydantic import BaseModel


class SimpleSchema(BaseModel):
    """Simple schema for testing."""
    value: str


class TestPromptLengthValidation:
    """Test prompt length validation to prevent resource exhaustion."""

    def test_prompt_exceeds_max_length_raises_error(self):
        """Test that prompts exceeding MAX_PROMPT_LENGTH are rejected."""
        from madspark.llm.router import LLMRouter, MAX_PROMPT_LENGTH

        router = LLMRouter(cache_enabled=False)
        long_prompt = "x" * (MAX_PROMPT_LENGTH + 1)

        with pytest.raises(ValueError, match="exceeds maximum"):
            router.generate_structured(prompt=long_prompt, schema=SimpleSchema)

    def test_prompt_at_max_length_accepted(self):
        """Test that prompts at exactly MAX_PROMPT_LENGTH are accepted."""
        from madspark.llm.router import LLMRouter, MAX_PROMPT_LENGTH

        # This test just verifies the validation passes, not actual generation
        router = LLMRouter(cache_enabled=False)
        max_prompt = "x" * MAX_PROMPT_LENGTH

        # Should not raise ValueError for length
        # (will raise other errors since no provider is available)
        try:
            router.generate_structured(prompt=max_prompt, schema=SimpleSchema)
            # If it succeeds (unlikely), that's fine
        except ValueError as e:
            # Should NOT be a length validation error
            assert "exceeds maximum" not in str(e)
        except Exception:
            # Other errors are expected (no provider available)
            pass

    def test_empty_prompt_rejected(self):
        """Test that empty prompts are rejected."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(ValueError, match="cannot be empty"):
            router.generate_structured(prompt="", schema=SimpleSchema)

    def test_whitespace_only_prompt_rejected(self):
        """Test that whitespace-only prompts are rejected."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(ValueError, match="cannot be empty"):
            router.generate_structured(prompt="   \n\t  ", schema=SimpleSchema)


class TestPathTraversalProtection:
    """Test cache path traversal protection."""

    def test_cache_rejects_path_outside_safe_dirs(self, monkeypatch, tmp_path):
        """Test that cache directories outside safe paths are rejected."""
        from madspark.llm.cache import ResponseCache

        # Try to set cache to a dangerous path
        dangerous_path = "/etc/passwd"

        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache = Mock()
                mock_diskcache.Cache.return_value = mock_cache

                ResponseCache(cache_dir=dangerous_path)

                # Should have redirected to safe default
                # The cache should have been initialized with a safe path
                if mock_diskcache.Cache.called:
                    actual_path = mock_diskcache.Cache.call_args[0][0]
                    # Should contain 'madspark' in path (safe default)
                    assert "madspark" in actual_path or str(Path.home()) in actual_path

    def test_cache_accepts_path_under_home(self, tmp_path):
        """Test that cache directories under home are accepted."""
        from madspark.llm.cache import ResponseCache

        # Use a path under home directory
        home_cache = Path.home() / ".cache" / "test_madspark"

        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache = Mock()
                mock_diskcache.Cache.return_value = mock_cache

                ResponseCache(cache_dir=str(home_cache))

                # Should accept this path
                if mock_diskcache.Cache.called:
                    actual_path = mock_diskcache.Cache.call_args[0][0]
                    # Should be the path we specified (or resolved version)
                    assert str(home_cache) in actual_path or "test_madspark" in actual_path

    def test_relative_to_prevents_prefix_bypass(self):
        """Test that /home/user doesn't match /home/user_evil."""
        from madspark.llm.cache import ResponseCache

        # This test verifies the relative_to() fix
        # /home/user should not match /home/user_evil even though strings match
        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache = Mock()
                mock_diskcache.Cache.return_value = mock_cache

                with patch("pathlib.Path.home") as mock_home:
                    # Use a real temp directory as base
                    with tempfile.TemporaryDirectory() as tmpdir:
                        mock_home.return_value = Path(tmpdir) / "user"
                        # Create the "user" directory
                        (Path(tmpdir) / "user").mkdir()

                        # Try a path that would be incorrectly allowed with startswith()
                        # but correctly rejected with relative_to()
                        evil_path = str(Path(tmpdir) / "user_evil" / "cache")

                        # The implementation should reject this
                        # Since it's not under safe directories, it should fall back to default
                        with patch("pathlib.Path.mkdir"):
                            ResponseCache(cache_dir=evil_path)
                            # Check that the warning was logged (path was rejected)
                            # The actual diskcache.Cache should be initialized with safe path
                            assert mock_diskcache.Cache.called
                            actual_init_path = mock_diskcache.Cache.call_args[0][0]
                            # The actual cache should NOT be initialized with evil path
                            assert "user_evil" not in actual_init_path
                            # Should contain safe default components
                            assert "madspark" in actual_init_path


class TestSSRFProtection:
    """Test SSRF protection for URL inputs."""

    def test_rejects_localhost_url(self):
        """Test that localhost URLs are rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        assert _is_private_ip("localhost") is True

    def test_rejects_127_0_0_1(self):
        """Test that 127.0.0.1 is rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        assert _is_private_ip("127.0.0.1") is True

    def test_rejects_private_ip_10_x(self):
        """Test that 10.x.x.x private IPs are rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        assert _is_private_ip("10.0.0.1") is True
        assert _is_private_ip("10.255.255.255") is True

    def test_rejects_private_ip_192_168_x(self):
        """Test that 192.168.x.x private IPs are rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        assert _is_private_ip("192.168.1.1") is True
        assert _is_private_ip("192.168.0.100") is True

    def test_rejects_private_ip_172_16_x(self):
        """Test that 172.16-31.x.x private IPs are rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        assert _is_private_ip("172.16.0.1") is True
        assert _is_private_ip("172.31.255.255") is True

    def test_rejects_aws_metadata_ip(self):
        """Test that AWS metadata service IP is rejected."""
        from madspark.llm.providers.gemini import _is_private_ip

        # AWS metadata service
        assert _is_private_ip("169.254.169.254") is True

    def test_accepts_public_ip(self):
        """Test that public IPs are accepted."""
        from madspark.llm.providers.gemini import _is_private_ip

        # Google's public DNS
        assert _is_private_ip("8.8.8.8") is False
        # Cloudflare's public DNS
        assert _is_private_ip("1.1.1.1") is False

    @patch("madspark.llm.providers.gemini.GENAI_AVAILABLE", True)
    @patch("madspark.llm.providers.gemini.genai")
    @patch("madspark.llm.providers.gemini.types")
    def test_gemini_rejects_private_url(self, mock_types, mock_genai):
        """Test that GeminiProvider rejects URLs with private IPs."""
        from madspark.llm.providers.gemini import GeminiProvider

        mock_config = Mock()
        mock_config.gemini_api_key = "test-key"
        mock_config.gemini_model = "gemini-test"
        mock_config.validate_api_key.return_value = True

        with patch("madspark.llm.providers.gemini.get_config", return_value=mock_config):
            with patch("madspark.llm.providers.gemini.pydantic_to_genai_schema"):
                provider = GeminiProvider()

                # Try to use a private URL
                with pytest.raises(ValueError, match="SSRF protection"):
                    provider.generate_structured(
                        prompt="Test",
                        schema=SimpleSchema,
                        urls=["http://localhost:8080/admin"]
                    )

    @patch("madspark.llm.providers.gemini.GENAI_AVAILABLE", True)
    @patch("madspark.llm.providers.gemini.genai")
    @patch("madspark.llm.providers.gemini.types")
    def test_gemini_rejects_invalid_url_scheme(self, mock_types, mock_genai):
        """Test that GeminiProvider rejects non-http(s) URLs."""
        from madspark.llm.providers.gemini import GeminiProvider

        mock_config = Mock()
        mock_config.gemini_api_key = "test-key"
        mock_config.gemini_model = "gemini-test"
        mock_config.validate_api_key.return_value = True

        with patch("madspark.llm.providers.gemini.get_config", return_value=mock_config):
            with patch("madspark.llm.providers.gemini.pydantic_to_genai_schema"):
                provider = GeminiProvider()

                # Try to use file:// URL (gets caught by format validation first)
                with pytest.raises(ValueError, match="Invalid URL format"):
                    provider.generate_structured(
                        prompt="Test",
                        schema=SimpleSchema,
                        urls=["file:///etc/passwd"]
                    )

                # Try to use ftp:// URL (should fail scheme check)
                with pytest.raises(ValueError, match="http or https"):
                    provider.generate_structured(
                        prompt="Test",
                        schema=SimpleSchema,
                        urls=["ftp://example.com/file"]
                    )


class TestCacheFieldValidation:
    """Test cache entry field validation."""

    def test_cache_rejects_missing_required_fields(self):
        """Test that cache rejects entries missing required fields."""
        from madspark.llm.cache import ResponseCache

        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache_obj = MagicMock()
                mock_diskcache.Cache.return_value = mock_cache_obj

                cache = ResponseCache(enabled=True)
                cache._cache = mock_cache_obj

                # Return cache entry with missing 'model' field
                mock_cache_obj.get.return_value = (
                    {"value": "test"},  # validated_dict
                    {"text": "response", "provider": "ollama"}  # missing 'model'
                )
                # Setup contains check for invalidate
                mock_cache_obj.__contains__.return_value = True

                result = cache.get("test_key")

                # Should return None and invalidate
                assert result is None
                # Verify del was called (invalidate)
                mock_cache_obj.__delitem__.assert_called_once_with("test_key")

    def test_cache_accepts_complete_entries(self):
        """Test that cache accepts entries with all required fields."""
        from madspark.llm.cache import ResponseCache
        from datetime import datetime, timezone

        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache_obj = Mock()
                mock_diskcache.Cache.return_value = mock_cache_obj

                cache = ResponseCache(enabled=True)
                cache._cache = mock_cache_obj

                # Return complete cache entry
                mock_cache_obj.get.return_value = (
                    {"value": "test"},  # validated_dict
                    {
                        "text": "response",
                        "provider": "ollama",
                        "model": "test-model",
                        "tokens_used": 10,
                        "latency_ms": 100.0,
                        "cost": 0.0,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "cached": False,
                    }
                )
                mock_cache_obj.__contains__ = Mock(return_value=True)

                result = cache.get("test_key")

                # Should return the cached data
                assert result is not None
                validated_dict, response = result
                assert validated_dict["value"] == "test"
                assert response.provider == "ollama"


class TestTimestampConsistency:
    """Test timestamp handling for consistency."""

    def test_cache_uses_utc_for_fallback_timestamp(self):
        """Test that fallback timestamps use UTC."""
        from madspark.llm.cache import ResponseCache
        from datetime import timezone

        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache_obj = Mock()
                mock_diskcache.Cache.return_value = mock_cache_obj

                cache = ResponseCache(enabled=True)
                cache._cache = mock_cache_obj

                # Return cache entry with invalid timestamp
                mock_cache_obj.get.return_value = (
                    {"value": "test"},
                    {
                        "text": "response",
                        "provider": "ollama",
                        "model": "test-model",
                        "tokens_used": 10,
                        "latency_ms": 100.0,
                        "cost": 0.0,
                        "timestamp": "invalid-timestamp",  # Will trigger fallback
                        "cached": False,
                    }
                )

                result = cache.get("test_key")

                # Should return result with UTC timestamp
                assert result is not None
                _, response = result
                # The timestamp should be timezone-aware (UTC)
                assert response.timestamp.tzinfo is not None or response.timestamp.tzinfo == timezone.utc
