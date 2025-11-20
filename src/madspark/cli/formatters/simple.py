"""
Simple formatter for user-friendly output with emojis.
"""

import json
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

            # Add multi-dimensional evaluation if available
            # Prefer improved evaluation (post-improvement), fall back to initial
            eval_data = result.get('improved_multi_dimensional_evaluation') or result.get('multi_dimensional_evaluation')

            if eval_data:
                # Show dimension scores in compact format
                if 'dimension_scores' in eval_data and eval_data['dimension_scores']:
                    scores = eval_data['dimension_scores']
                    overall = eval_data.get('overall_score', 'N/A')
                    lines.append(f"📊 Overall: {overall}/10")

                    # Show top dimensions (highest scores) for simple view
                    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    top_3 = sorted_dims[:3]
                    strongest_str = ", ".join(
                        f"{dim.replace('_', ' ').title()} ({score})"
                        for dim, score in top_3
                    )
                    lines.append(f"   ✅ Strongest: {strongest_str}")

                # Show evaluation summary if available
                if 'evaluation_summary' in eval_data:
                    summary = eval_data['evaluation_summary']
                    # Remove the "🧠 Enhanced Analysis:" prefix if present
                    summary = summary.replace('🧠 Enhanced Analysis:\n', '').replace('🧠 Enhanced Analysis:', '')
                    lines.append(f"📋 Analysis: {summary.strip()}")

            # Add enhanced reasoning sections if present
            if 'advocacy' in result and result['advocacy']:
                lines.append("")
                advocacy_data = self._parse_json_field(result['advocacy'])
                strengths = advocacy_data.get('strengths')
                if strengths and isinstance(strengths, list):
                    lines.append("💪 Top Strengths:")
                    for strength in strengths[:3]:  # Top 3
                        # Handle dict items with title/description fields
                        if isinstance(strength, dict):
                            text = strength.get('title') or strength.get('description') or str(strength)
                        else:
                            text = str(strength) if strength else ""
                        if text:
                            lines.append(f"   • {text}")

            if 'skepticism' in result and result['skepticism']:
                skepticism_data = self._parse_json_field(result['skepticism'])
                flaws = skepticism_data.get('flaws')
                if flaws and isinstance(flaws, list):
                    lines.append("⚠️  Key Concerns:")
                    for flaw in flaws[:3]:  # Top 3
                        # Handle dict items with title/description fields
                        if isinstance(flaw, dict):
                            text = flaw.get('title') or flaw.get('description') or str(flaw)
                        else:
                            text = str(flaw) if flaw else ""
                        if text:
                            lines.append(f"   • {text}")

            if 'logical_inference' in result and result['logical_inference']:
                try:
                    from madspark.utils.output_processor import format_logical_inference_results
                    inference_text = format_logical_inference_results(result['logical_inference'])
                    if inference_text:
                        lines.append("🧠 Logical Reasoning:")
                        # Extract first 2-3 key points
                        inference_lines = inference_text.split('\n')
                        point_count = 0
                        for line in inference_lines:
                            if '│  ' in line and point_count < 3:  # Logical step
                                clean_line = line.replace('│  ', '').replace('├─', '').strip()
                                if clean_line and not clean_line.startswith('Logical Steps'):
                                    lines.append(f"   • {clean_line}")
                                    point_count += 1
                except (ImportError, json.JSONDecodeError, KeyError, AttributeError, IndexError) as e:
                    # Fallback: try dict extraction
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Failed to format logical inference: {e}")
                    inference = result['logical_inference']
                    if isinstance(inference, dict):
                        lines.append("🧠 Logical Reasoning:")
                        if 'causal_chains' in inference and inference['causal_chains']:
                            first_chain = inference['causal_chains'][0] if isinstance(inference['causal_chains'], list) else str(inference['causal_chains'])
                            lines.append(f"   • {first_chain}")

            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas

        return "\n".join(lines)
