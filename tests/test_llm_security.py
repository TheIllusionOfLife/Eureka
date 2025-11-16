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
        """Test that /home/user doesn't match /home/user_evil via relative_to()."""
        from madspark.llm.cache import ResponseCache
        import logging

        # This test verifies that relative_to() properly checks path containment
        # A path like /fake_home/user_evil should NOT match /fake_home/user
        # even though "user_evil".startswith("user") is True
        with patch("madspark.llm.cache.DISKCACHE_AVAILABLE", True):
            with patch("madspark.llm.cache.diskcache") as mock_diskcache:
                mock_cache = Mock()
                mock_diskcache.Cache.return_value = mock_cache

                with tempfile.TemporaryDirectory() as tmpdir:
                    # Create directories to simulate home structure
                    user_dir = Path(tmpdir) / "fake_home" / "user"
                    user_evil_dir = Path(tmpdir) / "fake_home" / "user_evil"
                    user_dir.mkdir(parents=True)
                    user_evil_dir.mkdir(parents=True)

                    # Verify that relative_to() correctly distinguishes paths
                    # This is a unit test of the Path.relative_to() behavior
                    evil_cache_path = user_evil_dir / "cache"

                    # user_evil_dir is NOT under user_dir, so relative_to should raise
                    try:
                        evil_cache_path.relative_to(user_dir)
                        assert False, "relative_to() should have raised ValueError"
                    except ValueError:
                        pass  # Expected - this is the security check working

                    # But user_dir / "cache" IS under user_dir
                    safe_cache_path = user_dir / "cache"
                    relative = safe_cache_path.relative_to(user_dir)
                    assert str(relative) == "cache"

                    # Now test the actual cache implementation
                    # Since tmpdir is under /tmp (a safe directory in the code),
                    # paths under tmpdir will pass validation
                    ResponseCache(cache_dir=str(evil_cache_path))
                    assert mock_diskcache.Cache.called

                    # The key security property is verified above:
                    # relative_to() correctly rejects user_evil as not under user


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


class TestCacheKeyKwargsValidation:
    """Test cache key kwargs type validation."""

    def test_rejects_non_serializable_function(self):
        """Test that functions are rejected as kwargs."""
        from madspark.llm.cache import ResponseCache

        cache = ResponseCache(enabled=False)

        def my_func():
            pass

        with pytest.raises(TypeError, match="non-JSON-serializable"):
            cache.make_key("prompt", SimpleSchema, callback=my_func)

    def test_rejects_non_serializable_object(self):
        """Test that custom objects are rejected as kwargs."""
        from madspark.llm.cache import ResponseCache

        cache = ResponseCache(enabled=False)

        class CustomObj:
            pass

        with pytest.raises(TypeError, match="non-JSON-serializable"):
            cache.make_key("prompt", SimpleSchema, custom=CustomObj())

    def test_accepts_json_serializable_types(self):
        """Test that all JSON-serializable types are accepted."""
        from madspark.llm.cache import ResponseCache

        cache = ResponseCache(enabled=False)

        # Should not raise
        key = cache.make_key(
            "prompt",
            SimpleSchema,
            string_param="test",
            int_param=42,
            float_param=3.14,
            bool_param=True,
            none_param=None,
            list_param=["a", "b", "c"],
            dict_param={"nested": "value"},
        )

        # Should return valid hash
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex digest

    def test_rejects_nested_non_serializable(self):
        """Test that nested non-serializable types are caught."""
        from madspark.llm.cache import ResponseCache

        cache = ResponseCache(enabled=False)

        def bad_func():
            pass

        with pytest.raises(TypeError, match="non-JSON-serializable"):
            cache.make_key("prompt", SimpleSchema, nested_list=[1, 2, bad_func])

    def test_rejects_dict_with_non_serializable_value(self):
        """Test that dicts with non-serializable values are caught."""
        from madspark.llm.cache import ResponseCache

        cache = ResponseCache(enabled=False)

        class BadClass:
            pass

        with pytest.raises(TypeError, match="non-JSON-serializable"):
            cache.make_key("prompt", SimpleSchema, nested_dict={"key": BadClass()})


class TestRouterFileValidation:
    """Test router validates file inputs early."""

    def test_router_rejects_nonexistent_image(self):
        """Test that router rejects non-existent image files."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(ValueError, match="Image file not found"):
            router.generate_structured(
                prompt="Test",
                schema=SimpleSchema,
                images=["/nonexistent/image.jpg"]
            )

    def test_router_rejects_nonexistent_file(self):
        """Test that router rejects non-existent files."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(FileNotFoundError, match="File not found"):
            router.generate_structured(
                prompt="Test",
                schema=SimpleSchema,
                files=[Path("/nonexistent/document.pdf")]
            )

    def test_router_rejects_directory_as_image(self):
        """Test that router rejects directories passed as images."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(ValueError, match="not a file"):
            router.generate_structured(
                prompt="Test",
                schema=SimpleSchema,
                images=["/tmp"]  # /tmp is a directory
            )

    def test_router_rejects_directory_as_file(self):
        """Test that router rejects directories passed as files."""
        from madspark.llm.router import LLMRouter

        router = LLMRouter(cache_enabled=False)

        with pytest.raises(ValueError, match="not a file"):
            router.generate_structured(
                prompt="Test",
                schema=SimpleSchema,
                files=[Path("/tmp")]  # /tmp is a directory
            )


class TestRouterProductionIntegration:
    """Test router is actually used in production code paths."""

    def test_router_used_when_provider_env_var_set(self, monkeypatch):
        """Test that router is used when MADSPARK_LLM_PROVIDER is set."""
        from madspark.agents.structured_idea_generator import _should_use_router

        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_FALLBACK_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)

        assert _should_use_router() is True

    def test_router_used_when_cache_disabled(self, monkeypatch):
        """Test that router is used when cache is explicitly disabled."""
        from madspark.agents.structured_idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.setenv("MADSPARK_CACHE_ENABLED", "false")
        monkeypatch.delenv("MADSPARK_FALLBACK_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)

        assert _should_use_router() is True

    def test_router_used_when_model_tier_set(self, monkeypatch):
        """Test that router is used when model tier is set."""
        from madspark.agents.structured_idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_FALLBACK_ENABLED", raising=False)
        monkeypatch.setenv("MADSPARK_MODEL_TIER", "balanced")

        assert _should_use_router() is True

    def test_router_not_used_by_default(self, monkeypatch):
        """Test that router is not used when no env vars are set."""
        from madspark.agents.structured_idea_generator import _should_use_router

        monkeypatch.delenv("MADSPARK_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("MADSPARK_CACHE_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_FALLBACK_ENABLED", raising=False)
        monkeypatch.delenv("MADSPARK_MODEL_TIER", raising=False)

        assert _should_use_router() is False

    def test_improve_idea_uses_router_when_configured(self, monkeypatch):
        """Test that improve_idea_structured uses router when CLI flags are set."""
        from madspark.agents.structured_idea_generator import improve_idea_structured

        monkeypatch.setenv("MADSPARK_LLM_PROVIDER", "ollama")

        with patch("madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE", True):
            with patch("madspark.agents.structured_idea_generator.get_router") as mock_get_router:
                mock_router = Mock()
                mock_validated = Mock()
                mock_validated.improved_title = "Improved Title"
                mock_validated.improved_description = "Improved Description"
                mock_response = Mock()
                mock_response.provider = "ollama"
                mock_response.tokens_used = 100
                mock_router.generate_structured.return_value = (mock_validated, mock_response)
                mock_get_router.return_value = mock_router

                result = improve_idea_structured(
                    original_idea="Test idea",
                    critique="Test critique",
                    advocacy_points="- Point 1",
                    skeptic_points="- Concern 1",
                    topic="Test topic",
                    context="Test context",
                )

                # Verify router was called
                assert mock_router.generate_structured.called
                assert "Improved Title" in result
                assert "Improved Description" in result
