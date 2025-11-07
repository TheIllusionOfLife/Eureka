"""
JSON formatter for machine-readable output.
"""

import json
from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class JsonFormatter(ResultFormatter):
    """Formatter that outputs results as JSON."""

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results as JSON.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            JSON string representation
        """
        cleaned_results = self._clean_results(results)
        return json.dumps(cleaned_results, indent=2, ensure_ascii=False)
