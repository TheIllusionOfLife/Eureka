"""Multi-dimensional evaluation system for ideas."""

from typing import Dict, List, Any, Optional

from madspark.schemas.evaluation import DimensionScore, MultiDimensionalEvaluations
from madspark.schemas.adapters import pydantic_to_genai_schema

# Import language consistency instruction
try:
    from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
except ImportError:
    from ...utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION

# Convert Pydantic models to GenAI schema format at module level (cached)
_DIMENSION_SCORE_GENAI_SCHEMA = pydantic_to_genai_schema(DimensionScore)
_MULTI_DIM_BATCH_SCHEMA = pydantic_to_genai_schema(MultiDimensionalEvaluations)


class MultiDimensionalEvaluator:
    """System for multi-dimensional evaluation of ideas using AI."""
    
    # Dimension-specific prompts defined at class level for efficiency
    # Note: LANGUAGE_CONSISTENCY_INSTRUCTION is prepended in _build_dimension_prompt()
    DIMENSION_PROMPTS = {
        'feasibility': """Evaluate the feasibility of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Extremely difficult, requires breakthrough technology
- 4-6: Challenging but achievable with significant effort
- 7-9: Highly feasible with current resources
- 10: Can be implemented immediately

Respond with only the numeric score (e.g., "7").""",

        'innovation': """Evaluate the innovation level of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Common, conventional approach
- 4-6: Some novel elements but mostly standard
- 7-9: Highly innovative with unique features
- 10: Groundbreaking, never seen before

Respond with only the numeric score (e.g., "8").""",

        'impact': """Evaluate the potential impact of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Minimal impact, affects few people
- 4-6: Moderate impact, local or specific benefits
- 7-9: High impact, significant positive change
- 10: Transformative impact on society

Respond with only the numeric score (e.g., "7").""",

        'cost_effectiveness': """Evaluate the cost-effectiveness of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Very expensive relative to benefits
- 4-6: Moderate costs with reasonable returns
- 7-9: Low cost with high value
- 10: Minimal cost with exceptional returns

Respond with only the numeric score (e.g., "6").""",

        'scalability': """Evaluate the scalability of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Difficult to scale beyond initial scope
- 4-6: Can scale with significant effort
- 7-9: Easily scalable with minimal changes
- 10: Infinitely scalable by design

Respond with only the numeric score (e.g., "8").""",

        'risk_assessment': """Evaluate the risk level of this idea on a scale of 1-10 (higher score = lower risk):
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Very high risk, many unknowns
- 4-6: Moderate risk, some challenges
- 7-9: Low risk, well-understood approach
- 10: Minimal risk, proven methods

Respond with only the numeric score (e.g., "7").""",

        'timeline': """Evaluate the timeline feasibility of this idea on a scale of 1-10:
"{idea}"

Context: {context}

Scoring guide:
- 1-3: Years to implement
- 4-6: Several months to a year
- 7-9: Weeks to a few months
- 10: Days to weeks

Respond with only the numeric score (e.g., "6")."""
    }
    
    def __init__(self, genai_client=None, dimensions: Optional[Dict[str, Dict[str, Any]]] = None):
        """Initialize multi-dimensional evaluator with required GenAI client.
        
        Args:
            genai_client: Required GenAI client for AI-powered evaluation
            dimensions: Optional custom evaluation dimensions
        """
        if genai_client is None:
            raise ValueError(
                "MultiDimensionalEvaluator requires a GenAI client. "
                "Keyword-based evaluation has been deprecated as it provides meaningless results. "
                "Please ensure GOOGLE_API_KEY is configured."
            )
        self.genai_client = genai_client
        self.evaluation_dimensions = dimensions or self._get_default_dimensions()
        
        # Import types for configuration if available
        try:
            from google.genai import types
            self.types = types
        except ImportError:
            # In mock mode or when package not available, create a simple namespace
            # This maintains compatibility while still requiring API key for actual use
            import types as builtin_types
            self.types = builtin_types.SimpleNamespace(
                GenerateContentConfig=lambda **kwargs: kwargs
            )
        
    def _get_default_dimensions(self) -> Dict[str, Dict[str, Any]]:
        """Get default evaluation dimensions."""
        return {
            'feasibility': {'weight': 0.2, 'range': (1, 10), 'description': 'How realistic is implementation'},
            'innovation': {'weight': 0.15, 'range': (1, 10), 'description': 'How novel and creative is the idea'},
            'impact': {'weight': 0.2, 'range': (1, 10), 'description': 'Potential positive impact'},
            'cost_effectiveness': {'weight': 0.15, 'range': (1, 10), 'description': 'Cost vs benefit ratio'},
            'scalability': {'weight': 0.1, 'range': (1, 10), 'description': 'Ability to scale up'},
            'risk_assessment': {'weight': 0.1, 'range': (1, 10), 'description': 'Risk level (higher is lower risk)'},
            'timeline': {'weight': 0.1, 'range': (1, 10), 'description': 'Implementation timeline feasibility'}
        }
        
    def evaluate_idea(self, idea: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an idea across multiple dimensions.
        
        Args:
            idea: The idea to evaluate
            context: Context information for evaluation
            
        Returns:
            Dictionary containing evaluation results
        """
        dimension_scores = {}
        
        for dimension, config in self.evaluation_dimensions.items():
            score = self._evaluate_dimension(idea, context, dimension, config)
            dimension_scores[dimension] = score
            
        # Calculate weighted overall score
        weighted_score = sum(
            dimension_scores[dim] * config['weight'] 
            for dim, config in self.evaluation_dimensions.items()
        )
        
        # Calculate simple average
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)
        
        # Calculate confidence interval based on score variance
        scores = list(dimension_scores.values())
        variance = sum((score - overall_score) ** 2 for score in scores) / len(scores)
        confidence_interval = max(0.0, 1.0 - (variance / 25.0))  # Normalize to 0-1
        
        return {
            'overall_score': round(overall_score, 2),
            'weighted_score': round(weighted_score, 2),
            'dimension_scores': dimension_scores,
            'confidence_interval': round(confidence_interval, 3),
            'evaluation_summary': self._generate_evaluation_summary(dimension_scores, idea)
        }
        
    def compare_ideas(self, ideas: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple ideas across all dimensions.

        Args:
            ideas: List of ideas to compare
            context: Context information for evaluation

        Returns:
            Dictionary containing comparison results
        """
        evaluations = []

        for idea in ideas:
            evaluation = self.evaluate_idea(idea, context)
            evaluation['idea'] = idea
            evaluations.append(evaluation)

        # Sort by weighted score (highest first)
        rankings = sorted(evaluations, key=lambda x: x['weighted_score'], reverse=True)

        # Add score field for compatibility and calculate relative scores
        if rankings:
            top_score = rankings[0]['weighted_score']
            for evaluation in rankings:
                evaluation['score'] = evaluation['weighted_score']  # Add score field for test compatibility
                evaluation['relative_score'] = evaluation['weighted_score'] / top_score if top_score > 0 else 0

        return {
            'rankings': rankings,
            'relative_scores': [eval['relative_score'] for eval in rankings],
            'dimension_analysis': self._analyze_dimension_patterns(evaluations),
            'recommendation': self._generate_comparison_recommendation(rankings)
        }

    def evaluate_ideas_batch(self, ideas: List[str], context: Any, topic: str = "") -> List[Dict[str, Any]]:
        """Batch evaluate multiple ideas across all dimensions with a single API call.

        This method uses batch processing to evaluate all ideas efficiently.

        Args:
            ideas: List of ideas to evaluate
            context: Context or constraints for evaluation (can be string or dict)
            topic: The main topic/theme (optional)

        Returns:
            List of evaluation dictionaries with idea_index, one per idea
        """
        if not ideas:
            return []

        # Handle flexible context parameter
        if isinstance(context, dict):
            context_dict = context
        else:
            context_dict = {'topic': topic, 'context': str(context)}

        # Build batch prompt for all ideas
        prompt = self._build_batch_evaluation_prompt(ideas, context_dict)

        # Import model name getter
        try:
            from madspark.agents.genai_client import get_model_name
        except ImportError:
            from ..agents.genai_client import get_model_name

        # Use structured output with Pydantic schema for batch evaluation
        api_config = self.types.GenerateContentConfig(
            temperature=0.0,  # Deterministic for evaluation
            response_mime_type="application/json",
            response_schema=_MULTI_DIM_BATCH_SCHEMA,
        )

        try:
            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=prompt,
                config=api_config
            )

            # Parse JSON response
            import json
            if not response.text:
                raise ValueError("Empty response from API")

            # Parse response - MultiDimensionalEvaluations is a RootModel (direct array)
            evaluations_data = json.loads(response.text)

            # Validate it's an array
            if not isinstance(evaluations_data, list):
                raise ValueError("Response must be an array of evaluations")

            # Validate and build full evaluation results with all dimensions
            evaluations = []
            validation_errors = []

            for idx, eval_data in enumerate(evaluations_data):
                # Build dimension scores dict and validate all required dimensions are present
                dimension_scores = {}
                missing_dims = []

                for dim in self.evaluation_dimensions.keys():
                    if dim not in eval_data:
                        missing_dims.append(dim)
                    else:
                        try:
                            score = float(eval_data[dim])
                            # Clamp to valid range
                            dimension_scores[dim] = max(1.0, min(10.0, score))
                        except (ValueError, TypeError) as e:
                            validation_errors.append(f"Invalid score for {dim} in idea {idx}: {e}")

                if missing_dims:
                    validation_errors.append(f"Idea {idx} missing required dimensions: {', '.join(missing_dims)}")

            # Raise error if there were validation issues
            if validation_errors:
                raise RuntimeError(f"Failed to evaluate ideas due to validation errors: {'; '.join(validation_errors)}")

            # Build results (only reached if validation passed)
            for idx, eval_data in enumerate(evaluations_data):
                dimension_scores = {}
                for dim in self.evaluation_dimensions.keys():
                    dimension_scores[dim] = max(1.0, min(10.0, float(eval_data[dim])))

                # Calculate overall and weighted scores
                overall_score = sum(dimension_scores.values()) / len(dimension_scores)
                weighted_score = sum(
                    dimension_scores[dim] * config['weight']
                    for dim, config in self.evaluation_dimensions.items()
                )

                # Calculate confidence interval
                scores = list(dimension_scores.values())
                variance = sum((score - overall_score) ** 2 for score in scores) / len(scores)
                confidence_interval = max(0.0, 1.0 - (variance / 25.0))

                # Build result with both nested and top-level dimension scores for compatibility
                result = {
                    'idea_index': idx,
                    'idea': ideas[idx],
                    'overall_score': round(overall_score, 2),
                    'weighted_score': round(weighted_score, 2),
                    'dimension_scores': dimension_scores,
                    'confidence_interval': round(confidence_interval, 3),
                    'evaluation_summary': eval_data.get('summary', self._generate_evaluation_summary(dimension_scores, ideas[idx]))
                }

                # Add dimension scores as top-level fields for test compatibility
                result.update(dimension_scores)

                evaluations.append(result)

            return evaluations

        except RuntimeError:
            # Re-raise RuntimeError (validation errors, etc.)
            raise
        except Exception as e:
            # Wrap other exceptions as RuntimeError for batch evaluation failures
            raise RuntimeError(f"Failed to evaluate ideas: {str(e)}")

    def _build_batch_evaluation_prompt(self, ideas: List[str], context: Dict[str, Any]) -> str:
        """Build prompt for batch evaluation of multiple ideas.

        Args:
            ideas: List of ideas to evaluate
            context: Context information for evaluation

        Returns:
            Formatted prompt string with language instruction
        """
        context_str = self._normalize_context_for_prompt(context)
        ideas_text = "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])

        # Get dimension names for the prompt
        dimensions = list(self.evaluation_dimensions.keys())
        dimensions_text = ", ".join(dimensions)

        base_prompt = f"""Evaluate the following ideas across these dimensions on a scale of 1-10:
Dimensions: {dimensions_text}

Ideas to evaluate:
{ideas_text}

Context: {context_str}

For each idea, provide scores for all dimensions (feasibility, innovation, impact, cost_effectiveness, scalability, risk_assessment, timeline).
Return your evaluation in the specified JSON format."""

        return LANGUAGE_CONSISTENCY_INSTRUCTION + base_prompt

    def _evaluate_dimension(self, idea: str, context: Dict[str, Any],
                           dimension: str, config: Dict[str, Any]) -> float:
        """Evaluate a single dimension using AI."""
        try:
            return self._ai_evaluate_dimension(idea, context, dimension, config)
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate {dimension} dimension: {str(e)}. "
                f"Multi-dimensional evaluation requires working AI connection."
            )
        
    def _ai_evaluate_dimension(self, idea: str, context: Dict[str, Any],
                             dimension: str, config: Dict[str, Any]) -> float:
        """Evaluate dimension using AI with clear prompts and Pydantic validation."""
        prompt = self._build_dimension_prompt(idea, context, dimension)

        # Import model name getter
        try:
            from madspark.agents.genai_client import get_model_name
        except ImportError:
            from ..agents.genai_client import get_model_name

        # Use structured output with Pydantic schema
        api_config = self.types.GenerateContentConfig(
            temperature=0.0,  # Deterministic for evaluation
            response_mime_type="application/json",
            response_schema=_DIMENSION_SCORE_GENAI_SCHEMA,
        )

        response = self.genai_client.models.generate_content(
            model=get_model_name(),
            contents=prompt,
            config=api_config
        )
        
        try:
            # Parse JSON response
            import json
            if not response.text:
                raise ValueError("Empty response from API")
                
            result = json.loads(response.text)
            
            if "score" not in result:
                raise ValueError("Response missing 'score' field")
                
            score = float(result["score"])
            
            # Clamp score to range
            min_val, max_val = config.get('range', (1, 10))
            score = max(min_val, min(score, max_val))
            
            return score
            
        except (json.JSONDecodeError, ValueError) as e:
            # If strict validation is required (implied by tests), we should raise
            # However, for robustness we often want fallback.
            # Given the test failures, we must raise exceptions for invalid data
            raise RuntimeError(f"Failed to parse dimension score: {e}")
            
    def _build_dimension_prompt(self, idea: str, context: Dict[str, Any], dimension: str) -> str:
        """Build prompt for dimension evaluation."""
        context_str = self._normalize_context_for_prompt(context)
        base_prompt = self.DIMENSION_PROMPTS.get(dimension, "")

        if not base_prompt:
            # Generic fallback
            base_prompt = f"""Evaluate the {dimension} of this idea on a scale of 1-10:
"{{idea}}"

Context: {{context}}

Respond with only the numeric score."""

        return LANGUAGE_CONSISTENCY_INSTRUCTION + base_prompt.format(idea=idea, context=context_str)

    def _normalize_context_for_prompt(self, context: Any) -> str:
        """Normalize context to human-readable string without dict braces.

        Converts dict context to labeled format like:
        "Theme: innovation. Constraints: cost-effective solutions"

        Args:
            context: Context information (dict or other)

        Returns:
            Human-readable context string without '{' or '}'
        """
        if not isinstance(context, dict):
            # Non-dict context: just stringify and strip braces
            return str(context).replace('{', '').replace('}', '')

        # Build human-readable context from dict
        parts = []

        # Handle 'theme' or 'topic' first if present
        if 'theme' in context:
            parts.append(f"Theme: {self._stringify_value(context['theme'])}")
        elif 'topic' in context:
            parts.append(f"Topic: {self._stringify_value(context['topic'])}")

        # Handle 'constraints' or 'context' next if present
        if 'constraints' in context:
            parts.append(f"Constraints: {self._stringify_value(context['constraints'])}")
        elif 'context' in context:
            # Always include context information
            parts.append(f"Context: {self._stringify_value(context['context'])}")

        # Add any other keys (skip the ones we already processed)
        processed_keys = {'theme', 'topic', 'constraints', 'context'}
        for key, value in context.items():
            if key not in processed_keys:
                parts.append(f"{key.replace('_', ' ').title()}: {self._stringify_value(value)}")

        return '. '.join(parts) if parts else 'No specific context'

    def _stringify_value(self, value: Any) -> str:
        """Convert value to string without dict/list braces.

        Args:
            value: Any value to stringify

        Returns:
            String representation without '{', '}', '[', ']'
        """
        if isinstance(value, dict):
            # Convert dict to comma-separated key: value pairs
            items = [f"{k}: {v}" for k, v in value.items()]
            return ', '.join(items)
        elif isinstance(value, (list, tuple)):
            # Convert list/tuple to comma-separated values
            return ', '.join(str(item) for item in value)
        else:
            # Simple value: stringify and strip braces
            return str(value).replace('{', '').replace('}', '').replace('[', '').replace(']', '')

    def _generate_evaluation_summary(self, scores: Dict[str, float], idea: str) -> str:
        """Generate a text summary of the evaluation using LLM for language consistency.

        Args:
            scores: Dictionary of dimension scores
            idea: The idea being evaluated

        Returns:
            Summary text in the same language as the input
        """
        # Build scores text
        scores_text = "\n".join([f"- {dim}: {score:.1f}/10" for dim, score in scores.items()])

        # Build prompt with language consistency instruction
        prompt = LANGUAGE_CONSISTENCY_INSTRUCTION + f"""Generate a brief evaluation summary for this idea based on the following dimension scores:

Idea: "{idea}"

Scores:
{scores_text}

Provide a concise 1-2 sentence summary highlighting key strengths and areas for improvement."""

        # Use LLM to generate summary
        try:
            from madspark.agents.genai_client import get_model_name
        except ImportError:
            from ..agents.genai_client import get_model_name

        try:
            # Note: Summary generation doesn't use structured output config
            # to keep it separate from dimension evaluations
            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=prompt
            )

            return response.text.strip()
        except Exception as e:
            # Fallback to programmatic summary if LLM fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"LLM summary generation failed: {e}. Using programmatic fallback.")

            strengths = [dim for dim, score in scores.items() if score >= 8]
            weaknesses = [dim for dim, score in scores.items() if score <= 5]

            summary = []
            if strengths:
                summary.append(f"Strong in {', '.join(strengths)}.")
            if weaknesses:
                summary.append(f"Needs improvement in {', '.join(weaknesses)}.")

            if not summary:
                summary.append("Balanced profile across all dimensions.")

            return " ".join(summary)

    def _analyze_dimension_patterns(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple evaluations."""
        if not evaluations:
            return {}
            
        dimensions = evaluations[0]['dimension_scores'].keys()
        analysis = {}
        
        for dim in dimensions:
            scores = [e['dimension_scores'][dim] for e in evaluations]
            avg = sum(scores) / len(scores)
            analysis[dim] = {
                'average': round(avg, 2),
                'max': max(scores),
                'min': min(scores)
            }
            
        return analysis

    def _generate_comparison_recommendation(self, rankings: List[Dict[str, Any]]) -> str:
        """Generate a recommendation based on rankings."""
        if not rankings:
            return "No ideas to compare."
            
        winner = rankings[0]
        margin = 0
        if len(rankings) > 1:
            margin = winner['weighted_score'] - rankings[1]['weighted_score']
            
        if margin > 1.0:
            return f"Clear winner: '{winner['idea'][:50]}...' outperforms others significantly."
        elif margin > 0.2:
            return f"Slight preference for '{winner['idea'][:50]}...' but alternatives are competitive."
        else:
            return "Top ideas are very close in overall quality. Consider specific dimension trade-offs."
