"""
Formatter Strategy Pattern for CLI output.

This package provides a modular formatting system for workflow results.
Each formatter implements the ResultFormatter interface and handles a specific output format.
"""

from .base import ResultFormatter
from .brief import BriefFormatter
from .simple import SimpleFormatter
from .detailed import DetailedFormatter
from .summary import SummaryFormatter
from .json_formatter import JsonFormatter
from .factory import FormatterFactory

__all__ = [
    'ResultFormatter',
    'BriefFormatter',
    'SimpleFormatter',
    'DetailedFormatter',
    'SummaryFormatter',
    'JsonFormatter',
    'FormatterFactory',
]
