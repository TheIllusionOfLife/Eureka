"""Temperature Control Interface.

This module provides interfaces for controlling the creativity/temperature
settings of the multi-agent workflow, including CLI argument parsing
and configuration management.
"""
import argparse
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemperatureConfig:
    """Configuration for temperature settings."""
    base_temperature: float = 0.7  # Default for general use
    idea_generation: float = 0.9    # Higher creativity for idea generation
    evaluation: float = 0.3         # Lower for consistent evaluation
    advocacy: float = 0.5           # Balanced for argumentation
    skepticism: float = 0.5         # Balanced for criticism


class TemperatureManager:
    """Manages temperature settings for different workflow stages."""
    
    # Predefined temperature presets
    PRESETS = {
        "conservative": TemperatureConfig(
            base_temperature=0.3,
            idea_generation=0.5,
            evaluation=0.2,
            advocacy=0.3,
            skepticism=0.3
        ),
        "balanced": TemperatureConfig(
            base_temperature=0.7,
            idea_generation=0.8,
            evaluation=0.3,
            advocacy=0.5,
            skepticism=0.5
        ),
        "creative": TemperatureConfig(
            base_temperature=0.9,
            idea_generation=1.0,
            evaluation=0.4,
            advocacy=0.7,
            skepticism=0.7
        ),
        "wild": TemperatureConfig(
            base_temperature=1.0,
            idea_generation=1.0,
            evaluation=0.5,
            advocacy=0.9,
            skepticism=0.9
        )
    }
    
    def __init__(self, config: Optional[TemperatureConfig] = None):
        """Initialize temperature manager.
        
        Args:
            config: Temperature configuration to use
        """
        self.config = config or TemperatureConfig()
    
    @classmethod
    def from_preset(cls, preset_name: str) -> 'TemperatureManager':
        """Create manager from preset.
        
        Args:
            preset_name: Name of the preset to use
            
        Returns:
            TemperatureManager with preset configuration
            
        Raises:
            ValueError: If preset name is not recognized
        """
        if preset_name not in cls.PRESETS:
            available = ", ".join(cls.PRESETS.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")
        
        return cls(cls.PRESETS[preset_name])
    
    @classmethod
    def from_base_temperature(cls, temperature: float) -> 'TemperatureManager':
        """Create manager with scaled temperatures based on a base value.
        
        Args:
            temperature: Base temperature (0.0-1.0)
            
        Returns:
            TemperatureManager with scaled configuration
        """
        # Scale other temperatures relative to base
        config = TemperatureConfig(
            base_temperature=temperature,
            idea_generation=min(1.0, temperature * 1.3),  # Slightly higher for creativity
            evaluation=max(0.1, temperature * 0.4),       # Lower for consistency  
            advocacy=temperature,                          # Same as base
            skepticism=temperature                         # Same as base
        )
        
        return cls(config)
    
    def get_temperature_for_stage(self, stage: str) -> float:
        """Get temperature for a specific workflow stage.
        
        Args:
            stage: Stage name ('idea_generation', 'evaluation', 'advocacy', 'skepticism')
            
        Returns:
            Temperature value for the stage
        """
        stage_mapping = {
            'idea_generation': self.config.idea_generation,
            'evaluation': self.config.evaluation,
            'advocacy': self.config.advocacy,
            'skepticism': self.config.skepticism
        }
        
        return stage_mapping.get(stage, self.config.base_temperature)
    
    def get_overall_temperature(self) -> float:
        """Get the overall/base temperature setting.
        
        Returns:
            The base temperature value
        """
        return self.config.base_temperature
    
    def describe_settings(self) -> str:
        """Get a human-readable description of current settings."""
        return (
            f"Temperature Settings:\n"
            f"  Base: {self.config.base_temperature:.1f}\n"
            f"  Idea Generation: {self.config.idea_generation:.1f}\n"
            f"  Evaluation: {self.config.evaluation:.1f}\n"
            f"  Advocacy: {self.config.advocacy:.1f}\n"
            f"  Skepticism: {self.config.skepticism:.1f}"
        )
    
    @staticmethod
    def describe_presets() -> str:
        """Get description of available presets."""
        descriptions = {
            "conservative": "Low creativity, focused and practical ideas",
            "balanced": "Moderate creativity with good coherence (default)",
            "creative": "High creativity, more varied and innovative ideas",
            "wild": "Maximum creativity, experimental and unconventional ideas"
        }
        
        lines = ["Available temperature presets:"]
        for preset, description in descriptions.items():
            lines.append(f"  {preset}: {description}")
        
        return "\n".join(lines)


def add_temperature_arguments(parser: argparse.ArgumentParser):
    """Add temperature-related arguments to an argument parser.
    
    Args:
        parser: ArgumentParser to add arguments to
    """
    temp_group = parser.add_argument_group('temperature control')
    
    temp_group.add_argument(
        '--temperature', '-t',
        type=float,
        metavar='TEMP',
        help='Base temperature for creativity (0.0-1.0, default: 0.7)'
    )
    
    temp_group.add_argument(
        '--temperature-preset', '-tp',
        choices=list(TemperatureManager.PRESETS.keys()),
        help='Use a predefined temperature preset'
    )
    
    temp_group.add_argument(
        '--list-presets',
        action='store_true',
        help='List available temperature presets and exit'
    )


def create_temperature_manager_from_args(args: argparse.Namespace) -> TemperatureManager:
    """Create temperature manager from parsed command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        TemperatureManager configured according to arguments
    """
    if hasattr(args, 'list_presets') and args.list_presets:
        print(TemperatureManager.describe_presets())
        exit(0)
    
    if hasattr(args, 'temperature_preset') and args.temperature_preset:
        logger.info(f"Using temperature preset: {args.temperature_preset}")
        return TemperatureManager.from_preset(args.temperature_preset)
    
    if hasattr(args, 'temperature') and args.temperature is not None:
        if not 0.0 <= args.temperature <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        logger.info(f"Using base temperature: {args.temperature}")
        return TemperatureManager.from_base_temperature(args.temperature)
    
    # Default configuration
    return TemperatureManager()


# Convenience function for simple temperature scaling
def scale_temperature(base_temp: float, stage: str) -> float:
    """Scale temperature for a specific stage.
    
    Args:
        base_temp: Base temperature value
        stage: Stage name
        
    Returns:
        Scaled temperature for the stage
    """
    manager = TemperatureManager.from_base_temperature(base_temp)
    return manager.get_temperature_for_stage(stage)