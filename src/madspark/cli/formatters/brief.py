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

            # Add multi-dimensional evaluation if available (compact format)
            # Check both initial and improved evaluations (use initial if available, otherwise improved)
            eval_data = result.get('multi_dimensional_evaluation')
            if not eval_data:
                eval_data = result.get('improved_multi_dimensional_evaluation')

            if eval_data and 'dimension_scores' in eval_data and eval_data['dimension_scores']:
                scores = eval_data['dimension_scores']
                overall = eval_data.get('overall_score', 'N/A')

                # Brief format: show overall + all dimensions on one line
                dim_list = ', '.join([f"{dim.replace('_', ' ').title()}: {score}" for dim, score in scores.items()])
                lines.append(f"**Dimensions (Overall: {overall}):** {dim_list}")

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
