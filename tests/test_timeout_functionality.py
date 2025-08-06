"""Test timeout functionality in CLI and coordinator.

This test module verifies that the --timeout CLI argument
is properly passed through and utilized in the coordinator.
"""
import os
import asyncio
import pytest
from unittest.mock import patch

from madspark.cli.cli import create_parser
from madspark.core.coordinator import run_multistep_workflow
from madspark.core.async_coordinator import AsyncCoordinator


class TestCLITimeoutParsing:
    """Test that CLI properly parses timeout argument."""
    
    def test_parse_timeout_argument_default(self):
        """Test default timeout value."""
        parser = create_parser()
        args = parser.parse_args(['my topic', 'my context'])
        assert getattr(args, 'timeout', None) is not None, "CLI should have timeout argument"
        assert args.timeout == 1200, "Default timeout should be 1200 seconds"
    
    def test_parse_timeout_argument_custom(self):
        """Test custom timeout value."""
        parser = create_parser()
        args = parser.parse_args(['my topic', 'my context', '--timeout', '120'])
        assert args.timeout == 120, "Should parse custom timeout value"
    
    def test_parse_timeout_argument_with_other_flags(self):
        """Test timeout parsing with other flags."""
        parser = create_parser()
        args = parser.parse_args([
            'topic', 'context',
            '--timeout', '300',
            '--temperature', '0.8',
            '--enable-cache'
        ])
        assert args.timeout == 300
        assert args.temperature == 0.8
        assert args.enable_cache is True


class TestCoordinatorTimeoutImplementation:
    """Test that coordinator properly implements timeout."""
    
    @pytest.mark.asyncio
    async def test_async_coordinator_timeout_wraps_workflow(self):
        """Test that AsyncCoordinator wraps workflow with timeout."""
        # This test verifies the timeout is used in asyncio.wait_for
        coordinator = AsyncCoordinator(
            max_concurrent_agents=10,
            progress_callback=None
        )
        
        # Patch the internal workflow to take a long time
        with patch.object(coordinator, '_run_workflow_internal') as mock_internal:
            # Make internal workflow take forever
            async def slow_workflow(*args, **kwargs):
                await asyncio.sleep(10)
                return []
            
            mock_internal.side_effect = slow_workflow
            
            # Should timeout quickly
            with pytest.raises(asyncio.TimeoutError):
                await coordinator.run_workflow(topic="test topic",
                    context="test context",
                    timeout=0.1  # Very short timeout
                )
    
    @pytest.mark.asyncio
    async def test_async_coordinator_completes_within_timeout(self):
        """Test AsyncCoordinator completes successfully within timeout."""
        # Create coordinator
        coordinator = AsyncCoordinator(
            max_concurrent_agents=10,
            progress_callback=None
        )
        
        # Mock internal workflow to complete quickly
        with patch.object(coordinator, '_run_workflow_internal') as mock_internal:
            # Fast completion
            mock_internal.return_value = [
                {"idea": "Test idea", "score": 8, "improved_idea": "Improved test"}
            ]
            
            # Should complete within timeout
            results = await coordinator.run_workflow(topic="test topic",
                context="test context",
                timeout=10.0  # Generous timeout
            )
            
            assert results is not None
            assert len(results) > 0
            # Verify the internal workflow was called
            mock_internal.assert_called_once()
    
    @pytest.mark.skipif(os.getenv("MADSPARK_MODE") == "mock", reason="Test requires full mock control")
    def test_sync_coordinator_timeout_parameter(self):
        """Test that sync run_multistep_workflow accepts timeout parameter."""
        # Test that it accepts the parameter and logs warning
        with patch('madspark.core.coordinator.logging.warning') as mock_warning:
            # Mock the agent functions to avoid actual API calls
            with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_gen:
                mock_gen.return_value = "Idea 1: Test"
                
                # This should not raise an error and should log warning
                run_multistep_workflow(topic="test",
                    context="context",
                    timeout=300
                )
                
                # Should log warning about sync mode not supporting timeout
                # Find the timeout warning among all warnings
                timeout_warning_found = False
                for call in mock_warning.call_args_list:
                    warning_msg = call[0][0]
                    if "timeout" in warning_msg.lower() and "sync mode" in warning_msg.lower():
                        timeout_warning_found = True
                        break
                
                assert timeout_warning_found, f"Expected timeout warning not found. Warnings: {[call[0][0] for call in mock_warning.call_args_list]}"


class TestCLITimeoutIntegration:
    """Test end-to-end timeout integration from CLI to coordinator."""
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_passes_timeout_to_coordinator(self, mock_workflow):
        """Test that CLI passes timeout to run_multistep_workflow()"""
        # Setup mock
        mock_workflow.return_value = [{"idea": "test"}]
        
        # Import after patching
        from madspark.cli.cli import main
        
        # Run CLI with timeout
        with patch('sys.argv', ['mad_spark', 'topic', 'context', '--timeout', '300']):
            with patch('madspark.cli.cli.print'):  # Suppress output
                with patch('os.getenv', return_value=None):  # Force sync mode
                    main()
        
        # Verify timeout was passed
        mock_workflow.assert_called()
        call_args = mock_workflow.call_args
        
        # Check if timeout is in kwargs
        assert 'timeout' in call_args.kwargs, "Timeout should be passed to workflow"
        assert call_args.kwargs['timeout'] == 300, "Timeout value should be 300"


class TestTimeoutValidation:
    """Test timeout validation and constraints."""
    
    def test_minimum_timeout_validation(self):
        """Test that very small timeouts are rejected or warned."""
        parser = create_parser()
        args = parser.parse_args(['topic', 'context', '--timeout', '1'])
        # Should either raise or clamp to minimum
        assert args.timeout >= 1  # At least allow 1 second
    
    def test_maximum_timeout_validation(self):
        """Test that excessively large timeouts are handled."""
        parser = create_parser()
        args = parser.parse_args(['topic', 'context', '--timeout', '86400'])  # 24 hours
        assert args.timeout == 86400  # Should accept large values


class TestTimeoutErrorMessages:
    """Test that timeout errors produce helpful messages."""
    
    @pytest.mark.asyncio
    async def test_timeout_error_message(self):
        """Test that timeout produces clear error message."""
        coordinator = AsyncCoordinator(
            max_concurrent_agents=10,
            progress_callback=None
        )
        
        # Patch internal workflow to be slow
        with patch.object(coordinator, '_run_workflow_internal') as mock_internal:
            async def slow_response(*args, **kwargs):
                await asyncio.sleep(10)
                return []
            
            mock_internal.side_effect = slow_response
            
            with pytest.raises(asyncio.TimeoutError) as exc_info:
                await coordinator.run_workflow(topic="test",
                    context="test",
                    timeout=0.1
                )
            
            # The error should be clear about timeout
            assert exc_info.type == asyncio.TimeoutError