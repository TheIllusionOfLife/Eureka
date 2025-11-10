"""Test event loop handling in BatchProcessor.

This test module verifies that BatchProcessor correctly handles event loop contexts:
- Synchronous contexts (CLI, scripts) should work normally
- Asynchronous contexts should raise clear errors directing to correct API
- process_batch_async() should work correctly in async contexts
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from src.madspark.utils.batch_processor import BatchProcessor, BatchItem
from src.madspark.utils.errors import BatchProcessingError


class TestBatchProcessorEventLoop:
    """Test event loop detection and handling in BatchProcessor."""

    def test_process_batch_from_sync_context_succeeds(self):
        """Test that process_batch works in sync context (current behavior).

        This ensures existing usage (CLI, scripts) continues to work after fix.
        """
        # Mock the async workflow to avoid actual API calls
        with patch('src.madspark.utils.batch_processor.AsyncCoordinator') as mock_coordinator:
            # Setup mock to return valid results
            mock_instance = Mock()
            mock_instance.run_workflow = AsyncMock(return_value={
                'top_candidates': [{'text': 'Test idea', 'score': 8}],
                'all_ideas': [{'text': 'Test idea', 'score': 8}]
            })
            mock_coordinator.return_value = mock_instance

            processor = BatchProcessor(use_async=True)
            batch_items = [
                BatchItem(theme="Test theme", constraints="Test constraints")
            ]

            # Should not raise - we're not in async context
            summary = processor.process_batch(batch_items)

            assert summary is not None
            assert 'total_items' in summary
            assert summary['total_items'] == 1

    def test_process_batch_from_async_context_raises_error(self):
        """Test that process_batch raises helpful error from async context.

        This is the core fix: detect async context and guide users to correct API.
        """
        async def async_caller():
            processor = BatchProcessor(use_async=True)
            batch_items = [
                BatchItem(theme="Test theme", constraints="Test constraints")
            ]

            # Should raise BatchProcessingError with helpful message
            with pytest.raises(BatchProcessingError) as exc_info:
                processor.process_batch(batch_items)

            # Verify error message is helpful
            error_msg = str(exc_info.value)
            assert "cannot be called from an async context" in error_msg.lower()
            assert "process_batch_async" in error_msg
            assert "SOLUTION" in error_msg

            return True

        result = asyncio.run(async_caller())
        assert result is True

    @pytest.mark.asyncio
    async def test_process_batch_async_from_async_context_succeeds(self):
        """Test that process_batch_async works correctly in async context.

        This verifies the recommended async API works as expected.
        """
        # Mock the async workflow
        with patch('src.madspark.utils.batch_processor.AsyncCoordinator') as mock_coordinator:
            # Setup mock to return valid results
            mock_instance = Mock()

            # Create async mock for run_workflow
            async def mock_workflow(*args, **kwargs):
                return {
                    'top_candidates': [{'text': 'Test idea', 'score': 8}],
                    'all_ideas': [{'text': 'Test idea', 'score': 8}]
                }

            mock_instance.run_workflow = mock_workflow
            mock_coordinator.return_value = mock_instance

            processor = BatchProcessor(use_async=True)
            batch_items = [
                BatchItem(theme="Test theme", constraints="Test constraints")
            ]
            workflow_options = {
                "enable_novelty_filter": True,
                "novelty_threshold": 0.8,
                "verbose": False
            }

            # Should work - this is the correct async API
            summary = await processor.process_batch_async(batch_items, workflow_options)

            assert summary is not None
            assert 'total_items' in summary
            assert summary['total_items'] == 1

    def test_process_batch_sync_mode_always_works(self):
        """Test that sync mode (use_async=False) bypasses event loop issues.

        When async mode is disabled, asyncio.run() is never called,
        so it should work from any context.
        """
        # Mock the sync workflow
        with patch('src.madspark.core.coordinator_batch.run_multistep_workflow') as mock_workflow:
            mock_workflow.return_value = {
                'top_candidates': [{'text': 'Test idea', 'score': 8}],
                'all_ideas': [{'text': 'Test idea', 'score': 8}]
            }

            processor = BatchProcessor(use_async=False)  # Force sync mode
            batch_items = [
                BatchItem(theme="Test theme", constraints="Test constraints")
            ]

            # Should work - sync mode doesn't use asyncio.run()
            summary = processor.process_batch(batch_items)

            assert summary is not None
            assert 'total_items' in summary

    def test_error_message_quality_and_actionability(self):
        """Test that error message provides actionable guidance.

        Error messages should:
        - Explain what went wrong
        - Show how to fix it with code examples
        - Mention the correct method to use
        """
        async def async_caller():
            processor = BatchProcessor(use_async=True)
            batch_items = [BatchItem(theme="Test", constraints="Test constraints")]

            try:
                processor.process_batch(batch_items)
                pytest.fail("Expected BatchProcessingError was not raised")
            except BatchProcessingError as e:
                error_msg = str(e)

                # Check all required elements are in error message
                assert "process_batch_async" in error_msg, "Should mention correct method"
                assert "SOLUTION" in error_msg, "Should provide solutions"
                assert "async context" in error_msg.lower() or "event loop" in error_msg.lower(), \
                    "Should explain the problem"

                # Should provide alternatives
                assert "use_async=False" in error_msg or "synchronous mode" in error_msg.lower(), \
                    "Should mention sync mode alternative"

                return True

            return False

        result = asyncio.run(async_caller())
        assert result is True, "Error message validation failed"


class TestBatchProcessorIntegration:
    """Integration tests to ensure fix doesn't break existing functionality."""

    def test_cli_batch_processing_pattern_still_works(self):
        """Test that the common CLI batch processing pattern still works.

        This is the most important backward compatibility test - it simulates
        how the CLI currently uses BatchProcessor.
        """
        # Mock to avoid actual API calls
        with patch('src.madspark.utils.batch_processor.AsyncCoordinator') as mock_coordinator:
            mock_instance = Mock()
            mock_instance.run_workflow = AsyncMock(return_value={
                'top_candidates': [{'text': 'CLI test idea', 'score': 9}],
                'all_ideas': [{'text': 'CLI test idea', 'score': 9}]
            })
            mock_coordinator.return_value = mock_instance

            # Simulate CLI usage pattern
            processor = BatchProcessor(use_async=True, verbose=False)
            batch_items = [
                BatchItem(theme="AI in healthcare", constraints="Budget-friendly"),
                BatchItem(theme="Sustainable farming", constraints="Urban environments")
            ]
            workflow_options = {
                "enable_novelty_filter": True,
                "novelty_threshold": 0.8,
                "verbose": False
            }

            # This is how CLI calls it (from synchronous context)
            summary = processor.process_batch(batch_items, workflow_options)

            # Verify results
            assert summary is not None
            assert summary['total_items'] == 2
            assert 'completed' in summary
            assert 'failed' in summary
            assert 'total_processing_time' in summary

    @pytest.mark.asyncio
    async def test_new_async_usage_pattern_works(self):
        """Test that new async usage pattern works end-to-end.

        This demonstrates the new capability enabled by the fix.
        """
        # Mock to avoid actual API calls
        with patch('src.madspark.utils.batch_processor.AsyncCoordinator') as mock_coordinator:
            mock_instance = Mock()

            # Async mock for workflow
            async def mock_workflow(*args, **kwargs):
                return {
                    'top_candidates': [{'text': 'Async test idea', 'score': 9}],
                    'all_ideas': [{'text': 'Async test idea', 'score': 9}]
                }

            mock_instance.run_workflow = mock_workflow
            mock_coordinator.return_value = mock_instance

            # New async usage pattern (e.g., in web server)
            processor = BatchProcessor(use_async=True, verbose=False)
            batch_items = [
                BatchItem(theme="Async test theme", constraints="Async constraints")
            ]
            workflow_options = {
                "enable_novelty_filter": False,
                "verbose": False
            }

            # Use async API directly
            summary = await processor.process_batch_async(batch_items, workflow_options)

            # Verify results
            assert summary is not None
            assert summary['total_items'] == 1
            assert 'completed' in summary
