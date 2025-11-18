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
            lines.append(f"Initial Score: {self._format_score(initial_score)}")
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
                formatted_improved = self._format_score(improved_score)
                if formatted_improved != 'N/A':
                    lines.append(f"📈 Improved Score: {formatted_improved}")
                elif 'improved_idea' in result:
                    lines.append(f"📈 Improved Score: {formatted_improved}")

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
            # Check both initial and improved evaluations (use initial if available, otherwise improved)
            eval_data = result.get('multi_dimensional_evaluation')
            if not eval_data:
                eval_data = result.get('improved_multi_dimensional_evaluation')

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

        structured_data = None
        if isinstance(agent_data, dict):
            structured_data = agent_data
        elif isinstance(agent_data, str) and agent_data.strip():
            try:
                structured_data = json.loads(agent_data)
            except json.JSONDecodeError:
                # Not valid JSON, treat as plain text
                return {"formatted": agent_data, "structured": {}}

        if not structured_data:
            return {"formatted": f"No {agent_type} available", "structured": {}}

        try:
            if agent_type == 'advocacy':
                from madspark.utils.output_processor import format_advocacy_section
                formatted = format_advocacy_section(structured_data)
                return {"formatted": formatted, "structured": structured_data}

            if agent_type == 'skepticism':
                from madspark.utils.output_processor import format_skepticism_section
                formatted = format_skepticism_section(structured_data)
                return {"formatted": formatted, "structured": structured_data}

            if agent_type == 'evaluation':
                # Evaluation is handled differently - already parsed in coordinator
                return {"formatted": agent_data, "structured": structured_data}

            # Unknown agent type - return structured data with default formatting
            fallback_text = json.dumps(structured_data, indent=2)
            return {"formatted": fallback_text, "structured": structured_data}

        except ImportError:
            # Fallback if output_processor is not available
            fallback_text = json.dumps(structured_data, indent=2)
            return {"formatted": fallback_text, "structured": structured_data}
