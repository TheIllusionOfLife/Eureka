"""
Simple formatter for user-friendly output with emojis.
"""

from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class SimpleFormatter(ResultFormatter):
    """Simple format: Clean, user-friendly output with emoji indicators."""

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results in simple mode.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            Simple formatted string with emojis
        """
        cleaned_results = self._clean_results(results)
        lines = []

        for i, result in enumerate(cleaned_results, 1):
            if len(cleaned_results) > 1:
                lines.append(f"━━━ Idea {i} ━━━")

            # Original idea
            original_idea = result.get('idea', 'No idea available')
            initial_score = result.get('initial_score', 'N/A')

            lines.append(f"💭 Original: {original_idea}")
            lines.append(f"📊 Initial Score: {initial_score}")

            # Show improvement if available and meaningful
            if 'improved_idea' in result or 'improved_score' in result or 'score_delta' in result:
                improved_idea = result.get('improved_idea')
                improved_score = result.get('improved_score', 'N/A')
                score_delta = result.get('score_delta', 0)

                is_meaningful_improvement = result.get('is_meaningful_improvement', True)
                idea_text = self._handle_structured_idea(improved_idea) if improved_idea else ""

                if is_meaningful_improvement and idea_text:
                    lines.append(f"✨ Improved: {idea_text}")
                    lines.append(f"📈 Final Score: {self._format_score(improved_score)}")
                    if score_delta > 0:
                        lines.append(f"⬆️  Improvement: +{score_delta:.1f}")
                else:
                    # Show only final score, indicate no meaningful improvement
                    lines.append(f"📈 Final Score: {self._format_score(improved_score)}")
                    lines.append("✅ Already well-developed - no significant improvements needed")

            # Add evaluation summary if available (clean format)
            if 'multi_dimensional_evaluation' in result:
                eval_data = result['multi_dimensional_evaluation']
                if eval_data and 'evaluation_summary' in eval_data:
                    summary = eval_data['evaluation_summary']
                    # Remove the "🧠 Enhanced Analysis:" prefix if present
                    summary = summary.replace('🧠 Enhanced Analysis:\n', '').replace('🧠 Enhanced Analysis:', '')
                    lines.append(f"📋 Analysis: {summary.strip()}")

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
