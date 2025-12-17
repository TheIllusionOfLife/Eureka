"""
JSON formatter for machine-readable output.

Note on field ordering: JSON output preserves the raw result structure without
reordering fields. While human-readable formatters (brief, simple, detailed, summary)
display logical_inference before improved_idea to reflect workflow order, JSON
consumers should access fields by key rather than relying on position. The workflow
order is: logical_inference (Step 4.5) -> improved_idea (Step 5).
"""

import json
from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class JsonFormatter(ResultFormatter):
    """Formatter that outputs results as JSON.

    Note: JSON objects are unordered by specification. Consumers should access
    fields by key name. The workflow order (logical_inference before improved_idea)
    is reflected in human-readable formats but not enforced in JSON structure.
    """

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results as JSON.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            JSON string representation with all result fields preserved
        """
        cleaned_results = self._clean_results(results)
        return json.dumps(cleaned_results, indent=2, ensure_ascii=False)
