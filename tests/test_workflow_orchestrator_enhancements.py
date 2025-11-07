"""Tests for Phase 3.2a: WorkflowOrchestrator Enhancements.

This test suite validates the new features being added to WorkflowOrchestrator:
1. Monitoring integration with batch_call_context
2. Async method variants
3. Multi-dimensional evaluation support

Following TDD: These tests are written BEFORE implementation and should fail initially.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from madspark.core.workflow_orchestrator import WorkflowOrchestrator
from madspark.utils.batch_monitor import BatchMonitor
from madspark.config.workflow_constants import FALLBACK_ADVOCACY


class TestWorkflowOrchestratorMonitoring:
    """Test monitoring integration with batch_call_context."""

    def test_generate_ideas_with_monitoring(self):
        """Test that generate_ideas integrates with batch monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        with patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.json_parsers.parse_idea_generator_response') as mock_parser:
            mock_gen.return_value = '{"ideas": [{"text": "Idea 1"}, {"text": "Idea 2"}, {"text": "Idea 3"}]}'
            mock_parser.return_value = ["Idea 1", "Idea 2", "Idea 3"]

            # Call with monitoring enabled
            ideas, tokens = orchestrator.generate_ideas_with_monitoring(
                topic="Test topic",
                context="Test context",
                num_ideas=3,
                monitor=monitor
            )

            assert len(ideas) == 3
            assert tokens > 0
            # Verify monitoring was called
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "idea_generation"
            assert monitor.metrics_history[0].success is True

    def test_evaluate_ideas_with_monitoring(self):
        """Test that evaluate_ideas integrates with batch monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        with patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic:
            mock_critic.return_value = '[{"score": 8, "comment": "Good idea"}]'

            # Call with monitoring
            evaluated, tokens = orchestrator.evaluate_ideas_with_monitoring(
                ideas=["Test idea"],
                topic="Test topic",
                context="Test context",
                monitor=monitor
            )

            assert len(evaluated) == 1
            assert evaluated[0]["score"] == 8
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "evaluation"

    def test_process_advocacy_with_monitoring(self):
        """Test advocacy processing with monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        candidates = [
            {"idea": "Test idea", "initial_critique": "Test critique"}
        ]

        with patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate:
            mock_advocate.return_value = ([{"formatted": "Test advocacy"}], 100)

            updated, tokens = orchestrator.process_advocacy_with_monitoring(
                candidates=candidates,
                topic="Test",
                context="Test",
                monitor=monitor
            )

            assert updated[0]["advocacy"] == "Test advocacy"
            assert tokens == 100
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "advocate"
            assert monitor.metrics_history[0].tokens_used == 100

    def test_process_skepticism_with_monitoring(self):
        """Test skepticism processing with monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        candidates = [
            {"idea": "Test idea", "advocacy": "Test advocacy"}
        ]

        with patch('madspark.core.workflow_orchestrator.criticize_ideas_batch') as mock_skeptic:
            mock_skeptic.return_value = ([{"formatted": "Test skepticism"}], 100)

            updated, tokens = orchestrator.process_skepticism_with_monitoring(
                candidates=candidates,
                topic="Test",
                context="Test",
                monitor=monitor
            )

            assert updated[0]["skepticism"] == "Test skepticism"
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "skeptic"

    def test_improve_ideas_with_monitoring(self):
        """Test idea improvement with monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        candidates = [
            {
                "idea": "Original idea",
                "initial_critique": "Critique",
                "advocacy": "Advocacy",
                "skepticism": "Skepticism"
            }
        ]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Improved idea"}], 150)

            updated, tokens = orchestrator.improve_ideas_with_monitoring(
                candidates=candidates,
                topic="Test",
                context="Test",
                monitor=monitor
            )

            assert updated[0]["improved_idea"] == "Improved idea"
            assert tokens == 150
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "improve"
            assert monitor.metrics_history[0].tokens_used == 150

    def test_reevaluate_ideas_with_monitoring(self):
        """Test re-evaluation with monitoring."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        candidates = [
            {"improved_idea": "Improved idea", "initial_score": 5}
        ]

        with patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic:
            mock_critic.return_value = '[{"score": 9, "comment": "Much better"}]'

            updated, tokens = orchestrator.reevaluate_ideas_with_monitoring(
                candidates=candidates,
                topic="Test",
                context="Test",
                monitor=monitor
            )

            assert updated[0]["improved_score"] == 9.0
            assert len(monitor.metrics_history) == 1
            assert monitor.metrics_history[0].batch_type == "reevaluation"

    def test_monitoring_with_fallback_on_error(self):
        """Test that monitoring correctly records when fallback is used."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        candidates = [{"idea": "Test", "initial_critique": "Test"}]

        with patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate:
            mock_advocate.side_effect = Exception("API Error")

            updated, tokens = orchestrator.process_advocacy_with_monitoring(
                candidates=candidates,
                topic="Test",
                context="Test",
                monitor=monitor
            )

            # Should use fallback
            assert updated[0]["advocacy"] == FALLBACK_ADVOCACY
            assert tokens == 0
            # Verify monitoring was called
            assert len(monitor.metrics_history) == 1
            # Base method catches exception and returns gracefully, so success is True
            # The monitoring records that we completed the operation (even if with fallback)
            assert monitor.metrics_history[0].success is True


class TestWorkflowOrchestratorAsync:
    """Test async method variants for async_coordinator integration."""

    @pytest.mark.asyncio
    async def test_generate_ideas_async(self):
        """Test async idea generation."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        with patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.json_parsers.parse_idea_generator_response') as mock_parser:
            mock_gen.return_value = '{"ideas": [{"text": "Async idea 1"}, {"text": "Async idea 2"}]}'
            mock_parser.return_value = ["Async idea 1", "Async idea 2"]

            ideas, tokens = await orchestrator.generate_ideas_async(
                topic="Async test",
                context="Async context",
                num_ideas=2
            )

            assert len(ideas) == 2
            assert "Async idea 1" in ideas
            assert tokens > 0

    @pytest.mark.asyncio
    async def test_evaluate_ideas_async(self):
        """Test async idea evaluation."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        with patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic:
            mock_critic.return_value = '[{"score": 7, "comment": "Async evaluation"}]'

            evaluated, tokens = await orchestrator.evaluate_ideas_async(
                ideas=["Async idea"],
                topic="Test",
                context="Test"
            )

            assert len(evaluated) == 1
            assert evaluated[0]["score"] == 7

    @pytest.mark.asyncio
    async def test_process_advocacy_async(self):
        """Test async advocacy processing."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{"idea": "Test", "initial_critique": "Test"}]

        with patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate:
            mock_advocate.return_value = ([{"formatted": "Async advocacy"}], 100)

            updated, tokens = await orchestrator.process_advocacy_async(
                candidates=candidates,
                topic="Test",
                context="Test"
            )

            assert updated[0]["advocacy"] == "Async advocacy"

    @pytest.mark.asyncio
    async def test_process_skepticism_async(self):
        """Test async skepticism processing."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{"idea": "Test", "advocacy": "Test"}]

        with patch('madspark.core.workflow_orchestrator.criticize_ideas_batch') as mock_skeptic:
            mock_skeptic.return_value = ([{"formatted": "Async skepticism"}], 100)

            updated, tokens = await orchestrator.process_skepticism_async(
                candidates=candidates,
                topic="Test",
                context="Test"
            )

            assert updated[0]["skepticism"] == "Async skepticism"

    @pytest.mark.asyncio
    async def test_improve_ideas_async(self):
        """Test async idea improvement."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{
            "idea": "Original",
            "initial_critique": "Critique",
            "advocacy": "Advocacy",
            "skepticism": "Skepticism"
        }]

        with patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:
            mock_improve.return_value = ([{"improved_idea": "Async improved"}], 150)

            updated, tokens = await orchestrator.improve_ideas_async(
                candidates=candidates,
                topic="Test",
                context="Test"
            )

            assert updated[0]["improved_idea"] == "Async improved"

    @pytest.mark.asyncio
    async def test_reevaluate_ideas_async(self):
        """Test async re-evaluation."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates = [{"improved_idea": "Improved", "initial_score": 5}]

        with patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic:
            mock_critic.return_value = '[{"score": 8, "comment": "Async better"}]'

            updated, tokens = await orchestrator.reevaluate_ideas_async(
                candidates=candidates,
                topic="Test",
                context="Test"
            )

            assert updated[0]["improved_score"] == 8.0

    @pytest.mark.asyncio
    async def test_async_with_timeout(self):
        """Test that async methods respect timeouts."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        with patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.json_parsers.parse_idea_generator_response') as mock_parser:
            # Simulate slow response
            def slow_response(*args, **kwargs):
                import time
                time.sleep(2)
                return '{"ideas": ["Slow idea"]}'

            mock_gen.side_effect = slow_response
            mock_parser.return_value = ["Slow idea"]

            # Should timeout
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    orchestrator.generate_ideas_async("Test", "Test", 1),
                    timeout=0.5
                )

    @pytest.mark.asyncio
    async def test_async_parallel_execution(self):
        """Test that async methods can run in parallel."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        candidates1 = [{"idea": "Test1", "initial_critique": "Test1"}]
        candidates2 = [{"idea": "Test2", "advocacy": "Test2"}]

        with patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate, \
             patch('madspark.core.workflow_orchestrator.criticize_ideas_batch') as mock_skeptic:

            mock_advocate.return_value = ([{"formatted": "Advocacy"}], 100)
            mock_skeptic.return_value = ([{"formatted": "Skepticism"}], 100)

            # Run both in parallel
            results = await asyncio.gather(
                orchestrator.process_advocacy_async(candidates1, "Test", "Test"),
                orchestrator.process_skepticism_async(candidates2, "Test", "Test")
            )

            assert len(results) == 2
            assert results[0][0][0]["advocacy"] == "Advocacy"
            assert results[1][0][0]["skepticism"] == "Skepticism"


class TestWorkflowOrchestratorMultiDimensional:
    """Test multi-dimensional evaluation support."""

    def test_multi_dimensional_evaluation_integration(self):
        """Test that orchestrator can integrate multi-dimensional evaluation."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        # Create mock reasoning engine with multi_evaluator
        mock_engine = Mock()
        mock_multi_evaluator = Mock()
        mock_multi_evaluator.evaluate_ideas_batch.return_value = [
            {
                "feasibility": 0.8,
                "innovation": 0.9,
                "impact": 0.7,
                "cost_effectiveness": 0.6,
                "scalability": 0.8,
                "safety_score": 0.9,
                "timeline": 0.7
            }
        ]
        mock_engine.multi_evaluator = mock_multi_evaluator
        orchestrator.reasoning_engine = mock_engine

        candidates = [{"text": "Test idea", "critique": "Test critique"}]

        updated = orchestrator.add_multi_dimensional_evaluation(
            candidates=candidates,
            topic="Test",
            context="Test"
        )

        assert updated[0]["multi_dimensional_evaluation"] is not None
        assert updated[0]["multi_dimensional_evaluation"]["feasibility"] == 0.8
        assert updated[0]["multi_dimensional_evaluation"]["innovation"] == 0.9

    def test_multi_dimensional_with_monitoring(self):
        """Test multi-dimensional evaluation with monitoring integration."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        mock_engine = Mock()
        mock_multi_evaluator = Mock()
        mock_multi_evaluator.evaluate_ideas_batch.return_value = [
            {"feasibility": 0.8, "innovation": 0.9, "impact": 0.7,
             "cost_effectiveness": 0.6, "scalability": 0.8,
             "safety_score": 0.9, "timeline": 0.7}
        ]
        mock_engine.multi_evaluator = mock_multi_evaluator
        orchestrator.reasoning_engine = mock_engine

        candidates = [{"text": "Test", "critique": "Test"}]

        updated = orchestrator.add_multi_dimensional_evaluation_with_monitoring(
            candidates=candidates,
            topic="Test",
            context="Test",
            monitor=monitor
        )

        assert updated[0]["multi_dimensional_evaluation"] is not None
        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0].batch_type == "multi_dimensional"

    def test_multi_dimensional_fallback_on_error(self):
        """Test graceful fallback when multi-dimensional evaluation fails."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        mock_engine = Mock()
        mock_multi_evaluator = Mock()
        mock_multi_evaluator.evaluate_ideas_batch.side_effect = Exception("Evaluation error")
        mock_engine.multi_evaluator = mock_multi_evaluator
        orchestrator.reasoning_engine = mock_engine

        candidates = [{"text": "Test", "critique": "Test"}]

        updated = orchestrator.add_multi_dimensional_evaluation(
            candidates=candidates,
            topic="Test",
            context="Test"
        )

        # Should not crash, multi_dimensional_evaluation should not exist or be None
        assert updated[0].get("multi_dimensional_evaluation") is None

    def test_multi_dimensional_without_engine(self):
        """Test behavior when reasoning engine is not available."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        orchestrator.reasoning_engine = None

        candidates = [{"text": "Test", "critique": "Test"}]

        updated = orchestrator.add_multi_dimensional_evaluation(
            candidates=candidates,
            topic="Test",
            context="Test"
        )

        # Should not crash, multi_dimensional_evaluation should not exist or be None
        assert updated[0].get("multi_dimensional_evaluation") is None

    @pytest.mark.asyncio
    async def test_multi_dimensional_async(self):
        """Test async variant of multi-dimensional evaluation."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        mock_engine = Mock()
        mock_multi_evaluator = Mock()
        mock_multi_evaluator.evaluate_ideas_batch.return_value = [
            {"feasibility": 0.8, "innovation": 0.9, "impact": 0.7,
             "cost_effectiveness": 0.6, "scalability": 0.8,
             "safety_score": 0.9, "timeline": 0.7}
        ]
        mock_engine.multi_evaluator = mock_multi_evaluator
        orchestrator.reasoning_engine = mock_engine

        candidates = [{"text": "Async test", "critique": "Test"}]

        updated = await orchestrator.add_multi_dimensional_evaluation_async(
            candidates=candidates,
            topic="Test",
            context="Test"
        )

        assert updated[0]["multi_dimensional_evaluation"] is not None
        assert updated[0]["multi_dimensional_evaluation"]["innovation"] == 0.9


class TestWorkflowOrchestratorIntegration:
    """Integration tests for enhanced orchestrator features."""

    def test_complete_workflow_with_monitoring(self):
        """Test complete workflow with monitoring enabled."""
        orchestrator = WorkflowOrchestrator(verbose=False)
        monitor = BatchMonitor()

        with patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.json_parsers.parse_idea_generator_response') as mock_parser, \
             patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic, \
             patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate, \
             patch('madspark.core.workflow_orchestrator.criticize_ideas_batch') as mock_skeptic, \
             patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:

            mock_gen.return_value = '{"ideas": [{"text": "Idea 1"}, {"text": "Idea 2"}]}'
            mock_parser.return_value = ["Idea 1", "Idea 2"]
            mock_critic.return_value = '[{"score": 7, "comment": "Good"}, {"score": 6, "comment": "Ok"}]'
            mock_advocate.return_value = ([{"formatted": "Advocacy"}] * 2, 100)
            mock_skeptic.return_value = ([{"formatted": "Skepticism"}] * 2, 100)
            mock_improve.return_value = ([{"improved_idea": "Better"}] * 2, 150)

            # Run complete workflow with monitoring
            ideas, _ = orchestrator.generate_ideas_with_monitoring("Test", "Test", 2, monitor)
            evaluated, _ = orchestrator.evaluate_ideas_with_monitoring(ideas, "Test", "Test", monitor)

            # Convert to candidates
            candidates = [
                {
                    "idea": evaluated[0]["text"],
                    "initial_score": evaluated[0]["score"],
                    "initial_critique": evaluated[0]["critique"]
                }
            ]

            candidates, _ = orchestrator.process_advocacy_with_monitoring(candidates, "Test", "Test", monitor)
            candidates, _ = orchestrator.process_skepticism_with_monitoring(candidates, "Test", "Test", monitor)
            candidates, _ = orchestrator.improve_ideas_with_monitoring(candidates, "Test", "Test", monitor)

            # Verify monitoring recorded all steps
            assert len(monitor.metrics_history) == 5
            assert monitor.metrics_history[0].batch_type == "idea_generation"
            assert monitor.metrics_history[1].batch_type == "evaluation"
            assert monitor.metrics_history[2].batch_type == "advocate"
            assert monitor.metrics_history[3].batch_type == "skeptic"
            assert monitor.metrics_history[4].batch_type == "improve"

    @pytest.mark.asyncio
    async def test_complete_async_workflow(self):
        """Test complete async workflow."""
        orchestrator = WorkflowOrchestrator(verbose=False)

        with patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.json_parsers.parse_idea_generator_response') as mock_parser, \
             patch('madspark.core.workflow_orchestrator.call_critic_with_retry') as mock_critic, \
             patch('madspark.core.workflow_orchestrator.advocate_ideas_batch') as mock_advocate, \
             patch('madspark.core.workflow_orchestrator.criticize_ideas_batch') as mock_skeptic, \
             patch('madspark.core.workflow_orchestrator.improve_ideas_batch') as mock_improve:

            mock_gen.return_value = '{"ideas": [{"text": "Async idea"}]}'
            mock_parser.return_value = ["Async idea"]
            mock_critic.return_value = '[{"score": 8, "comment": "Great"}]'
            mock_advocate.return_value = ([{"formatted": "Advocacy"}], 100)
            mock_skeptic.return_value = ([{"formatted": "Skepticism"}], 100)
            mock_improve.return_value = ([{"improved_idea": "Improved"}], 150)

            # Run async workflow
            ideas, _ = await orchestrator.generate_ideas_async("Test", "Test", 1)
            evaluated, _ = await orchestrator.evaluate_ideas_async(ideas, "Test", "Test")

            candidates = [{
                "idea": evaluated[0]["text"],
                "initial_score": evaluated[0]["score"],
                "initial_critique": evaluated[0]["critique"]
            }]

            # Run advocacy and skepticism in parallel
            results = await asyncio.gather(
                orchestrator.process_advocacy_async(candidates, "Test", "Test"),
                orchestrator.process_skepticism_async(candidates, "Test", "Test")
            )

            candidates, _ = results[0]
            candidates, _ = results[1]

            candidates, _ = await orchestrator.improve_ideas_async(candidates, "Test", "Test")
            final_results = orchestrator.build_final_results(candidates)

            assert len(final_results) == 1
            assert final_results[0]["improved_idea"] == "Improved"
