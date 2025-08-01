"""Tests for batch monitoring and error handling."""
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from madspark.utils.batch_monitor import (
    BatchMonitor, batch_call_context, 
    get_batch_monitor, reset_batch_monitor
)
from madspark.utils.batch_fallback import batch_with_fallback


class TestBatchMonitor:
    """Test batch monitoring functionality."""
    
    def setup_method(self):
        """Reset monitor before each test."""
        reset_batch_monitor()
    
    def test_basic_monitoring(self):
        """Test basic batch call monitoring."""
        monitor = BatchMonitor()
        
        # Test successful call
        context = monitor.start_batch_call("test_batch", 3)
        time.sleep(0.01)  # Small delay for duration measurement
        metrics = monitor.end_batch_call(context, success=True, tokens_used=150)
        
        assert metrics.batch_type == "test_batch"
        assert metrics.items_count == 3
        assert metrics.tokens_used == 150
        assert metrics.success is True
        assert metrics.duration_seconds > 0
        assert metrics.tokens_per_item == 50.0
        
        # Test session summary
        summary = monitor.get_session_summary()
        assert summary["total_calls"] == 1
        assert summary["successful_calls"] == 1
        assert summary["total_items_processed"] == 3
    
    def test_failed_call_monitoring(self):
        """Test monitoring of failed batch calls."""
        monitor = BatchMonitor()
        
        context = monitor.start_batch_call("failed_batch", 2)
        metrics = monitor.end_batch_call(
            context, 
            success=False, 
            error_message="API timeout",
            fallback_used=True
        )
        
        assert metrics.success is False
        assert metrics.error_message == "API timeout"
        assert metrics.fallback_used is True
        
        summary = monitor.get_session_summary()
        assert summary["failed_calls"] == 1
        assert summary["fallback_calls"] == 1
    
    def test_context_manager(self):
        """Test batch_call_context context manager."""
        with batch_call_context("context_test", 5) as ctx:
            ctx.set_tokens_used(200)
            time.sleep(0.01)
        
        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()
        
        assert summary["total_calls"] == 1
        assert summary["successful_calls"] == 1
        assert summary["total_items_processed"] == 5
    
    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly."""
        with pytest.raises(ValueError):
            with batch_call_context("error_test", 2):
                raise ValueError("Test error")
        
        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()
        
        assert summary["total_calls"] == 1
        assert summary["failed_calls"] == 1
    
    def test_cost_analysis(self):
        """Test cost effectiveness analysis."""
        monitor = BatchMonitor()
        
        # Add successful batch calls
        context1 = monitor.start_batch_call("advocate", 3)
        monitor.end_batch_call(context1, success=True, tokens_used=300)
        
        context2 = monitor.start_batch_call("skeptic", 3)
        monitor.end_batch_call(context2, success=True, tokens_used=250)
        
        analysis = monitor.analyze_cost_effectiveness()
        
        assert "batch_effectiveness" in analysis
        assert "advocate" in analysis["batch_effectiveness"]
        assert "skeptic" in analysis["batch_effectiveness"]
        
        advocate_stats = analysis["batch_effectiveness"]["advocate"]
        assert advocate_stats["total_calls"] == 1
        assert advocate_stats["total_items"] == 3
    
    def test_metrics_logging_to_file(self):
        """Test metrics are logged to file correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            log_file = f.name
        
        try:
            monitor = BatchMonitor(log_file=log_file)
            
            context = monitor.start_batch_call("file_test", 2)
            monitor.end_batch_call(context, success=True, tokens_used=100)
            
            # Check file contents
            log_path = Path(log_file)
            assert log_path.exists()
            
            content = log_path.read_text()
            assert "file_test" in content
            assert "100" in content  # tokens_used
            
        finally:
            Path(log_file).unlink(missing_ok=True)


class TestBatchFallback:
    """Test batch fallback mechanisms."""
    
    def test_successful_batch(self):
        """Test successful batch processing without fallback."""
        def mock_batch_func(items, theme, temp):
            return [{"idea_index": i, "result": f"batch_{i}"} for i in range(len(items))]
        
        def mock_fallback_func(item, theme, temp):
            return {"result": "fallback"}
        
        items = ["item1", "item2", "item3"]
        results = batch_with_fallback(
            mock_batch_func, mock_fallback_func, items, "test_batch",
            "theme", 0.5
        )
        
        assert len(results) == 3
        assert all(r["result"].startswith("batch_") for r in results)
    
    def test_batch_failure_with_fallback(self):
        """Test fallback when batch processing fails."""
        def failing_batch_func(items, theme, temp):
            raise Exception("Batch processing failed")
        
        def mock_fallback_func(item, theme, temp):
            return {"result": f"fallback_{item}"}
        
        items = ["item1", "item2"]
        results = batch_with_fallback(
            failing_batch_func, mock_fallback_func, items, "test_batch",
            "theme", 0.5
        )
        
        assert len(results) == 2
        assert all("fallback_" in r["result"] for r in results)
        assert all("idea_index" in r for r in results)
    
    def test_both_batch_and_fallback_fail(self):
        """Test behavior when both batch and fallback fail."""
        def failing_batch_func(items, theme, temp):
            raise Exception("Batch failed")
        
        def failing_fallback_func(item, theme, temp):
            raise Exception("Fallback failed")
        
        items = ["item1", "item2"]
        results = batch_with_fallback(
            failing_batch_func, failing_fallback_func, items, "test_batch",
            "theme", 0.5
        )
        
        assert len(results) == 2
        assert all("error" in r for r in results)
        assert all("formatted" in r for r in results)
    
    def test_invalid_batch_results(self):
        """Test handling of invalid batch function results."""
        def invalid_batch_func(items, theme, temp):
            return "invalid_result"  # Should return list
        
        def mock_fallback_func(item, theme, temp):
            return {"result": "fallback"}
        
        items = ["item1"]
        results = batch_with_fallback(
            invalid_batch_func, mock_fallback_func, items, "test_batch",
            "theme", 0.5
        )
        
        assert len(results) == 1
        assert "fallback" in results[0]["result"]


class TestBatchIntegration:
    """Integration tests for batch monitoring with coordinator."""
    
    def setup_method(self):
        """Reset monitor before each test."""
        reset_batch_monitor()
    
    @patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry')
    @patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry')
    @patch('madspark.agents.advocate.advocate_ideas_batch')
    @patch('madspark.agents.skeptic.criticize_ideas_batch')
    @patch('madspark.agents.idea_generator.improve_ideas_batch')
    def test_coordinator_monitoring(
        self, mock_improve, mock_skeptic, mock_advocate, mock_critic, mock_gen
    ):
        """Test that coordinator properly uses monitoring."""
        # Setup mocks
        mock_gen.return_value = "Idea 1: Test idea"
        mock_critic.side_effect = [
            '{"score": 8, "comment": "Good"}',
            '{"score": 9, "comment": "Better"}'
        ]
        mock_advocate.return_value = [{"idea_index": 0, "formatted": "STRENGTHS: Good"}]
        mock_skeptic.return_value = [{"idea_index": 0, "formatted": "FLAWS: None"}]
        mock_improve.return_value = [{"idea_index": 0, "improved_idea": "Better idea"}]
        
        # Run coordinator
        from madspark.core.coordinator_batch import run_multistep_workflow_batch
        
        results = run_multistep_workflow_batch(
            theme="Test Theme",
            constraints="Test Constraints", 
            num_top_candidates=1,
            verbose=False
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["improved_idea"] == "Better idea"
        
        # Verify monitoring
        monitor = get_batch_monitor()
        summary = monitor.get_session_summary()
        
        assert summary["total_calls"] >= 3  # At least advocate, skeptic, improve
        assert summary["successful_calls"] >= 3
        assert summary["total_items_processed"] >= 3
        
        # Check batch types
        batch_types = summary.get("batch_type_breakdown", {})
        expected_types = {"advocate", "skeptic", "improve"}
        assert expected_types.issubset(set(batch_types.keys()))
    
    @patch('madspark.agents.advocate.advocate_ideas_batch')
    def test_coordinator_handles_batch_failure(self, mock_advocate):
        """Test coordinator handles batch failures gracefully."""
        # Make advocate batch fail
        mock_advocate.side_effect = Exception("API Error")
        
        with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_gen, \
             patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_critic, \
             patch('madspark.agents.skeptic.criticize_ideas_batch') as mock_skeptic, \
             patch('madspark.agents.idea_generator.improve_ideas_batch') as mock_improve:
            
            mock_gen.return_value = "Idea 1: Test idea"
            mock_critic.side_effect = ['{"score": 8, "comment": "Good"}', '{"score": 9, "comment": "Better"}']
            mock_skeptic.return_value = [{"idea_index": 0, "formatted": "FLAWS: None"}]
            mock_improve.return_value = [{"idea_index": 0, "improved_idea": "Better idea"}]
            
            from madspark.core.coordinator_batch import run_multistep_workflow_batch
            
            results = run_multistep_workflow_batch(
                theme="Test Theme",
                constraints="Test Constraints",
                num_top_candidates=1,
                verbose=False
            )
            
            # Should still work with fallback
            assert len(results) == 1
            assert "N/A (Batch advocate failed)" in results[0]["advocacy"]
            
            # Check monitoring recorded the fallback
            monitor = get_batch_monitor()
            summary = monitor.get_session_summary()
            assert summary["fallback_calls"] >= 1  # At least the advocate fallback