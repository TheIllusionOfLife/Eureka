"""
Tests for LLM Router integration with agents.

Verifies that the router is actually called during workflow execution.
"""

from unittest.mock import patch, Mock

from madspark.schemas.generation import ImprovementResponse
from madspark.llm.response import LLMResponse


class TestRouterIntegration:
    """Test that router is actually wired into execution paths."""

    def test_improve_idea_structured_uses_router(self):
        """Test that improve_idea_structured calls router when available."""
        from madspark.agents.structured_idea_generator import improve_idea_structured

        # Create mock router
        mock_router = Mock()
        mock_validated = ImprovementResponse(
            improved_title="Router Improved Title",
            improved_description="Router improved description with all feedback addressed.",
            key_improvements=["Addressed strength 1", "Mitigated concern 1"],
            implementation_steps=["Step 1: Implement", "Step 2: Test"],
            differentiators=["Unique feature 1"]
        )
        mock_response = LLMResponse(
            text='{"improved_title": "Router Improved Title", "improved_description": "..."}',
            provider="ollama",
            model="gemma3:4b",
            tokens_used=100,
            latency_ms=500,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_validated, mock_response)

        with patch('madspark.agents.structured_idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                result = improve_idea_structured(
                    original_idea="Original idea",
                    critique="Good evaluation",
                    advocacy_points="Strong points",
                    skeptic_points="Some concerns",
                    topic="Test topic",
                    context="Test context",
                    use_router=True,
                    genai_client=None  # No direct client, should use router
                )

        # Verify router was called
        mock_router.generate_structured.assert_called_once()
        call_kwargs = mock_router.generate_structured.call_args[1]
        assert "Test topic" in call_kwargs['prompt']
        assert call_kwargs['schema'] == ImprovementResponse
        assert call_kwargs['temperature'] == 0.9  # default

        # Verify result format
        assert "Router Improved Title" in result
        assert "Router improved description" in result

    def test_improve_idea_structured_increments_metrics(self):
        """Test that router metrics are incremented during call."""
        from madspark.agents.structured_idea_generator import improve_idea_structured
        from madspark.llm import reset_router

        # Reset router to get fresh metrics
        reset_router()

        mock_validated = ImprovementResponse(
            improved_title="Improved",
            improved_description="Description",
            key_improvements=["Change 1"],
            implementation_steps=["Step 1"],
            differentiators=["Unique aspect"]
        )
        mock_response = LLMResponse(
            text="{}",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=150,
            latency_ms=600,
            cost=0.0
        )

        with patch('madspark.agents.structured_idea_generator.get_router') as mock_get_router:
            mock_router = Mock()
            mock_router.generate_structured.return_value = (mock_validated, mock_response)
            mock_get_router.return_value = mock_router

            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                improve_idea_structured(
                    original_idea="Idea",
                    critique="Eval",
                    advocacy_points="Points",
                    skeptic_points="Concerns",
                    topic="Topic",
                    context="Context",
                    use_router=True
                )

        # Router's generate_structured was called
        mock_router.generate_structured.assert_called_once()

    def test_improve_idea_structured_respects_use_router_false(self):
        """Test that router is bypassed when use_router=False."""
        from madspark.agents.structured_idea_generator import improve_idea_structured

        mock_router = Mock()

        with patch('madspark.agents.structured_idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                # use_router=False should skip router entirely
                result = improve_idea_structured(
                    original_idea="Idea",
                    critique="Eval",
                    advocacy_points="Points",
                    skeptic_points="Concerns",
                    topic="Topic",
                    context="Context",
                    use_router=False
                )

        # Router should NOT have been called
        mock_router.generate_structured.assert_not_called()
        # Should return mock response (no genai_client)
        assert "revolutionary" in result or "Context" in result

    def test_improve_idea_structured_falls_back_on_router_failure(self):
        """Test fallback to direct API when router fails."""
        from madspark.agents.structured_idea_generator import improve_idea_structured
        from madspark.llm.exceptions import AllProvidersFailedError

        mock_router = Mock()
        mock_router.generate_structured.side_effect = AllProvidersFailedError(
            "Both Ollama and Gemini failed", {}
        )

        with patch('madspark.agents.structured_idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                # Should fall back to mock response (no genai_client available)
                result = improve_idea_structured(
                    original_idea="Idea",
                    critique="Eval",
                    advocacy_points="Points",
                    skeptic_points="Concerns",
                    topic="Topic",
                    context="Test Context"
                )

        # Router was called but failed
        mock_router.generate_structured.assert_called_once()
        # Should get mock fallback response
        assert "Test Context" in result or "revolutionary" in result

    def test_improve_idea_structured_uses_genai_client_when_provided(self):
        """Test that explicit genai_client bypasses router."""
        from madspark.agents.structured_idea_generator import improve_idea_structured

        mock_router = Mock()
        mock_genai_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"improved_title": "Direct API Title", "improved_description": "Direct API desc", "improvements": []}'
        mock_genai_client.models.generate_content.return_value = mock_response

        with patch('madspark.agents.structured_idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                with patch('madspark.agents.structured_idea_generator.GENAI_AVAILABLE', True):
                    result = improve_idea_structured(
                        original_idea="Idea",
                        critique="Eval",
                        advocacy_points="Points",
                        skeptic_points="Concerns",
                        topic="Topic",
                        context="Context",
                        genai_client=mock_genai_client  # Explicit client should bypass router
                    )

        # Router should NOT have been called (explicit client provided)
        mock_router.generate_structured.assert_not_called()
        # Direct API should have been called
        mock_genai_client.models.generate_content.assert_called_once()
        assert "Direct API Title" in result

    def test_router_handles_empty_multimodal_inputs(self):
        """Test that empty multimodal files/URLs are passed correctly to router."""
        from madspark.agents.structured_idea_generator import improve_idea_structured

        mock_router = Mock()
        mock_validated = ImprovementResponse(
            improved_title="Result Without Files",
            improved_description="Processed without multimodal",
            key_improvements=["Improvement 1"],
            implementation_steps=["Step 1"],
            differentiators=["Differentiator 1"]
        )
        mock_response = LLMResponse(
            text="{}",
            provider="ollama",
            model="gemma3:4b",
            tokens_used=200,
            latency_ms=800,
            cost=0.0
        )
        mock_router.generate_structured.return_value = (mock_validated, mock_response)

        with patch('madspark.agents.structured_idea_generator.get_router', return_value=mock_router):
            with patch('madspark.agents.structured_idea_generator.LLM_ROUTER_AVAILABLE', True):
                result = improve_idea_structured(
                    original_idea="Idea",
                    critique="Eval",
                    advocacy_points="Points",
                    skeptic_points="Concerns",
                    topic="Topic",
                    context="Context",
                    multimodal_files=None,  # No files
                    multimodal_urls=None  # No URLs
                )

        # Verify None values are passed correctly
        call_kwargs = mock_router.generate_structured.call_args[1]
        assert call_kwargs['files'] is None
        assert call_kwargs['urls'] is None
        assert "Result Without Files" in result


class TestCLIStatsAfterRouterIntegration:
    """Test that --show-llm-stats shows non-zero values after router usage."""

    def test_stats_show_actual_usage_when_router_used(self, capsys):
        """Test that stats display reflects actual router usage."""
        from madspark.cli.cli import _show_llm_stats

        mock_router = Mock()
        # Simulate actual router usage
        mock_router.get_metrics.return_value = {
            'total_requests': 5,
            'ollama_calls': 3,
            'gemini_calls': 2,
            'cache_hits': 1,
            'fallback_triggers': 1,
            'total_tokens': 750,
            'total_cost': 0.00015,
            'cache_hit_rate': 0.2,
            'avg_latency_ms': 450.0,
        }

        mock_cache = Mock()
        mock_cache.enabled = True
        mock_cache.stats.return_value = {
            'size': 5,
            'volume': 2048,
        }

        with patch('madspark.llm.get_router', return_value=mock_router):
            with patch('madspark.llm.get_cache', return_value=mock_cache):
                _show_llm_stats()

        output = capsys.readouterr().out
        # Should NOT show "router not used" warning
        assert 'LLM Router was not used' not in output
        # Should show actual non-zero metrics
        assert 'Total Requests: 5' in output
        assert 'Ollama Calls: 3' in output
        assert 'Gemini Calls: 2' in output
        assert 'Cache Hits: 1' in output
        assert 'Fallback Triggers: 1' in output
        assert 'Total Tokens: 750' in output
