"""
Tests for LLM provider CLI integration.

Tests the CLI flags for --provider, --model-tier, --no-cache, etc.
"""

import os
from unittest.mock import patch, Mock
import argparse
import pytest


@pytest.fixture(autouse=True)
def clean_llm_env_vars():
    """
    Automatically clean up LLM-related environment variables after each test.

    This prevents environment pollution between tests when _configure_llm_provider
    mutates os.environ globally. Saves and restores the original state explicitly.
    """
    # List of env vars to track
    env_vars = [
        'MADSPARK_LLM_PROVIDER',
        'MADSPARK_MODEL_TIER',
        'MADSPARK_FALLBACK_ENABLED',
        'MADSPARK_CACHE_ENABLED',
    ]

    # Store original values before test
    original_values = {}
    for var in env_vars:
        if var in os.environ:
            original_values[var] = os.environ[var]
        else:
            original_values[var] = None
        # Remove from environment to start clean
        os.environ.pop(var, None)

    # Yield control to the test
    yield

    # Cleanup: Restore original state after test completes
    # This handles both cases:
    # 1. Var was set before test -> restore original value
    # 2. Var was not set before test -> remove it
    for var in env_vars:
        if original_values[var] is not None:
            os.environ[var] = original_values[var]
        else:
            os.environ.pop(var, None)


class TestCLIProviderConfiguration:
    """Test _configure_llm_provider function."""

    def test_provider_flag_sets_env_var(self, monkeypatch):
        """Test that --provider flag sets environment variable."""
        from madspark.cli.cli import _configure_llm_provider

        # No need to mock sys.argv - we just check if args.provider is not None
        args = argparse.Namespace(
            provider='ollama',
            model_tier=None,
            no_fallback=False,
            no_cache=False,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger') as mock_logger:
            _configure_llm_provider(args)

        assert os.environ.get('MADSPARK_LLM_PROVIDER') == 'ollama'
        # Should log info about router configuration
        mock_logger.info.assert_called_once()
        assert 'Router is enabled' in str(mock_logger.info.call_args)

    def test_model_tier_flag_sets_env_var(self, monkeypatch):
        """Test that --model-tier flag sets environment variable."""
        from madspark.cli.cli import _configure_llm_provider

        # No need to mock sys.argv - we just check if args.model_tier is not None
        args = argparse.Namespace(
            provider=None,
            model_tier='balanced',
            no_fallback=False,
            no_cache=False,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger'):
            _configure_llm_provider(args)

        assert os.environ.get('MADSPARK_MODEL_TIER') == 'balanced'

    def test_no_fallback_flag_sets_env_var(self, monkeypatch):
        """Test that --no-fallback flag sets environment variable."""
        from madspark.cli.cli import _configure_llm_provider

        # Clean environment before test
        monkeypatch.delenv('MADSPARK_FALLBACK_ENABLED', raising=False)

        args = argparse.Namespace(
            provider=None,
            model_tier=None,
            no_fallback=True,
            no_cache=False,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger'):
            _configure_llm_provider(args)

        assert os.environ.get('MADSPARK_FALLBACK_ENABLED') == 'false'

    def test_no_cache_flag_sets_env_var(self, monkeypatch):
        """Test that --no-cache flag sets environment variable."""
        from madspark.cli.cli import _configure_llm_provider

        # Clean environment before test
        monkeypatch.delenv('MADSPARK_CACHE_ENABLED', raising=False)

        args = argparse.Namespace(
            provider=None,
            model_tier=None,
            no_fallback=False,
            no_cache=True,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger'):
            _configure_llm_provider(args)

        assert os.environ.get('MADSPARK_CACHE_ENABLED') == 'false'

    def test_no_flags_no_warning(self, monkeypatch):
        """Test that no warning is issued when no provider flags are used."""
        from madspark.cli.cli import _configure_llm_provider

        # Ensure clean environment state
        monkeypatch.delenv('MADSPARK_LLM_PROVIDER', raising=False)
        monkeypatch.delenv('MADSPARK_MODEL_TIER', raising=False)
        monkeypatch.delenv('MADSPARK_FALLBACK_ENABLED', raising=False)
        monkeypatch.delenv('MADSPARK_CACHE_ENABLED', raising=False)

        args = argparse.Namespace(
            provider=None,
            model_tier=None,
            no_fallback=False,
            no_cache=False,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger') as mock_logger:
            _configure_llm_provider(args)

        # No warning should be issued
        mock_logger.warning.assert_not_called()

    def test_multiple_flags_combined_info(self, monkeypatch):
        """Test that multiple flags are listed in the info message."""
        from madspark.cli.cli import _configure_llm_provider

        # No need to mock sys.argv - we just check if args values are not None
        args = argparse.Namespace(
            provider='gemini',
            model_tier='quality',
            no_fallback=True,
            no_cache=False,
            clear_cache=False
        )

        with patch('madspark.cli.cli.logger') as mock_logger:
            _configure_llm_provider(args)

        # Should log info about multiple flags
        call_args = str(mock_logger.info.call_args)
        assert '--provider gemini' in call_args
        assert '--model-tier quality' in call_args
        assert '--no-fallback' in call_args


class TestShowLLMStats:
    """Test _show_llm_stats function."""

    def test_stats_show_zero_request_warning(self, capsys):
        """Test that warning is shown when router has zero requests."""
        from madspark.cli.cli import _show_llm_stats

        mock_router = Mock()
        mock_router.get_metrics.return_value = {
            'total_requests': 0,
            'ollama_calls': 0,
            'gemini_calls': 0,
            'cache_hits': 0,
            'fallback_triggers': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'cache_hit_rate': 0.0,
            'avg_latency_ms': 0.0,
        }

        mock_cache = Mock()
        mock_cache.enabled = False

        # Patch at the import location inside the function
        with patch('madspark.llm.get_router', return_value=mock_router):
            with patch('madspark.llm.get_cache', return_value=mock_cache):
                _show_llm_stats()

        output = capsys.readouterr().out
        assert 'LLM Router was not used' in output
        assert 'Phase 2' in output
        assert 'direct Gemini API calls' in output

    def test_stats_show_metrics_when_used(self, capsys):
        """Test that metrics are shown without warning when router is used."""
        from madspark.cli.cli import _show_llm_stats

        mock_router = Mock()
        mock_router.get_metrics.return_value = {
            'total_requests': 10,
            'ollama_calls': 8,
            'gemini_calls': 2,
            'cache_hits': 3,
            'fallback_triggers': 1,
            'total_tokens': 500,
            'total_cost': 0.0001,
            'cache_hit_rate': 0.3,
            'avg_latency_ms': 150.0,
        }

        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.stats.return_value = {
            'size': 10,
            'volume': 1024,
        }

        with patch('madspark.llm.get_router', return_value=mock_router):
            with patch('madspark.llm.get_cache', return_value=mock_cache):
                _show_llm_stats()

        output = capsys.readouterr().out
        # Should NOT show the warning
        assert 'LLM Router was not used' not in output
        # Should show actual metrics
        assert 'Total Requests: 10' in output
        assert 'Ollama Calls: 8' in output
        assert 'Gemini Calls: 2' in output
        assert 'Cache Hits: 3' in output

    def test_stats_handles_import_error(self, capsys):
        """Test graceful handling when LLM module is not available."""
        from madspark.cli.cli import _show_llm_stats

        # Simulate ImportError by patching the import itself
        import madspark.llm as llm_module

        def raise_import_error():
            raise ImportError("Module not found")

        with patch.object(llm_module, 'get_router', side_effect=raise_import_error):
            _show_llm_stats()

        output = capsys.readouterr().out
        assert 'not available' in output or output == ''


class TestClearCache:
    """Test cache clearing functionality."""

    def test_clear_cache_when_enabled(self, capsys):
        """Test that cache is cleared when enabled."""
        from madspark.cli.cli import _configure_llm_provider

        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.clear.return_value = True

        args = argparse.Namespace(
            provider=None,
            model_tier=None,
            no_fallback=False,
            no_cache=False,
            clear_cache=True
        )

        # Patch at the madspark.llm module level (where it's imported from)
        with patch('madspark.llm.get_cache', return_value=mock_cache):
            with patch('madspark.cli.cli.logger'):
                _configure_llm_provider(args)

        mock_cache.clear.assert_called_once()
        output = capsys.readouterr().out
        assert 'cache cleared' in output

    def test_clear_cache_when_disabled(self, capsys):
        """Test that message is shown when cache is disabled."""
        from madspark.cli.cli import _configure_llm_provider

        mock_cache = Mock()
        mock_cache.enabled = False

        args = argparse.Namespace(
            provider=None,
            model_tier=None,
            no_fallback=False,
            no_cache=False,
            clear_cache=True
        )

        with patch('madspark.llm.get_cache', return_value=mock_cache):
            with patch('madspark.cli.cli.logger'):
                _configure_llm_provider(args)

        mock_cache.clear.assert_not_called()
        output = capsys.readouterr().out
        assert 'disabled' in output
