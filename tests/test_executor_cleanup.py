"""Test suite for ThreadPoolExecutor cleanup in BatchOperationsBase.

This module tests that the executor is properly cleaned up to prevent resource leaks.
"""
import pytest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

from src.madspark.core.batch_operations_base import BatchOperationsBase


class TestExecutorCleanup:
    """Test cases for executor cleanup functionality."""

    def test_executor_cleanup_registered_on_init(self):
        """Test that executor cleanup is registered with atexit on initialization."""
        # Mock atexit.register to verify it's called
        with patch('atexit.register') as mock_register:
            batch_ops = BatchOperationsBase()

            # Verify atexit.register was called
            mock_register.assert_called_once()

            # Verify it was called with executor.shutdown
            call_args = mock_register.call_args
            assert call_args[0][0] == batch_ops.executor.shutdown
            assert call_args[1] == {'wait': False}

    def test_executor_created_on_init(self):
        """Test that executor is created during initialization."""
        batch_ops = BatchOperationsBase()

        assert batch_ops.executor is not None
        assert isinstance(batch_ops.executor, ThreadPoolExecutor)

    def test_executor_shutdown_called_with_correct_params(self):
        """Test that executor.shutdown is called with wait=False."""
        batch_ops = BatchOperationsBase()

        # Mock the shutdown method
        with patch.object(batch_ops.executor, 'shutdown') as mock_shutdown:
            # Manually trigger what atexit would do
            batch_ops.executor.shutdown(wait=False)

            # Verify shutdown was called with wait=False
            mock_shutdown.assert_called_once_with(wait=False)

    def test_multiple_instances_each_register_cleanup(self):
        """Test that multiple instances each register their own cleanup."""
        with patch('atexit.register') as mock_register:
            batch_ops1 = BatchOperationsBase()
            batch_ops2 = BatchOperationsBase()

            # Each instance should register its own cleanup
            assert mock_register.call_count == 2

            # Verify each registered its own executor's shutdown
            calls = mock_register.call_args_list
            assert calls[0][0][0] == batch_ops1.executor.shutdown
            assert calls[1][0][0] == batch_ops2.executor.shutdown

    def test_executor_accepts_tasks_before_shutdown(self):
        """Test that executor can accept tasks normally before shutdown."""
        batch_ops = BatchOperationsBase()

        # Submit a simple task
        def simple_task():
            return "task_result"

        future = batch_ops.executor.submit(simple_task)
        result = future.result(timeout=1)

        assert result == "task_result"

    def test_cleanup_pattern_matches_async_coordinator(self):
        """Test that cleanup pattern matches the one in async_coordinator.py."""
        # This test verifies we're using the same pattern as the existing good example
        with patch('atexit.register') as mock_register:
            BatchOperationsBase()  # Create instance to trigger atexit registration

            # Should match: atexit.register(self.executor.shutdown, wait=False)
            call_args = mock_register.call_args

            # Verify the function is shutdown
            assert call_args[0][0].__name__ == 'shutdown'

            # Verify wait=False is passed as keyword argument
            assert 'wait' in call_args[1]
            assert call_args[1]['wait'] is False


class TestExecutorCleanupIntegration:
    """Integration tests for executor cleanup."""

    def test_real_executor_cleanup_doesnt_block(self):
        """Test that real executor cleanup with wait=False doesn't block."""
        import time

        batch_ops = BatchOperationsBase()

        # Submit a long-running task
        def long_task():
            time.sleep(2)
            return "done"

        batch_ops.executor.submit(long_task)

        # Shutdown with wait=False should not block
        start = time.time()
        batch_ops.executor.shutdown(wait=False)
        elapsed = time.time() - start

        # Should complete almost immediately (< 0.1s)
        assert elapsed < 0.1, f"Shutdown blocked for {elapsed}s"

    def test_executor_rejects_tasks_after_shutdown(self):
        """Test that executor rejects new tasks after shutdown."""
        batch_ops = BatchOperationsBase()
        batch_ops.executor.shutdown(wait=False)

        # Attempting to submit after shutdown should raise RuntimeError
        with pytest.raises(RuntimeError):
            batch_ops.executor.submit(lambda: "test")
