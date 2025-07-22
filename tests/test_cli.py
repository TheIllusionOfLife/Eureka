"""Comprehensive tests for MadSpark CLI modules."""
import pytest
import sys
import io
from unittest.mock import Mock, patch, MagicMock
from contextlib import redirect_stdout, redirect_stderr

from madspark.cli.cli import main as cli_main
from madspark.cli.interactive_mode import InteractiveSession


class TestCLIMain:
    """Test cases for CLI main functionality."""
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_basic_execution(self, mock_workflow):
        """Test basic CLI execution."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 8.0,
                "initial_critique": "Good idea",
                "advocacy": "Strong potential",
                "skepticism": "Some concerns",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 9.0,
                "improved_critique": "Great improvement"
            }
        ]
        
        # Mock sys.argv
        test_args = ["cli.py", "AI automation", "Cost-effective"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # Should complete without error
                assert result is None or result == 0
            except SystemExit as e:
                # CLI might exit with 0 on success
                assert e.code == 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_with_verbose_flag(self, mock_workflow):
        """Test CLI with verbose flag."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 7.5,
                "initial_critique": "Decent idea",
                "advocacy": "Good foundation",
                "skepticism": "Needs work",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 8.5,
                "improved_critique": "Better now"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--verbose"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                # Check that verbose=True was passed
                args, kwargs = mock_workflow.call_args
                assert kwargs.get('verbose') == True
            except SystemExit as e:
                assert e.code == 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_with_temperature_settings(self, mock_workflow):
        """Test CLI with temperature settings."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 7.5,
                "initial_critique": "Decent idea",
                "advocacy": "Good foundation",
                "skepticism": "Needs work",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 8.5,
                "improved_critique": "Better now"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--temperature", "0.8"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                args, kwargs = mock_workflow.call_args
                # Check that temperature_manager is present and has the right temperature
                # Note: idea_generation temperature is scaled to min(1.0, base * 1.3)
                temp_manager = kwargs.get('temperature_manager')
                assert temp_manager is not None
                # For base temperature 0.8, idea generation is scaled to min(1.0, 0.8 * 1.3) = 1.0
                assert temp_manager.get_temperature_for_stage('idea_generation') == 1.0
                assert temp_manager.config.base_temperature == 0.8
            except SystemExit as e:
                assert e.code == 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_with_temperature_preset(self, mock_workflow):
        """Test CLI with temperature preset."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 7.5,
                "initial_critique": "Decent idea",
                "advocacy": "Good foundation",
                "skepticism": "Needs work",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 8.5,
                "improved_critique": "Better now"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--temperature-preset", "creative"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                args, kwargs = mock_workflow.call_args
                # Check that temperature_manager is present and configured for creative preset
                temp_manager = kwargs.get('temperature_manager')
                assert temp_manager is not None
                # Creative preset should have high creativity temperature
                assert temp_manager.get_temperature_for_stage('idea_generation') >= 0.8
            except SystemExit as e:
                assert e.code == 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_with_timeout(self, mock_workflow):
        """Test CLI with timeout parameter."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 7.5,
                "initial_critique": "Decent idea",
                "advocacy": "Good foundation",
                "skepticism": "Needs work",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 8.5,
                "improved_critique": "Better now"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--timeout", "30"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                args, kwargs = mock_workflow.call_args
                assert kwargs.get('timeout') == 30
            except SystemExit as e:
                assert e.code == 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_with_enhanced_reasoning(self, mock_workflow):
        """Test CLI with enhanced reasoning flag."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea",
                "initial_score": 7.5,
                "initial_critique": "Decent idea",
                "advocacy": "Good foundation",
                "skepticism": "Needs work",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 8.5,
                "improved_critique": "Better now"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--enhanced-reasoning"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                args, kwargs = mock_workflow.call_args
                assert kwargs.get('enhanced_reasoning') == True
            except SystemExit as e:
                assert e.code == 0
    
    def test_cli_missing_arguments(self):
        """Test CLI with missing required arguments."""
        test_args = ["cli.py"]  # Missing theme and constraints
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # Should exit with error
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code != 0
    
    def test_cli_invalid_temperature(self):
        """Test CLI with invalid temperature value."""
        test_args = ["cli.py", "AI automation", "Cost-effective", "--temperature", "2.5"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # Should handle invalid temperature
                assert False, "Should have raised SystemExit or handled error"
            except SystemExit as e:
                assert e.code != 0
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_workflow_failure(self, mock_workflow):
        """Test CLI when workflow fails."""
        mock_workflow.return_value = None  # Simulate workflow failure
        
        test_args = ["cli.py", "AI automation", "Cost-effective"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # Should handle workflow failure gracefully
                assert result is None or result != 0
            except SystemExit as e:
                assert e.code != 0


class TestInteractiveMode:
    """Test cases for interactive CLI mode."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock interactive session."""
        session = InteractiveSession()
        return session
    
    def test_interactive_session_initialization(self, mock_session):
        """Test interactive session initialization."""
        assert mock_session is not None
        assert hasattr(mock_session, 'config')
        assert hasattr(mock_session, 'temp_manager')
        assert hasattr(mock_session, 'bookmark_manager')
    
    def test_interactive_session_clear_screen(self, mock_session):
        """Test screen clearing functionality."""
        # Should not raise any exceptions
        mock_session.clear_screen()
    
    def test_interactive_session_print_header(self, mock_session):
        """Test header printing functionality."""
        # Capture output
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            mock_session.print_header()
        
        output = captured_output.getvalue()
        assert "MadSpark" in output or len(output) > 0
    
    @patch('builtins.input', side_effect=['AI automation', 'Cost-effective', 'y'])
    def test_interactive_session_user_input(self, mock_input, mock_session):
        """Test user input handling."""
        # This would test the actual input flow
        # For now, just verify the session can handle mocked input
        assert mock_session.config is not None
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_interactive_session_keyboard_interrupt(self, mock_input, mock_session):
        """Test handling of keyboard interrupt."""
        # Should handle KeyboardInterrupt gracefully by exiting
        with pytest.raises(SystemExit) as e:
            mock_session.get_input_with_default("test prompt")
        assert e.value.code == 0
    
    @patch('builtins.input', side_effect=EOFError())
    def test_interactive_session_eof_handling(self, mock_input, mock_session):
        """Test handling of EOF (Ctrl+D)."""
        # Should handle EOFError gracefully by exiting
        with pytest.raises(SystemExit) as e:
            mock_session.get_input_with_default("test prompt")
        assert e.value.code == 0


class TestCLIIntegration:
    """Integration tests for CLI components."""
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_full_workflow_integration(self, mock_workflow):
        """Test full CLI workflow integration."""
        mock_workflow.return_value = [
            {
                "idea": "AI-Powered Productivity Suite: A comprehensive productivity platform",
                "initial_score": 7.5,
                "initial_critique": "Strong concept with good market demand and technical feasibility, but faces competition and complexity challenges",
                "advocacy": "Solves real problems, Scalable solution, Improves workplace efficiency",
                "skepticism": "High development cost, Market saturation, Medium to high risk",
                "multi_dimensional_evaluation": {
                    "innovation_score": 8,
                    "feasibility_score": 7
                },
                "improved_idea": "Enhanced AI-Powered Productivity Suite with unique differentiators",
                "improved_score": 8.5,
                "improved_critique": "Improved positioning and feature set to stand out from competition"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective solutions", "--verbose", "--enhanced-reasoning"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                mock_workflow.assert_called_once()
                
                # Verify all expected parameters were passed
                args, kwargs = mock_workflow.call_args
                assert kwargs.get('verbose') == True
                assert kwargs.get('enhanced_reasoning') == True
                
            except SystemExit as e:
                assert e.code == 0
    
    def test_cli_error_handling_integration(self):
        """Test CLI error handling integration."""
        # Test with various error scenarios
        error_scenarios = [
            ["cli.py"],  # Missing arguments
            ["cli.py", "theme"],  # Missing constraints
            ["cli.py", "theme", "constraints", "--temperature", "invalid"],  # Invalid temperature
            ["cli.py", "theme", "constraints", "--timeout", "-1"],  # Invalid timeout
        ]
        
        for test_args in error_scenarios:
            with patch.object(sys, 'argv', test_args):
                try:
                    result = cli_main()
                    # Should handle errors gracefully
                except SystemExit as e:
                    # Expected for invalid arguments
                    assert e.code != 0
                except Exception as e:
                    # Should not raise unhandled exceptions
                    assert False, f"Unhandled exception: {e}"
    
    @patch('madspark.cli.cli.run_multistep_workflow')
    def test_cli_output_formatting(self, mock_workflow):
        """Test CLI output formatting."""
        mock_workflow.return_value = [
            {
                "idea": "Test Idea: Test description",
                "initial_score": 8.0,
                "initial_critique": "Good test idea",
                "advocacy": "Strong potential",
                "skepticism": "Some concerns",
                "multi_dimensional_evaluation": None,
                "improved_idea": "Improved Test Idea",
                "improved_score": 9.0,
                "improved_critique": "Great improvement"
            }
        ]
        
        test_args = ["cli.py", "AI automation", "Cost-effective", "--verbose"]
        
        # Capture output
        captured_output = io.StringIO()
        captured_error = io.StringIO()
        
        with patch.object(sys, 'argv', test_args):
            with redirect_stdout(captured_output), redirect_stderr(captured_error):
                try:
                    result = cli_main()
                    
                    output = captured_output.getvalue()
                    error = captured_error.getvalue()
                    
                    # Should produce formatted output
                    assert len(output) > 0 or len(error) > 0
                    
                except SystemExit as e:
                    assert e.code == 0


class TestCLIUtilities:
    """Test cases for CLI utility functions."""
    
    def test_argument_parsing_edge_cases(self):
        """Test argument parsing edge cases."""
        # Test with empty strings
        test_args = ["cli.py", "", ""]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # Should handle empty strings appropriately
            except SystemExit as e:
                # May exit with error for empty arguments
                pass
    
    def test_cli_help_functionality(self):
        """Test CLI help functionality."""
        test_args = ["cli.py", "--help"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                assert False, "Should have raised SystemExit for help"
            except SystemExit as e:
                assert e.code == 0  # Help should exit with 0
    
    def test_cli_version_functionality(self):
        """Test CLI version functionality if available."""
        test_args = ["cli.py", "--version"]
        
        with patch.object(sys, 'argv', test_args):
            try:
                result = cli_main()
                # May or may not have version flag
            except SystemExit as e:
                # Version flag may exit with 0 or 2 (unrecognized)
                pass