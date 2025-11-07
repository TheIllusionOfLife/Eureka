"""
Brief formatter for solution-focused output.
"""

from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class BriefFormatter(ResultFormatter):
    """Brief format: Solution-focused output with markdown headers."""

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results in brief mode.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            Brief formatted string
        """
        cleaned_results = self._clean_results(results)
        lines = []

        for i, result in enumerate(cleaned_results, 1):
            # Add markdown header
            if len(cleaned_results) > 1:
                lines.append(f"## Idea {i}")
            else:
                lines.append("## Solution")

            # Show improved idea if available, otherwise original
            final_idea = self._get_final_idea(result)
            final_score = self._get_final_score(result)

            # Handle structured improved idea for brief format
            if isinstance(final_idea, dict) and 'improved_title' in final_idea:
                lines.append(f"{final_idea['improved_title']}")
                if 'improved_description' in final_idea:
                    lines.append("")
                    lines.append(final_idea['improved_description'])
            else:
                # Focus on the solution first - clean presentation
                lines.append(f"{final_idea}")
            lines.append("")

            # Add score information after the solution
            if final_score != 'N/A':
                lines.append(f"**Score:** {final_score}/10")

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
