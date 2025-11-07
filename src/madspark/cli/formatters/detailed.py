"""
Detailed formatter for comprehensive output with all agent interactions.
"""

import json
import re
from argparse import Namespace
from typing import Any, Dict, List

from .base import ResultFormatter


class DetailedFormatter(ResultFormatter):
    """Detailed format: Show all agent interactions and analysis."""

    def format(self, results: List[Dict[str, Any]], args: Namespace) -> str:
        """Format results in detailed mode.

        Args:
            results: List of result dictionaries
            args: Command-line arguments

        Returns:
            Detailed formatted string with all agent interactions
        """
        cleaned_results = self._clean_results(results)
        lines = ["=" * 80]
        lines.append("MADSPARK MULTI-AGENT IDEA GENERATION RESULTS")
        lines.append("=" * 80)

        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"\n--- IDEA {i} ---")

            # Strip leading number from idea text if present
            idea_text = result.get('idea', 'No idea available')
            # Remove pattern like "3. " or "10. " from the beginning
            idea_text = re.sub(r'^\d+\.\s+', '', idea_text)
            lines.append(idea_text)

            initial_score = result.get('initial_score', 'N/A')
            if initial_score != 'N/A':
                lines.append(f"Initial Score: {initial_score:.2f}")
            else:
                lines.append(f"Initial Score: {initial_score}")
            lines.append(f"Initial Critique: {result.get('initial_critique', 'No critique available')}")

            # Agent feedback with structured parsing
            if 'advocacy' in result:
                advocacy_data = self._parse_structured_agent_data(result['advocacy'], 'advocacy')
                lines.append(f"\n{advocacy_data['formatted']}")

            if 'skepticism' in result:
                skepticism_data = self._parse_structured_agent_data(result['skepticism'], 'skepticism')
                lines.append(f"\n{skepticism_data['formatted']}")

            # Show improvement section if we have improved idea OR score improvements
            if 'improved_idea' in result or 'improved_score' in result or 'score_delta' in result:
                # Show improved idea if available
                if 'improved_idea' in result:
                    lines.append("\n✨ Improved Idea:")
                    improved_idea = result['improved_idea']

                    # Handle structured improved idea (dictionary format)
                    if isinstance(improved_idea, dict):
                        try:
                            from madspark.utils.output_processor import format_improved_idea_section
                            formatted_improved = format_improved_idea_section(improved_idea)
                            lines.append(formatted_improved)
                        except ImportError:
                            # Fallback: extract key information
                            if 'improved_title' in improved_idea:
                                lines.append(f"**{improved_idea['improved_title']}**")
                            if 'improved_description' in improved_idea:
                                lines.append(improved_idea['improved_description'])
                            if 'key_improvements' in improved_idea:
                                lines.append("\nKey Improvements:")
                                for improvement in improved_idea['key_improvements']:
                                    lines.append(f"• {improvement}")
                            if 'implementation_steps' in improved_idea:
                                lines.append("\nImplementation Steps:")
                                for step_i, step in enumerate(improved_idea['implementation_steps'], 1):
                                    lines.append(f"{step_i}. {step}")
                    else:
                        # Handle string format
                        lines.append(improved_idea)

                # Show improved score if available
                improved_score = result.get('improved_score', 'N/A')
                if improved_score != 'N/A':
                    lines.append(f"📈 Improved Score: {improved_score:.2f}")
                elif 'improved_idea' not in result:
                    # Don't show score line if there's no improved idea and no improved score
                    pass
                else:
                    lines.append(f"📈 Improved Score: {improved_score}")

                # Show score delta if available
                if 'score_delta' in result:
                    score_delta = result['score_delta']
                    if score_delta > 0:
                        lines.append(f"⬆️  Improvement: +{score_delta:.1f}")
                    elif score_delta < 0:
                        lines.append(f"⬇️  Change: {score_delta:.1f}")
                    else:
                        lines.append("➡️  No significant change")

            # Multi-dimensional evaluation with enhanced formatting
            if 'multi_dimensional_evaluation' in result:
                eval_data = result['multi_dimensional_evaluation']
                if eval_data:
                    try:
                        from madspark.utils.output_processor import format_multi_dimensional_scores

                        overall_score = eval_data.get('overall_score', 0)
                        dimension_scores = eval_data.get('dimension_scores', {})

                        if dimension_scores:
                            formatted_scores = format_multi_dimensional_scores(dimension_scores, overall_score)
                            lines.append(f"\n{formatted_scores}")
                        else:
                            lines.append(f"\n📊 Overall Score: {overall_score}")

                        if 'evaluation_summary' in eval_data:
                            lines.append(f"\n💡 Summary: {eval_data['evaluation_summary']}")

                    except ImportError:
                        # Fallback to simple formatting
                        lines.append("\n📊 Multi-Dimensional Evaluation:")
                        lines.append(f"  Overall Score: {eval_data.get('overall_score', 'N/A')}")

                        if 'dimension_scores' in eval_data:
                            scores = eval_data['dimension_scores']
                            for dim, score in scores.items():
                                lines.append(f"  • {dim.replace('_', ' ').title()}: {score}")

            # Logical inference analysis (when --logical flag is used)
            if 'logical_inference' in result and result['logical_inference']:
                try:
                    from madspark.utils.output_processor import format_logical_inference_results
                    inference_data = result['logical_inference']
                    formatted_inference = format_logical_inference_results(inference_data)
                    if formatted_inference:
                        lines.append(f"\n{formatted_inference}")
                except ImportError:
                    # Fallback formatting
                    lines.append("\n🔍 Logical Inference Analysis:")
                    inference_data = result['logical_inference']
                    if 'causal_chains' in inference_data:
                        lines.append("  Causal Chains:")
                        for chain in inference_data['causal_chains']:
                            lines.append(f"    • {chain}")

            lines.append("-" * 80)

        return "\n".join(lines)

    def _parse_structured_agent_data(self, agent_data: str, agent_type: str) -> Dict[str, Any]:
        """Parse structured JSON agent data or fallback to text parsing.

        Args:
            agent_data: Raw agent response (JSON or text)
            agent_type: Type of agent ('advocacy', 'skepticism', 'evaluation')

        Returns:
            Dictionary with parsed and formatted data
        """
        if not agent_data:
            return {"formatted": f"No {agent_type} available", "structured": {}}

        # Handle both string (JSON) and dict inputs
        if isinstance(agent_data, str):
            if not agent_data.strip():
                return {"formatted": f"No {agent_type} available", "structured": {}}
            agent_data_str = agent_data
        else:
            # Already a dict, convert to JSON string for processing
            agent_data_str = json.dumps(agent_data)

        try:
            # Try to parse as JSON first
            if isinstance(agent_data, dict):
                structured_data = agent_data
            else:
                structured_data = json.loads(agent_data_str)

            if agent_type == 'advocacy':
                from madspark.utils.output_processor import format_advocacy_section
                formatted = format_advocacy_section(structured_data)
                return {"formatted": formatted, "structured": structured_data}

            elif agent_type == 'skepticism':
                from madspark.utils.output_processor import format_skepticism_section
                formatted = format_skepticism_section(structured_data)
                return {"formatted": formatted, "structured": structured_data}

            elif agent_type == 'evaluation':
                # Evaluation is handled differently - already parsed in coordinator
                return {"formatted": agent_data, "structured": structured_data}

            else:
                # Unknown agent type - return structured data with default formatting
                fallback_text = json.dumps(structured_data, indent=2) if structured_data else agent_data
                return {"formatted": fallback_text, "structured": structured_data}

        except (json.JSONDecodeError, TypeError, ImportError):
            # Fall back to text format for backward compatibility
            fallback_text = agent_data if isinstance(agent_data, str) else str(agent_data)
            return {"formatted": fallback_text, "structured": {}}
