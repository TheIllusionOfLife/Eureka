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
            # Prefer improved evaluation (post-improvement), fall back to initial
            eval_data = result.get('improved_multi_dimensional_evaluation') or result.get('multi_dimensional_evaluation')

            if eval_data and 'dimension_scores' in eval_data and eval_data['dimension_scores']:
                scores = eval_data['dimension_scores']
                overall = eval_data.get('overall_score', 'N/A')

                # Brief format: show overall + all dimensions on one line
                dim_list = ', '.join([f"{dim.replace('_', ' ').title()}: {score}" for dim, score in scores.items()])
                lines.append(f"**Dimensions (Overall: {overall}):** {dim_list}")

            # Add enhanced reasoning highlights if present
            if 'advocacy' in result and result['advocacy']:
                lines.append("")
                advocacy_data = self._parse_json_field(result['advocacy'])
                if advocacy_data.get('strengths'):
                    strengths_preview = advocacy_data['strengths'][:2]  # Top 2
                    lines.append(f"**✅ Key Strengths:** {', '.join(strengths_preview)}")

            if 'skepticism' in result and result['skepticism']:
                skepticism_data = self._parse_json_field(result['skepticism'])
                if skepticism_data.get('flaws'):
                    flaws_preview = skepticism_data['flaws'][:2]  # Top 2
                    lines.append(f"**⚠️  Key Concerns:** {', '.join(flaws_preview)}")

            if 'logical_inference' in result and result['logical_inference']:
                try:
                    from madspark.utils.output_processor import format_logical_inference_results
                    inference_text = format_logical_inference_results(result['logical_inference'])
                    if inference_text:
                        # Extract first line/insight for brief display
                        first_line = inference_text.split('\n')[1] if '\n' in inference_text else inference_text
                        first_line = first_line.replace('├─ Logical Steps:', '').replace('│  1.', '').strip()
                        if first_line:
                            lines.append("")
                            lines.append(f"**🔍 Logical Insight:** {first_line[:200]}")  # First 200 chars
                except (ImportError, Exception):
                    # Fallback: try to extract from dict
                    inference = result['logical_inference']
                    if isinstance(inference, dict) and 'causal_chains' in inference and inference['causal_chains']:
                        first_chain = inference['causal_chains'][0] if isinstance(inference['causal_chains'], list) else str(inference['causal_chains'])
                        lines.append("")
                        lines.append(f"**🔍 Logical Insight:** {first_chain}")

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
