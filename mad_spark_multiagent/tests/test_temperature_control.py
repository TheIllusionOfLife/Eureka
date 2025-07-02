"""Tests for the temperature control module."""
import pytest
import argparse
from mad_spark_multiagent.temperature_control import (
    TemperatureConfig,
    TemperatureManager,
    add_temperature_arguments,
    create_temperature_manager_from_args,
    scale_temperature
)


class TestTemperatureConfig:
    """Test cases for TemperatureConfig dataclass."""
    
    def test_default_config(self):
        """Test default temperature configuration."""
        config = TemperatureConfig()
        
        assert config.base_temperature == 0.7
        assert config.idea_generation == 0.9
        assert config.evaluation == 0.3
        assert config.advocacy == 0.5
        assert config.skepticism == 0.5
    
    def test_custom_config(self):
        """Test custom temperature configuration."""
        config = TemperatureConfig(
            base_temperature=0.8,
            idea_generation=1.0,
            evaluation=0.2,
            advocacy=0.6,
            skepticism=0.4
        )
        
        assert config.base_temperature == 0.8
        assert config.idea_generation == 1.0
        assert config.evaluation == 0.2
        assert config.advocacy == 0.6
        assert config.skepticism == 0.4


class TestTemperatureManager:
    """Test cases for TemperatureManager class."""
    
    def test_default_manager(self):
        """Test manager with default configuration."""
        manager = TemperatureManager()
        
        assert manager.get_temperature_for_stage('idea_generation') == 0.9
        assert manager.get_temperature_for_stage('evaluation') == 0.3
        assert manager.get_temperature_for_stage('advocacy') == 0.5
        assert manager.get_temperature_for_stage('skepticism') == 0.5
        assert manager.get_temperature_for_stage('unknown_stage') == 0.7  # base temperature
    
    def test_custom_config_manager(self):
        """Test manager with custom configuration."""
        config = TemperatureConfig(base_temperature=0.8, idea_generation=1.0)
        manager = TemperatureManager(config)
        
        assert manager.get_temperature_for_stage('idea_generation') == 1.0
        assert manager.get_temperature_for_stage('unknown_stage') == 0.8
    
    def test_preset_managers(self):
        """Test managers created from presets."""
        # Test conservative preset
        conservative = TemperatureManager.from_preset('conservative')
        assert conservative.config.base_temperature == 0.3
        assert conservative.config.idea_generation == 0.5
        assert conservative.config.evaluation == 0.2
        
        # Test creative preset
        creative = TemperatureManager.from_preset('creative')
        assert creative.config.base_temperature == 0.9
        assert creative.config.idea_generation == 1.0
        assert creative.config.evaluation == 0.4
        
        # Test wild preset
        wild = TemperatureManager.from_preset('wild')
        assert wild.config.base_temperature == 1.0
        assert wild.config.idea_generation == 1.0
        assert wild.config.advocacy == 0.9
    
    def test_invalid_preset(self):
        """Test error handling for invalid preset."""
        with pytest.raises(ValueError) as exc_info:
            TemperatureManager.from_preset('invalid_preset')
        
        assert 'Unknown preset' in str(exc_info.value)
        assert 'conservative' in str(exc_info.value)  # Should list available presets
    
    def test_from_base_temperature(self):
        """Test creating manager from base temperature."""
        manager = TemperatureManager.from_base_temperature(0.6)
        
        assert manager.config.base_temperature == 0.6
        assert manager.config.idea_generation == min(1.0, 0.6 * 1.3)  # 0.78
        assert manager.config.evaluation == max(0.1, 0.6 * 0.4)  # 0.24
        assert manager.config.advocacy == 0.6
        assert manager.config.skepticism == 0.6
    
    def test_base_temperature_bounds(self):
        """Test base temperature scaling respects bounds."""
        # Test lower bound for evaluation
        manager = TemperatureManager.from_base_temperature(0.1)
        assert manager.config.evaluation >= 0.1
        
        # Test upper bound for idea generation
        manager = TemperatureManager.from_base_temperature(1.0)
        assert manager.config.idea_generation <= 1.0
    
    def test_describe_settings(self):
        """Test settings description."""
        manager = TemperatureManager()
        description = manager.describe_settings()
        
        assert 'Temperature Settings:' in description
        assert 'Base: 0.7' in description
        assert 'Idea Generation: 0.9' in description
        assert 'Evaluation: 0.3' in description
        assert 'Advocacy: 0.5' in description
        assert 'Skepticism: 0.5' in description
    
    def test_describe_presets(self):
        """Test preset descriptions."""
        description = TemperatureManager.describe_presets()
        
        assert 'Available temperature presets:' in description
        assert 'conservative:' in description
        assert 'balanced:' in description
        assert 'creative:' in description
        assert 'wild:' in description
        assert 'Low creativity' in description
        assert 'Maximum creativity' in description


class TestArgumentParsing:
    """Test argument parsing functions."""
    
    def test_add_temperature_arguments(self):
        """Test adding temperature arguments to parser."""
        parser = argparse.ArgumentParser()
        add_temperature_arguments(parser)
        
        # Test that arguments were added
        help_text = parser.format_help()
        assert '--temperature' in help_text
        assert '--temperature-preset' in help_text
        assert '--list-presets' in help_text
        assert 'temperature control' in help_text  # Group name
    
    def test_create_manager_from_temperature_arg(self):
        """Test creating manager from temperature argument."""
        args = argparse.Namespace(
            temperature=0.8,
            temperature_preset=None,
            list_presets=False
        )
        
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 0.8
    
    def test_create_manager_from_preset_arg(self):
        """Test creating manager from preset argument."""
        args = argparse.Namespace(
            temperature=None,
            temperature_preset='creative',
            list_presets=False
        )
        
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 0.9  # Creative preset
    
    def test_create_manager_default(self):
        """Test creating manager with no arguments."""
        args = argparse.Namespace(
            temperature=None,
            temperature_preset=None,
            list_presets=False
        )
        
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 0.7  # Default
    
    def test_temperature_validation(self):
        """Test temperature argument validation."""
        args = argparse.Namespace(
            temperature=1.5,  # Invalid - above 1.0
            temperature_preset=None,
            list_presets=False
        )
        
        with pytest.raises(ValueError) as exc_info:
            create_temperature_manager_from_args(args)
        
        assert 'between 0.0 and 1.0' in str(exc_info.value)
        
        # Test negative temperature
        args.temperature = -0.1
        with pytest.raises(ValueError):
            create_temperature_manager_from_args(args)
    
    def test_preset_priority_over_temperature(self):
        """Test that preset argument takes priority over temperature."""
        args = argparse.Namespace(
            temperature=0.8,
            temperature_preset='conservative',  # Should override temperature
            list_presets=False
        )
        
        manager = create_temperature_manager_from_args(args)
        assert manager.config.base_temperature == 0.3  # Conservative preset, not 0.8


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_scale_temperature(self):
        """Test the scale_temperature convenience function."""
        # Test idea generation scaling
        temp = scale_temperature(0.7, 'idea_generation')
        expected = TemperatureManager.from_base_temperature(0.7).get_temperature_for_stage('idea_generation')
        assert temp == expected
        
        # Test evaluation scaling
        temp = scale_temperature(0.7, 'evaluation')
        expected = TemperatureManager.from_base_temperature(0.7).get_temperature_for_stage('evaluation')
        assert temp == expected
        
        # Test unknown stage (should return base)
        temp = scale_temperature(0.7, 'unknown_stage')
        assert temp == 0.7


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_all_preset_names_valid(self):
        """Test that all preset names can be used to create managers."""
        for preset_name in TemperatureManager.PRESETS.keys():
            manager = TemperatureManager.from_preset(preset_name)
            assert manager is not None
            assert hasattr(manager.config, 'base_temperature')
    
    def test_temperature_bounds_in_presets(self):
        """Test that all preset temperatures are within valid bounds."""
        for preset_name, config in TemperatureManager.PRESETS.items():
            assert 0.0 <= config.base_temperature <= 1.0
            assert 0.0 <= config.idea_generation <= 1.0
            assert 0.0 <= config.evaluation <= 1.0
            assert 0.0 <= config.advocacy <= 1.0
            assert 0.0 <= config.skepticism <= 1.0
    
    def test_stage_name_case_sensitivity(self):
        """Test that stage names are case sensitive."""
        manager = TemperatureManager()
        
        # Correct case
        temp1 = manager.get_temperature_for_stage('idea_generation')
        
        # Wrong case - should return base temperature
        temp2 = manager.get_temperature_for_stage('IDEA_GENERATION')
        
        assert temp1 != temp2
        assert temp2 == manager.config.base_temperature