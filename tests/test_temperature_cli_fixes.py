"""Tests for temperature range validation and CLI option fixes."""
import pytest
import argparse
from unittest.mock import patch
import sys

from madspark.utils.temperature_control import (
    TemperatureManager,
    create_temperature_manager_from_args,
    add_temperature_arguments
)
from madspark.utils.errors import TemperatureError
from madspark.cli.cli import create_parser


class TestTemperatureRangeValidation:
    """Test temperature range validation supports 0.0-2.0."""
    
    def test_temperature_2_0_should_be_valid(self):
        """Test that temperature 2.0 is accepted."""
        # Create args with temperature 2.0
        args = argparse.Namespace(
            temperature=2.0,
            temperature_preset=None,
            list_presets=False
        )
        
        # This should NOT raise an error when fixed
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 2.0
    
    def test_temperature_1_5_should_be_valid(self):
        """Test that temperature 1.5 is accepted."""
        args = argparse.Namespace(
            temperature=1.5,
            temperature_preset=None,
            list_presets=False
        )
        
        # This should NOT raise an error when fixed
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 1.5
    
    def test_temperature_2_1_should_be_invalid(self):
        """Test that temperature 2.1 is rejected."""
        args = argparse.Namespace(
            temperature=2.1,
            temperature_preset=None,
            list_presets=False
        )
        
        # This should raise an error
        with pytest.raises(TemperatureError) as exc_info:
            create_temperature_manager_from_args(args)
        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)
    
    def test_temperature_negative_should_be_invalid(self):
        """Test that negative temperature is rejected."""
        args = argparse.Namespace(
            temperature=-0.1,
            temperature_preset=None,
            list_presets=False
        )
        
        with pytest.raises(TemperatureError) as exc_info:
            create_temperature_manager_from_args(args)
        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)
    
    def test_wild_preset_uses_temperature_2_0(self):
        """Test that wild preset can use temperature 2.0 for idea generation."""
        manager = TemperatureManager.from_preset("wild")
        
        # Wild preset should use 2.0 for idea generation
        assert manager.config.idea_generation == 2.0
        assert manager.get_temperature_for_stage('idea_generation') == 2.0


class TestCreativityOptionRemoval:
    """Test that --creativity option is removed and --temperature-preset is used."""
    
    def test_creativity_option_should_not_exist(self):
        """Test that --creativity option is removed from CLI."""
        parser = create_parser()
        
        # Test that attempting to use --creativity raises an error
        with pytest.raises(SystemExit):
            parser.parse_args(['test topic', '--creativity', 'creative'])
    
    def test_temperature_preset_option_exists(self):
        """Test that --temperature-preset option exists and includes wild."""
        parser = create_parser()
        
        # Find the temperature-preset action
        temp_preset_action = None
        for group in parser._action_groups:
            for action in group._group_actions:
                if '--temperature-preset' in action.option_strings:
                    temp_preset_action = action
                    break
        
        assert temp_preset_action is not None
        assert 'wild' in temp_preset_action.choices
        assert 'conservative' in temp_preset_action.choices
        assert 'balanced' in temp_preset_action.choices
        assert 'creative' in temp_preset_action.choices
    
    def test_help_text_mentions_temperature_range_2_0(self):
        """Test that help text shows correct temperature range."""
        parser = argparse.ArgumentParser()
        add_temperature_arguments(parser)
        
        # Find temperature argument
        temp_action = None
        for action in parser._actions:
            if '--temperature' in action.option_strings:
                temp_action = action
                break
        
        assert temp_action is not None
        assert "0.0-2.0" in temp_action.help


class TestCLIIntegration:
    """Integration tests for CLI with temperature options."""
    
    @pytest.fixture
    def mock_cli_environment(self):
        """Fixture to set up common CLI test environment."""
        with patch('madspark.cli.cli.os.getenv') as mock_getenv, \
             patch('madspark.cli.commands.workflow_executor.run_multistep_workflow') as mock_workflow:
            mock_getenv.return_value = "test_api_key"
            mock_workflow.return_value = [{"idea": "test", "score": 8.0}]
            yield mock_getenv, mock_workflow
    
    def run_cli_with_args(self, args):
        """Helper method to run CLI with given arguments."""
        with patch.object(sys, 'argv', args):
            from madspark.cli.cli import main
            main()
    
    def test_cli_with_temperature_2_0(self, mock_cli_environment):
        """Test CLI accepts temperature 2.0."""
        # This should not raise an error when fixed
        # Use --top-ideas 1 to force sync execution (which uses run_multistep_workflow)
        self.run_cli_with_args(['cli.py', 'test topic', '--temperature', '2.0', '--no-bookmark', '--top-ideas', '1'])
    
    def test_cli_with_wild_preset(self, mock_cli_environment):
        """Test CLI accepts wild preset."""
        # Should not raise an error
        # Use --top-ideas 1 to force sync execution (which uses run_multistep_workflow)
        self.run_cli_with_args(['cli.py', 'test topic', '--temperature-preset', 'wild', '--no-bookmark', '--top-ideas', '1'])
    
    def test_cli_rejects_creativity_option(self, mock_cli_environment):
        """Test CLI rejects --creativity option."""
        with pytest.raises(SystemExit):
            self.run_cli_with_args(['cli.py', 'test topic', '--creativity', 'wild', '--no-bookmark'])