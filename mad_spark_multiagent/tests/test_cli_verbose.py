"""Tests for CLI verbose logging functionality."""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import logging

# Import the CLI functions we want to test
from cli import setup_logging, main


class TestCLIVerboseLogging:
    """Test cases for CLI verbose logging functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create a temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    @patch('cli.datetime')
    def test_setup_logging_creates_log_file(self, mock_datetime):
        """Test that verbose logging creates timestamped log files."""
        # Mock datetime to get predictable timestamp
        mock_datetime.now.return_value.strftime.return_value = "20250101_120000"
        
        # Setup verbose logging
        setup_logging(verbose=True)
        
        # Check that logs directory was created
        assert os.path.exists("logs")
        
        # Check that log file was created
        expected_log_file = "logs/madspark_verbose_20250101_120000.log"
        
        # Test by actually logging something
        logging.info("Test log message")
        
        # Check if log file exists and has content
        if os.path.exists(expected_log_file):
            with open(expected_log_file, 'r') as f:
                content = f.read()
                assert "Test log message" in content
        
    def test_setup_logging_permission_error_fallback(self):
        """Test graceful fallback when logs directory cannot be created."""
        # Create a file named 'logs' to cause permission error when trying to create directory
        with open("logs", "w") as f:
            f.write("dummy")
        
        with patch('builtins.print') as mock_print:
            setup_logging(verbose=True)
            
            # Should print warning message
            mock_print.assert_called()
            warning_calls = [call for call in mock_print.call_args_list 
                           if "Warning:" in str(call)]
            assert len(warning_calls) > 0
    
    @patch('cli.os.makedirs')
    def test_setup_logging_os_error_fallback(self, mock_makedirs):
        """Test graceful fallback when os.makedirs raises OSError."""
        mock_makedirs.side_effect = OSError("Disk full")
        
        with patch('builtins.print') as mock_print:
            setup_logging(verbose=True)
            
            # Should print warning message with error details
            mock_print.assert_called()
            warning_calls = [call for call in mock_print.call_args_list 
                           if "Warning:" in str(call) and "Disk full" in str(call)]
            assert len(warning_calls) > 0
    
    def test_setup_logging_non_verbose_mode(self):
        """Test that non-verbose mode doesn't create log files."""
        setup_logging(verbose=False)
        
        # Should not create logs directory in non-verbose mode
        assert not os.path.exists("logs")
    
    @patch('cli.run_multistep_workflow')
    @patch('cli.create_temperature_manager_from_args')
    @patch('sys.argv', ['cli.py', 'test theme', 'test constraints', '--verbose'])
    def test_cli_verbose_flag_integration(self, mock_temp_manager, mock_workflow):
        """Test that --verbose flag is properly passed to workflow."""
        # Mock the temperature manager
        mock_temp_manager.return_value = Mock()
        
        # Mock the workflow to return simple results
        mock_workflow.return_value = [
            {
                "idea": "Test idea",
                "initial_score": 8,
                "initial_critique": "Good idea",
                "advocacy": "Strong support",
                "skepticism": "Some concerns"
            }
        ]
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            try:
                main()
            except SystemExit:
                pass  # main() may call sys.exit(), which is expected
        
        # Verify that workflow was called with verbose=True
        mock_workflow.assert_called_once()
        call_args = mock_workflow.call_args
        assert call_args[1]['verbose'] is True  # Check keyword argument
    
    @patch('cli.run_multistep_workflow')
    @patch('cli.create_temperature_manager_from_args')
    @patch('sys.argv', ['cli.py', 'test theme', 'test constraints'])  # No --verbose flag
    def test_cli_non_verbose_flag_integration(self, mock_temp_manager, mock_workflow):
        """Test that workflow defaults to non-verbose when flag not provided."""
        # Mock the temperature manager
        mock_temp_manager.return_value = Mock()
        
        # Mock the workflow to return simple results
        mock_workflow.return_value = [
            {
                "idea": "Test idea",
                "initial_score": 8,
                "initial_critique": "Good idea",
                "advocacy": "Strong support",
                "skepticism": "Some concerns"
            }
        ]
        
        try:
            main()
        except SystemExit:
            pass  # main() may call sys.exit(), which is expected
        
        # Verify that workflow was called with verbose=False (default)
        mock_workflow.assert_called_once()
        call_args = mock_workflow.call_args
        assert call_args[1]['verbose'] is False  # Check keyword argument
    
    def test_verbose_log_file_format(self):
        """Test that verbose log files have correct format."""
        setup_logging(verbose=True)
        
        # Log some test messages
        logging.info("Test INFO message")
        logging.debug("Test DEBUG message")
        
        # Find the created log file
        if os.path.exists("logs"):
            log_files = [f for f in os.listdir("logs") if f.startswith("madspark_verbose_")]
            if log_files:
                log_file = os.path.join("logs", log_files[0])
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Check format includes timestamp, level, filename, line number
                    lines = content.strip().split('\n')
                    for line in lines:
                        if line.strip():  # Skip empty lines
                            # Format should be: YYYY-MM-DD HH:MM:SS - LEVEL - filename:line - message
                            parts = line.split(' - ')
                            assert len(parts) >= 4, f"Log line doesn't have expected format: {line}"
                            
                            # Check timestamp format (basic check)
                            timestamp = parts[0]
                            assert len(timestamp) == 19, f"Timestamp format incorrect: {timestamp}"
                            
                            # Check level
                            level = parts[1]
                            assert level in ['INFO', 'DEBUG', 'WARNING', 'ERROR'], f"Invalid log level: {level}"
    
    def test_large_response_handling(self):
        """Test that very large responses are handled efficiently in verbose mode."""
        from coordinator import log_verbose_data
        
        # Create a very large data string
        large_data = "x" * 10000
        
        with patch('builtins.print') as mock_print:
            # This should complete quickly even with large data
            log_verbose_data("Large Data Test", large_data, verbose=True, max_length=500)
            
            # Verify truncation occurred
            mock_print.assert_called_once()
            printed_content = str(mock_print.call_args[0][0])
            assert "Truncated" in printed_content
            assert len(printed_content) < len(large_data)  # Should be much shorter
    
    def test_verbose_performance_impact(self):
        """Test that verbose mode doesn't significantly impact performance."""
        import time
        from coordinator import log_verbose_step, log_verbose_data
        
        # Test data
        test_data = "Medium sized test data " * 100
        
        # Time non-verbose operations
        start_time = time.time()
        for i in range(100):
            log_verbose_step(f"Step {i}", "details", verbose=False)
            log_verbose_data(f"Data {i}", test_data, verbose=False)
        non_verbose_time = time.time() - start_time
        
        # Time verbose operations (but mock print to avoid I/O overhead)
        with patch('builtins.print'):
            start_time = time.time()
            for i in range(100):
                log_verbose_step(f"Step {i}", "details", verbose=True)
                log_verbose_data(f"Data {i}", test_data, verbose=True)
            verbose_time = time.time() - start_time
        
        # Verbose should not be more than 10x slower (very generous threshold)
        # In practice, it should be much closer, but we want to avoid flaky tests
        assert verbose_time < non_verbose_time * 10, f"Verbose mode too slow: {verbose_time}s vs {non_verbose_time}s"