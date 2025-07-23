"""Verbose Logging Utility

This module provides centralized verbose logging functionality that was previously
scattered throughout coordinator.py. This improves code organization and provides
consistent logging behavior across the application.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class VerboseLogger:
    """Centralized verbose logging for workflow steps and operations.
    
    This class consolidates the verbose logging patterns that were duplicated
    throughout coordinator.py, providing a clean interface for optional detailed
    output during workflow execution.
    """
    
    def __init__(self, enabled: bool = False):
        """Initialize verbose logger.
        
        Args:
            enabled: Whether verbose logging is enabled
        """
        self.enabled = enabled
        
    def step(self, name: str, details: str = "") -> None:
        """Log a workflow step with optional details.
        
        Args:
            name: Name of the step
            details: Optional additional details
        """
        if not self.enabled:
            return
            
        if details:
            print(f"\n🔄 {name}")
            print(f"   {details}")
        else:
            print(f"\n🔄 {name}")
    
    def data(self, label: str, data: str, max_length: int = 500) -> None:
        """Log data with truncation for readability.
        
        Args:
            label: Label for the data
            data: Data content to log
            max_length: Maximum characters to display
        """
        if not self.enabled:
            return
            
        if len(data) > max_length:
            truncated_data = data[:max_length] + f"... (truncated, full length: {len(data)})"
        else:
            truncated_data = data
            
        print(f"📊 {label}:")
        print(f"   {truncated_data}")
    
    def completion(self, name: str, count: int, duration: float, unit: str = "items") -> None:
        """Log completion of a step with metrics.
        
        Args:
            name: Name of the completed step
            count: Number of items processed
            duration: Time taken in seconds
            unit: Unit description for the count
        """
        if not self.enabled:
            return
            
        rate = count / duration if duration > 0 else 0
        print(f"✅ {name} completed: {count} {unit} in {duration:.2f}s ({rate:.1f} {unit}/s)")
    
    def agent_execution(self, step_name: str, agent_name: str, emoji: str, 
                       description: str, temperature: float) -> None:
        """Log agent execution with standard format.
        
        Args:
            step_name: Name of the workflow step
            agent_name: Name of the agent
            emoji: Emoji for visual identification
            description: Description of the agent's task
            temperature: Temperature setting used
        """
        if not self.enabled:
            return
            
        print(f"\n{emoji} {step_name} - {agent_name}")
        print(f"   {description}")
        print(f"   Temperature: {temperature:.1f}")
    
    def subsection(self, title: str, items: Optional[Dict[str, Any]] = None) -> None:
        """Log a subsection with optional key-value items.
        
        Args:
            title: Title of the subsection
            items: Optional dictionary of items to display
        """
        if not self.enabled:
            return
            
        print(f"\n📋 {title}")
        if items:
            for key, value in items.items():
                print(f"   {key}: {value}")
    
    def separator(self, title: str = "") -> None:
        """Print a visual separator with optional title.
        
        Args:
            title: Optional title for the separator
        """
        if not self.enabled:
            return
            
        if title:
            print(f"\n{'='*60}")
            print(f"  {title}")
            print('='*60)
        else:
            print(f"\n{'-'*40}")
    
    def error(self, message: str, details: str = "") -> None:
        """Log an error with optional details.
        
        Args:
            message: Error message
            details: Optional error details
        """
        if not self.enabled:
            return
            
        print(f"\n❌ ERROR: {message}")
        if details:
            print(f"   {details}")
    
    def warning(self, message: str, details: str = "") -> None:
        """Log a warning with optional details.
        
        Args:
            message: Warning message  
            details: Optional warning details
        """
        if not self.enabled:
            return
            
        print(f"\n⚠️  WARNING: {message}")
        if details:
            print(f"   {details}")


# Convenience function for backward compatibility
def log_verbose_step(step_name: str, details: str = "", verbose: bool = False) -> None:
    """Legacy function for backward compatibility."""
    if verbose:
        logger = VerboseLogger(enabled=True)
        logger.step(step_name, details)


def log_verbose_data(label: str, data: str, verbose: bool = False, max_length: int = 500) -> None:
    """Legacy function for backward compatibility."""
    if verbose:
        logger = VerboseLogger(enabled=True)
        logger.data(label, data, max_length)


def log_verbose_completion(step_name: str, count: int, duration: float, verbose: bool = False) -> None:
    """Legacy function for backward compatibility."""
    if verbose:
        logger = VerboseLogger(enabled=True)
        logger.completion(step_name, count, duration)