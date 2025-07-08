"""Tests for interactive CLI mode."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

from interactive_mode import InteractiveSession, run_interactive_mode
from temperature_control import TemperatureManager


class TestInteractiveMode:
    """Test suite for interactive CLI mode."""
    
    def test_interactive_session_init(self):
        """Test InteractiveSession initialization."""
        session = InteractiveSession()
        
        assert isinstance(session.config, dict)
        assert isinstance(session.temp_manager, TemperatureManager)
        assert hasattr(session, 'bookmark_manager')
        
    def test_get_input_with_default(self):
        """Test input with default value."""
        session = InteractiveSession()
        
        # Test with empty input (should return default)
        with patch('builtins.input', return_value=''):
            result = session.get_input_with_default("Test prompt", "default_value")
            assert result == "default_value"
            
        # Test with actual input
        with patch('builtins.input', return_value='user_input'):
            result = session.get_input_with_default("Test prompt", "default_value")
            assert result == "user_input"
            
    def test_get_yes_no(self):
        """Test yes/no input handling."""
        session = InteractiveSession()
        
        # Test default yes
        with patch('builtins.input', return_value=''):
            assert session.get_yes_no("Test?", default=True) is True
            
        # Test explicit yes
        with patch('builtins.input', return_value='y'):
            assert session.get_yes_no("Test?") is True
            
        # Test explicit no
        with patch('builtins.input', return_value='n'):
            assert session.get_yes_no("Test?") is False
            
    @patch('builtins.input')
    def test_get_choice(self, mock_input):
        """Test choice selection."""
        session = InteractiveSession()
        options = [
            ("opt1", "Option 1"),
            ("opt2", "Option 2"),
            ("opt3", "Option 3")
        ]
        
        # Test valid choice
        mock_input.return_value = "2"
        result = session.get_choice("Select option", options)
        assert result == "opt2"
        
        # Test default choice
        mock_input.return_value = ""
        result = session.get_choice("Select option", options, default=0)
        assert result == "opt1"
        
    @patch('builtins.input')
    def test_collect_theme_and_constraints(self, mock_input):
        """Test theme and constraints collection."""
        session = InteractiveSession()
        
        # Set up inputs: theme, constraints, confirm yes
        mock_input.side_effect = [
            "AI in healthcare",
            "Budget-friendly",
            "y"
        ]
        
        theme, constraints = session.collect_theme_and_constraints()
        
        assert theme == "AI in healthcare"
        assert constraints == "Budget-friendly"
        
    def test_configure_temperature_presets(self):
        """Test temperature configuration with presets."""
        session = InteractiveSession()
        
        with patch.object(session, 'get_choice', return_value='creative'):
            temp_manager = session.configure_temperature()
            
            assert session.current_preset == 'creative'
            assert temp_manager.config.base_temperature == 0.9
            
    @patch('builtins.input')
    def test_configure_temperature_custom(self, mock_input):
        """Test custom temperature configuration."""
        session = InteractiveSession()
        
        with patch.object(session, 'get_choice', return_value='custom'):
            # Mock temperature inputs
            mock_input.side_effect = ["0.8", "0.3", "0.6", "0.5"]
            
            temp_manager = session.configure_temperature()
            
            assert temp_manager.get_temperature_for_stage('idea_generation') == 0.8
            assert temp_manager.get_temperature_for_stage('evaluation') == 0.3
            assert temp_manager.get_temperature_for_stage('advocacy') == 0.6
            assert temp_manager.get_temperature_for_stage('skepticism') == 0.5
            
    @patch('builtins.input')
    def test_configure_workflow_options(self, mock_input):
        """Test workflow options configuration."""
        session = InteractiveSession()
        
        # Mock inputs for workflow options
        mock_input.side_effect = [
            "3",      # num_top_candidates
            "y",      # enable novelty filter
            "0.85",   # novelty threshold
            "n",      # enhanced reasoning
            "y",      # multi-dimensional eval
            "n",      # logical inference
            "y",      # async execution
            "n"       # caching
        ]
        
        config = session.configure_workflow_options()
        
        assert config['num_top_candidates'] == 3
        assert config['enable_novelty_filter'] is True
        assert config['novelty_threshold'] == 0.85
        assert config['enhanced_reasoning'] is False
        assert config['multi_dimensional_eval'] is True
        assert config['logical_inference'] is False
        assert config['async'] is True
        assert config['enable_cache'] is False
        
    def test_show_summary(self, capsys):
        """Test configuration summary display."""
        session = InteractiveSession()
        
        config = {
            'num_top_candidates': 2,
            'enable_novelty_filter': True,
            'novelty_threshold': 0.8,
            'enhanced_reasoning': True,
            'multi_dimensional_eval': False,
            'logical_inference': False,
            'async': True,
            'enable_cache': False,
            'output_format': 'json',
            'export': 'csv',
            'export_dir': 'exports',
            'bookmark_results': True,
            'bookmark_tags': ['test', 'demo'],
            'verbose': False
        }
        
        session.show_summary("Test theme", "Test constraints", config)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "Test theme" in output
        assert "Test constraints" in output
        assert "Top candidates: 2" in output
        assert "Novelty filter: Yes" in output
        assert "Enhanced reasoning: Yes" in output