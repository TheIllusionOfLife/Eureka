"""
Brief formatter for solution-focused output.
"""

import json
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

            # Show analysis BEFORE solution (reflects workflow order)
            # Enhanced reasoning highlights come first
            if 'advocacy' in result and result['advocacy']:
                advocacy_data = self._parse_json_field(result['advocacy'])
                raw_strengths = advocacy_data.get('strengths')
                if raw_strengths:
                    # Normalize to a list and ensure each item is a string
                    if isinstance(raw_strengths, list):
                        strengths_items = raw_strengths[:2]
                    else:
                        strengths_items = [raw_strengths]

                    # Convert each item to string (handle dicts with title/description)
                    strengths_preview = []
                    for item in strengths_items:
                        if isinstance(item, dict):
                            # Prefer title, fall back to description, then stringify
                            text = item.get('title') or item.get('description') or str(item)
                        else:
                            text = str(item) if item else ""
                        if text:
                            strengths_preview.append(text)

                    if strengths_preview:
                        lines.append(f"**✅ Key Strengths:** {', '.join(strengths_preview)}")

            if 'skepticism' in result and result['skepticism']:
                skepticism_data = self._parse_json_field(result['skepticism'])
                raw_flaws = skepticism_data.get('flaws')
                if raw_flaws:
                    # Normalize to a list and ensure each item is a string
                    if isinstance(raw_flaws, list):
                        flaws_items = raw_flaws[:2]
                    else:
                        flaws_items = [raw_flaws]

                    # Convert each item to string (handle dicts with title/description)
                    flaws_preview = []
                    for item in flaws_items:
                        if isinstance(item, dict):
                            # Prefer title, fall back to description, then stringify
                            text = item.get('title') or item.get('description') or str(item)
                        else:
                            text = str(item) if item else ""
                        if text:
                            flaws_preview.append(text)

                    if flaws_preview:
                        lines.append(f"**⚠️  Key Concerns:** {', '.join(flaws_preview)}")

            # Logical inference (shown before solution as it informs improvement)
            if 'logical_inference' in result and result['logical_inference']:
                try:
                    from madspark.utils.output_processor import format_logical_inference_results
                    inference_text = format_logical_inference_results(result['logical_inference'])
                    if inference_text:
                        # Extract first line/insight for brief display
                        lines_list = inference_text.split('\n')
                        first_line = lines_list[1] if len(lines_list) > 1 else (lines_list[0] if lines_list else "")
                        first_line = first_line.replace('├─ Logical Steps:', '').replace('│  1.', '').strip()
                        if first_line:
                            lines.append(f"**🔍 Logical Insight:** {first_line[:200]}")  # First 200 chars
                except (ImportError, json.JSONDecodeError, KeyError, AttributeError, IndexError) as e:
                    # Fallback: try to extract from dict
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Failed to format logical inference: {e}")
                    inference = result['logical_inference']
                    if isinstance(inference, dict) and 'causal_chains' in inference and inference['causal_chains']:
                        first_chain = inference['causal_chains'][0] if isinstance(inference['causal_chains'], list) else str(inference['causal_chains'])
                        lines.append(f"**🔍 Logical Insight:** {first_chain}")

            # Now show the solution (improved idea)
            final_idea = self._get_final_idea(result)
            final_score = self._get_final_score(result)

            lines.append("")  # Separator before solution

            # Handle structured improved idea for brief format
            if isinstance(final_idea, dict) and 'improved_title' in final_idea:
                lines.append(f"**Solution:** {final_idea['improved_title']}")
                if 'improved_description' in final_idea:
                    lines.append("")
                    lines.append(final_idea['improved_description'])
            else:
                # Focus on the solution - clean presentation
                lines.append(f"**Solution:** {final_idea}")
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

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
