"""
MadSpark Multi-Agent System

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API
with advanced reasoning capabilities.
"""

__version__ = "2.1.0"
__author__ = "MadSpark Development Team"

# Core exports
from .core.coordinator import run_multistep_workflow
from .core.async_coordinator import AsyncCoordinator

__all__ = ["run_multistep_workflow", "AsyncCoordinator"]