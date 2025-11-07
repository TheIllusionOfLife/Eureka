"""
Base formatter abstract class for result formatting.

Provides shared utilities and defines the formatter interface.
"""

from abc import ABC, abstractmethod
from argparse import Namespace
from typing import Any, Dict, List, Optional


class ResultFormatter(ABC):
    """Abstract base class for result formatters.

    All formatters must implement the format() method to convert
    workflow results into a formatted string output.
    """

    @abstractmethod
    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format workflow results into a string.

        Args:
            results: List of workflow result dictionaries
            args: Command-line arguments namespace

        Returns:
            Formatted string representation of results
        """
        pass

    def _clean_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply cleaning to all results before formatting.

        Args:
            results: List of result dictionaries

        Returns:
            Cleaned results
        """
        try:
            from madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
        except ImportError:
            from ...utils.improved_idea_cleaner import clean_improved_ideas_in_results
        return clean_improved_ideas_in_results(results)

    def _format_score(self, score: Any, precision: int = 2) -> str:
        """Format a score value for display.

        Args:
            score: Score value (float, int, or 'N/A')
            precision: Decimal precision for floats

        Returns:
            Formatted score string
        """
        if score == 'N/A' or score is None:
            return 'N/A'
        try:
            return f"{float(score):.{precision}f}"
        except (ValueError, TypeError):
            return str(score)

    def _get_final_idea(self, result: Dict[str, Any]) -> Any:
        """Get the final idea (improved or original).

        Args:
            result: Result dictionary

        Returns:
            Final idea text or structured dict
        """
        improved = result.get('improved_idea')
        if improved and improved != 'No improved idea available':
            return improved

        original = result.get('idea')
        if original:
            return original

        return 'No idea available'

    def _get_final_score(self, result: Dict[str, Any]) -> Any:
        """Get the final score (improved or initial).

        Args:
            result: Result dictionary

        Returns:
            Final score value
        """
        return result.get('improved_score', result.get('initial_score', 'N/A'))

    def _handle_structured_idea(self, idea: Any) -> str:
        """Handle structured improved idea (dict or string).

        Args:
            idea: Improved idea (dict or string)

        Returns:
            Formatted idea text
        """
        if isinstance(idea, dict) and 'improved_title' in idea:
            parts = []
            parts.append(idea['improved_title'])
            if 'improved_description' in idea:
                parts.append("")
                parts.append(idea['improved_description'])
            return "\n".join(parts)
        return str(idea) if idea else ''

    def _format_improvement_section(self, result: Dict[str, Any]) -> Optional[str]:
        """Format improvement section with score delta.

        Args:
            result: Result dictionary

        Returns:
            Formatted improvement text or None if not applicable
        """
        if 'improved_idea' not in result and 'improved_score' not in result:
            return None

        improved_idea = result.get('improved_idea')
        improved_score = result.get('improved_score', 'N/A')
        score_delta = result.get('score_delta', 0)
        is_meaningful = result.get('is_meaningful_improvement', True)

        lines = []
        if improved_idea and is_meaningful:
            idea_text = self._handle_structured_idea(improved_idea)
            lines.append(f"✨ Improved: {idea_text}")

        if improved_score != 'N/A':
            lines.append(f"📈 Final Score: {self._format_score(improved_score)}")

        if score_delta > 0:
            lines.append(f"⬆️  Improvement: +{score_delta:.1f}")
        elif score_delta < 0:
            lines.append(f"⬇️  Change: {score_delta:.1f}")
        elif not is_meaningful:
            lines.append("✅ Already well-developed - no significant improvements needed")

        return "\n".join(lines) if lines else None

    def _format_score_display(self, initial: Any, improved: Any, delta: Any = None) -> str:
        """Format score display with initial, improved, and delta.

        Args:
            initial: Initial score
            improved: Improved score
            delta: Score delta

        Returns:
            Formatted score display
        """
        lines = []
        if initial != 'N/A' and initial is not None:
            lines.append(f"Initial Score: {self._format_score(initial)}")
        if improved != 'N/A' and improved is not None:
            lines.append(f"Improved Score: {self._format_score(improved)}")
        if delta is not None and delta != 0:
            if delta > 0:
                lines.append(f"⬆️  Improvement: +{delta:.1f}")
            elif delta < 0:
                lines.append(f"⬇️  Change: {delta:.1f}")
            else:
                lines.append("➡️  No significant change")
        return "\n".join(lines)
