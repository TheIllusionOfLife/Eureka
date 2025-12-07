"""
Summary formatter for improved ideas with multi-dimensional evaluation.
"""

from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class SummaryFormatter(ResultFormatter):
    """Summary format: Improved ideas with multi-dimensional evaluation."""

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results in summary mode.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            Summary formatted string
        """
        cleaned_results = self._clean_results(results)
        lines = [f"Generated {len(cleaned_results)} improved ideas:\n"]

        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"--- IMPROVED IDEA {i} ---")

            # Get cleaned improved idea (already cleaned by clean_improved_ideas_in_results)
            # Fall back to original idea if no improved idea available
            idea_source = result.get('improved_idea')
            if not idea_source or idea_source == 'No improved idea available':
                idea_source = self._get_final_idea(result)

            idea_text = self._handle_structured_idea(idea_source) or 'No idea available'

            if len(idea_text) > 500:
                truncated = idea_text[:497] + "..."
                lines.append(truncated)
                lines.append("\n[Note: Full improved idea available in text or JSON format]")
            else:
                lines.append(idea_text)

            lines.append(f"\nImproved Score: {self._format_score(result.get('improved_score', 'N/A'))}")

            # Add multi-dimensional evaluation if available
            # Prefer improved evaluation (post-improvement), fall back to initial
            eval_data = result.get('improved_multi_dimensional_evaluation') or result.get('multi_dimensional_evaluation')
            if eval_data:
                lines.append("\nMulti-Dimensional Evaluation:")
                # Only show overall score if it has a value
                overall_score = eval_data.get('overall_score')
                if overall_score is not None:
                    lines.append(f"  Overall Score: {overall_score}")

                # Only show dimension scores that have actual values (no N/A clutter)
                if 'dimension_scores' in eval_data and eval_data['dimension_scores']:
                    scores = eval_data['dimension_scores']
                    # Dimension display mapping for DRY formatting
                    dimension_display = {
                        "feasibility": "Feasibility",
                        "innovation": "Innovation",
                        "impact": "Impact",
                        "cost_effectiveness": "Cost-Effectiveness",
                        "scalability": "Scalability",
                        "risk_assessment": "Risk Assessment",
                        "timeline": "Timeline",
                    }
                    for key, display_name in dimension_display.items():
                        if scores.get(key) is not None:
                            suffix = " (lower is better)" if key == "risk_assessment" else ""
                            lines.append(f"  - {display_name}: {scores[key]}{suffix}")

                if 'evaluation_summary' in eval_data and eval_data.get('evaluation_summary'):
                    lines.append(f"  Summary: {eval_data['evaluation_summary']}")

            lines.append("")  # Empty line between ideas

        return "\n".join(lines)
