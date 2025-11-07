"""
Factory for creating formatter instances.
"""

from typing import Optional, Type, List, Dict

from .base import ResultFormatter
from .brief import BriefFormatter
from .simple import SimpleFormatter
from .detailed import DetailedFormatter
from .summary import SummaryFormatter
from .json_formatter import JsonFormatter


class FormatterFactory:
    """Factory for creating result formatters based on format type."""

    _formatters: Dict[str, Type[ResultFormatter]] = {
        'brief': BriefFormatter,
        'simple': SimpleFormatter,
        'detailed': DetailedFormatter,
        'summary': SummaryFormatter,
        'json': JsonFormatter,
        'text': DetailedFormatter,  # Legacy alias for detailed
    }

    @classmethod
    def create(cls, format_name: Optional[str]) -> ResultFormatter:
        """Create a formatter instance based on format name.

        Args:
            format_name: Name of the format ('brief', 'simple', 'detailed', 'summary', 'json', 'text')
                        If None or unknown, defaults to 'brief'

        Returns:
            ResultFormatter instance
        """
        if format_name is None:
            format_name = 'brief'

        formatter_class = cls._formatters.get(format_name, BriefFormatter)
        return formatter_class()

    @classmethod
    def register_formatter(cls, format_name: str, formatter_class: Type[ResultFormatter]) -> None:
        """Register a custom formatter.

        Args:
            format_name: Name to register the formatter under
            formatter_class: Formatter class to register
        """
        cls._formatters[format_name] = formatter_class

    @classmethod
    def available_formats(cls) -> List[str]:
        """Get list of available format names.

        Returns:
            List of format names
        """
        return list(cls._formatters.keys())
