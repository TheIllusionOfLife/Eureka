"""JSON parsing package with structured strategies and pre-compiled patterns.

This package provides a robust JSON parsing system with:
- Pre-compiled regex patterns for performance
- Progressive fallback parsing strategies
- Telemetry for strategy usage tracking
- High-performance parser orchestration

Public API:
    - JsonParser: Main parser with fallback strategies
    - patterns: Pre-compiled regex patterns module
    - ParsingTelemetry: Strategy usage tracking
"""

from madspark.utils.json_parsing import patterns

__all__ = ['patterns']
