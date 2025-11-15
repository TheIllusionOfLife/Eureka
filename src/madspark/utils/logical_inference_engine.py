"""
Logical Inference Engine for MadSpark.

This module provides LLM-based logical inference capabilities to replace
the hardcoded templates with genuine logical analysis.
"""
import logging
import json
from enum import Enum
from typing import Dict, Any, List, Optional, Union
# Removed dataclass import - using Pydantic models instead
import re

# Third-party imports
from google import genai

# Pydantic schemas for logical inference
from madspark.schemas.logical_inference import (
    InferenceResult as PydanticInferenceResult,
    CausalAnalysis,
    ConstraintAnalysis,
    ContradictionAnalysis,
    ImplicationsAnalysis
)
from madspark.schemas.adapters import pydantic_to_genai_schema

logger = logging.getLogger(__name__)

# Convert Pydantic models to GenAI schema format at module level (cached)
_FULL_ANALYSIS_GENAI_SCHEMA = pydantic_to_genai_schema(PydanticInferenceResult)
_CAUSAL_ANALYSIS_GENAI_SCHEMA = pydantic_to_genai_schema(CausalAnalysis)
_CONSTRAINT_ANALYSIS_GENAI_SCHEMA = pydantic_to_genai_schema(ConstraintAnalysis)
_CONTRADICTION_ANALYSIS_GENAI_SCHEMA = pydantic_to_genai_schema(ContradictionAnalysis)
_IMPLICATIONS_ANALYSIS_GENAI_SCHEMA = pydantic_to_genai_schema(ImplicationsAnalysis)


class InferenceType(Enum):
    """Types of logical inference analysis."""
    FULL = "full"
    CAUSAL = "causal"
    CONSTRAINTS = "constraints"
    CONTRADICTION = "contradiction"
    IMPLICATIONS = "implications"


# Type alias for backward compatibility - actual model defined in schemas/logical_inference.py
# This module now uses Pydantic models from madspark.schemas.logical_inference
InferenceResult = PydanticInferenceResult


class LogicalInferenceEngine:
    """
    LLM-based logical inference engine for analyzing ideas.
    
    Replaces hardcoded logical templates with genuine reasoning using
    the language model's capabilities.
    """
    
    def __init__(self, genai_client):
        """
        Initialize the inference engine.
        
        Args:
            genai_client: Google GenAI client instance
        """
        self.genai_client = genai_client
        self.inference_types = list(InferenceType)
        
        # Prompt templates
        self.prompts = {
            InferenceType.FULL: self._get_full_analysis_prompt,
            InferenceType.CAUSAL: self._get_causal_analysis_prompt,
            InferenceType.CONSTRAINTS: self._get_constraint_analysis_prompt,
            InferenceType.CONTRADICTION: self._get_contradiction_analysis_prompt,
            InferenceType.IMPLICATIONS: self._get_implications_analysis_prompt,
        }
    
    def analyze(
        self,
        idea: str,
        topic: str,
        context: str,
        analysis_type: Union[InferenceType, str] = InferenceType.FULL
    ) -> InferenceResult:
        """
        Perform logical inference analysis on an idea.

        Args:
            idea: The generated idea to analyze
            topic: Original topic/topic
            context: Constraints and requirements
            analysis_type: Type of analysis to perform

        Returns:
            InferenceResult containing the analysis
        """
        # Convert string to enum if needed
        if isinstance(analysis_type, str):
            analysis_type = InferenceType(analysis_type)

        try:
            # Get appropriate prompt
            prompt = self.prompts[analysis_type](idea, topic, context)

            # Call LLM using proper API pattern with structured output
            from madspark.agents.genai_client import get_model_name

            # Get pre-computed schema for analysis type
            schema_map = {
                InferenceType.FULL: _FULL_ANALYSIS_GENAI_SCHEMA,
                InferenceType.CAUSAL: _CAUSAL_ANALYSIS_GENAI_SCHEMA,
                InferenceType.CONSTRAINTS: _CONSTRAINT_ANALYSIS_GENAI_SCHEMA,
                InferenceType.CONTRADICTION: _CONTRADICTION_ANALYSIS_GENAI_SCHEMA,
                InferenceType.IMPLICATIONS: _IMPLICATIONS_ANALYSIS_GENAI_SCHEMA
            }
            response_schema = schema_map[analysis_type]

            api_config = genai.types.GenerateContentConfig(
                temperature=0.7,  # Moderate temperature for balanced reasoning
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction="You are a logical reasoning expert. Analyze ideas systematically and provide structured logical insights in JSON format."
            )
            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=prompt,
                config=api_config
            )

            # Parse JSON response
            data = json.loads(response.text)
            return self._create_result_from_json(data, analysis_type)

        except json.JSONDecodeError as e:
            # Fallback to text parsing for backward compatibility
            logger.warning(f"JSON parsing failed, falling back to text parsing: {e}")
            result = self._parse_response(response.text, analysis_type)
            # Note that we fell back to text parsing due to invalid JSON
            if result.error is None and result.confidence > 0:
                # Successfully parsed as text, but note the JSON failure
                pass  # Don't set error if text parsing succeeded
            return result

        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Logical inference failed: {e}")
            return InferenceResult(
                conclusion="Unable to perform logical analysis due to an error",
                confidence=0.0,
                error=str(e)
            )
    
    def analyze_batch(
        self,
        ideas: List[str],
        topic: str,
        context: str,
        analysis_type: Union[InferenceType, str] = InferenceType.FULL
    ) -> List[InferenceResult]:
        """
        Perform logical inference analysis on multiple ideas in a single API call.

        This method significantly reduces API calls from O(N) to O(1) for logical inference,
        providing substantial performance improvements for batch processing.

        Args:
            ideas: List of generated ideas to analyze
            topic: Original topic
            context: Constraints and requirements
            analysis_type: Type of analysis to perform

        Returns:
            List of InferenceResult objects, one for each idea
        """
        if not ideas:
            return []

        # Convert string to enum if needed
        if isinstance(analysis_type, str):
            analysis_type = InferenceType(analysis_type)

        try:
            # Create batch prompt for all ideas
            batch_prompt = self._get_batch_analysis_prompt(ideas, topic, context, analysis_type)

            # Call LLM using proper API pattern with structured output
            from madspark.agents.genai_client import get_model_name

            # Build batch schema from pre-computed single-item schemas
            schema_map = {
                InferenceType.FULL: {"type": "ARRAY", "items": _FULL_ANALYSIS_GENAI_SCHEMA},
                InferenceType.CAUSAL: {"type": "ARRAY", "items": _CAUSAL_ANALYSIS_GENAI_SCHEMA},
                InferenceType.CONSTRAINTS: {"type": "ARRAY", "items": _CONSTRAINT_ANALYSIS_GENAI_SCHEMA},
                InferenceType.CONTRADICTION: {"type": "ARRAY", "items": _CONTRADICTION_ANALYSIS_GENAI_SCHEMA},
                InferenceType.IMPLICATIONS: {"type": "ARRAY", "items": _IMPLICATIONS_ANALYSIS_GENAI_SCHEMA},
            }

            response_schema = schema_map[analysis_type]

            api_config = genai.types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction="You are a logical reasoning expert. Analyze multiple ideas systematically and provide structured logical insights for each one in JSON array format."
            )

            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=batch_prompt,
                config=api_config
            )

            # Parse batch JSON response
            data = json.loads(response.text)
            if not isinstance(data, list):
                raise ValueError(f"Expected array response, got {type(data).__name__}")

            # Convert each JSON object to InferenceResult
            results = []
            for item_data in data:
                result = self._create_result_from_json(item_data, analysis_type)
                results.append(result)

            # Fill remaining slots if parsing didn't get all ideas
            while len(results) < len(ideas):
                results.append(PydanticInferenceResult(
                    inference_chain=["Batch parsing incomplete"],
                    conclusion="Unable to parse logical analysis from batch response",
                    confidence=0.0
                ))

            return results[:len(ideas)]  # Ensure we return exact number requested

        except json.JSONDecodeError as e:
            # Fallback to text parsing for backward compatibility
            logger.warning(f"JSON batch parsing failed, falling back to text parsing: {e}")
            return self._parse_batch_response(response.text, len(ideas), analysis_type)

        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Batch logical inference failed: {e}")
            # Return error results for all ideas
            return [
                PydanticInferenceResult(
                    inference_chain=["Analysis failed due to error"],
                    conclusion="Unable to perform logical analysis due to an error",
                    confidence=0.0
                )
                for _ in ideas
            ]
    
    def _get_batch_analysis_prompt(
        self, 
        ideas: List[str], 
        topic: str, 
        context: str, 
        analysis_type: InferenceType
    ) -> str:
        """Generate batch prompt for logical analysis of multiple ideas."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        ideas_section = ""
        for i, idea in enumerate(ideas, 1):
            ideas_section += f"\nIDEA_{i}:\n{idea}\n"
        
        if analysis_type == InferenceType.FULL:
            return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Perform comprehensive logical analysis on these {len(ideas)} ideas.

Theme: {topic}
Context/Constraints: {context}
{ideas_section}

For each idea, provide a structured logical analysis following this exact format:

=== ANALYSIS_FOR_IDEA_1 ===
INFERENCE_CHAIN:
- [Step 1]: [First logical step explaining why this addresses the topic]
- [Step 2]: [Next logical deduction or observation]
- [Step 3]: [Further reasoning building on previous steps]
- [Step N]: [Final logical step leading to conclusion]

CONCLUSION: [One paragraph summary of the logical conclusion based on the inference chain]

CONFIDENCE: [0.0-1.0 score indicating logical soundness]

IMPROVEMENTS: [Specific suggestions to make the idea more logically sound or address gaps]

=== ANALYSIS_FOR_IDEA_2 ===
[Same format for idea 2]
...
[Continue for all {len(ideas)} ideas]

Important:
- Each inference step should logically follow from the previous
- Consider causal relationships, constraints, and potential contradictions
- Base confidence on logical consistency and how well constraints are satisfied
- Suggest concrete improvements based on logical gaps identified
- Use the exact format with === ANALYSIS_FOR_IDEA_N === separators"""
        
        # Add other analysis types as needed
        return self._get_full_analysis_prompt(ideas[0], topic, context)  # Fallback to single analysis
    
    def _parse_batch_response(
        self, 
        response_text: str, 
        num_ideas: int, 
        analysis_type: InferenceType
    ) -> List[InferenceResult]:
        """Parse batch analysis response into individual InferenceResult objects."""
        results = []
        
        try:
            # Split response by analysis sections
            sections = response_text.split("=== ANALYSIS_FOR_IDEA_")
            
            # Skip first section (usually empty or header)
            if len(sections) > 1:
                sections = sections[1:]
            
            for i, section in enumerate(sections[:num_ideas]):
                # Extract the analysis content after the ID
                if " ===" in section:
                    analysis_content = section.split(" ===", 1)[1].strip()
                else:
                    analysis_content = section.strip()
                
                # Parse individual analysis
                result = self._parse_response(analysis_content, analysis_type)
                results.append(result)
            
            # Fill remaining slots if parsing didn't get all ideas
            while len(results) < num_ideas:
                results.append(InferenceResult(
                    conclusion="Unable to parse logical analysis from batch response",
                    confidence=0.0,
                    error="Batch parsing incomplete"
                ))
            
        except Exception as e:
            logger.error(f"Failed to parse batch response: {e}")
            # Return error results for all ideas
            results = [
                InferenceResult(
                    conclusion="Unable to parse logical analysis from batch response",
                    confidence=0.0,
                    error=str(e)
                )
                for _ in range(num_ideas)
            ]
        
        return results
    
    def _get_full_analysis_prompt(self, idea: str, topic: str, context: str) -> str:
        """Generate prompt for full logical analysis."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Perform comprehensive logical analysis on this idea.

Theme: {topic}
Context/Constraints: {context}
Idea: {idea}

Provide a structured logical analysis following this exact format:

INFERENCE_CHAIN:
- [Step 1]: [First logical step explaining why this addresses the topic]
- [Step 2]: [Next logical deduction or observation]
- [Step 3]: [Further reasoning building on previous steps]
- [Step N]: [Final logical step leading to conclusion]

CONCLUSION: [One paragraph summary of the logical conclusion based on the inference chain]

CONFIDENCE: [0.0-1.0 score indicating logical soundness]

IMPROVEMENTS: [Specific suggestions to make the idea more logically sound or address gaps]

Important:
- Each inference step should logically follow from the previous
- Consider causal relationships, constraints, and potential contradictions
- Base confidence on logical consistency and how well constraints are satisfied
- Suggest concrete improvements based on logical gaps identified"""
    
    def _get_causal_analysis_prompt(self, idea: str, topic: str, context: str) -> str:
        """Generate prompt for causal reasoning analysis."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Analyze the causal relationships in this idea.

Theme: {topic}
Context: {context}
Idea: {idea}

Provide causal analysis in this exact format:

CAUSAL_CHAIN:
1. [Root cause or initial condition] → [Direct effect]
2. [Previous effect] → [Next effect]
3. [Continue the causal chain...]

FEEDBACK_LOOPS:
- [Describe any reinforcing or balancing feedback loops]

ROOT_CAUSE: [Identify the fundamental cause that makes this idea necessary]

Trace the complete causal chain from root causes to final outcomes."""
    
    def _get_constraint_analysis_prompt(self, idea: str, topic: str, context: str) -> str:
        """Generate prompt for constraint satisfaction analysis."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Analyze how well this idea satisfies the given constraints.

Theme: {topic}
Constraints: {context}
Idea: {idea}

Provide constraint analysis in this exact format:

CONSTRAINT_ANALYSIS:
- [Constraint 1]: [SATISFIED/PARTIALLY SATISFIED/NOT SATISFIED] ([0-100]%) - [Explanation]
- [Constraint 2]: [Status] ([Percentage]%) - [How it's addressed]
- [Continue for each constraint...]

OVERALL_SATISFACTION: [0-100]%

TRADE_OFFS:
- [Trade-off 1 made to satisfy constraints]
- [Trade-off 2]

Evaluate each constraint separately and explain the degree of satisfaction."""
    
    def _get_contradiction_analysis_prompt(self, idea: str, topic: str, context: str) -> str:
        """Generate prompt for contradiction detection."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Identify any logical contradictions in this idea.

Theme: {topic}
Context: {context}
Idea: {idea}

Provide contradiction analysis in this exact format:

CONTRADICTIONS_FOUND: [number]

[If contradictions exist:]
CONTRADICTION_1:
- Conflict: [Element A] vs [Element B]
- Type: [Internal/External/Practical]
- Severity: [HIGH/MEDIUM/LOW]
- Explanation: [Why these elements conflict]

RESOLUTION:
[Suggest how to resolve the contradictions]

[If no contradictions:]
NO_CONTRADICTIONS: True
Explanation: [Why the idea is logically consistent]"""
    
    def _get_implications_analysis_prompt(self, idea: str, topic: str, context: str) -> str:
        """Generate prompt for implications analysis."""
        # Import language consistency instruction
        try:
            from madspark.utils.constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        except ImportError:
            from .constants import LANGUAGE_CONSISTENCY_INSTRUCTION
        
        return f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Analyze the logical implications and consequences of this idea.

Theme: {topic}
Context: {context}
Idea: {idea}

Provide implications analysis in this format:

DIRECT_IMPLICATIONS:
1. [Immediate consequence of implementing this idea]
2. [Another direct implication]

SECOND_ORDER_EFFECTS:
- [Consequence of the implications]
- [Broader systemic effects]

LONG_TERM_CONSEQUENCES:
- [What happens if this succeeds at scale]
- [Potential future states]

Consider both positive and negative implications."""

    def _create_result_from_json(self, data: Dict[str, Any], analysis_type: InferenceType) -> InferenceResult:
        """Create InferenceResult from JSON data using Pydantic validation.

        This method uses Pydantic models to parse and validate JSON responses,
        providing automatic type checking and field validation.

        Args:
            data: Parsed JSON dictionary from LLM response
            analysis_type: Type of analysis performed

        Returns:
            Pydantic InferenceResult model with validated data

        Raises:
            ValidationError: If JSON data doesn't match expected Pydantic schema
        """
        # Select appropriate Pydantic model based on analysis type
        model_map = {
            InferenceType.FULL: PydanticInferenceResult,
            InferenceType.CAUSAL: CausalAnalysis,
            InferenceType.CONSTRAINTS: ConstraintAnalysis,
            InferenceType.CONTRADICTION: ContradictionAnalysis,
            InferenceType.IMPLICATIONS: ImplicationsAnalysis
        }

        model_class = model_map.get(analysis_type, PydanticInferenceResult)

        # Parse and validate using Pydantic model
        return model_class(**data)

    def _parse_response(self, response_text: str, analysis_type: InferenceType) -> InferenceResult:
        """Parse LLM response into structured Pydantic InferenceResult."""
        try:
            if analysis_type == InferenceType.FULL:
                result = self._parse_full_response(response_text)
            elif analysis_type == InferenceType.CAUSAL:
                result = self._parse_causal_response(response_text)
            elif analysis_type == InferenceType.CONSTRAINTS:
                result = self._parse_constraint_response(response_text)
            elif analysis_type == InferenceType.CONTRADICTION:
                result = self._parse_contradiction_response(response_text)
            elif analysis_type == InferenceType.IMPLICATIONS:
                result = self._parse_implications_response(response_text)
            else:
                # Fallback for unknown types
                result = PydanticInferenceResult(
                    inference_chain=["Analysis completed"],
                    conclusion="Analysis completed",
                    confidence=0.5
                )

        except (AttributeError, IndexError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse response fully: {e}")
            # Provide basic Pydantic result even if parsing fails
            conclusion = self._extract_section(response_text, "CONCLUSION") or \
                        "Analysis completed but parsing was incomplete"
            confidence = self._extract_confidence(response_text) or 0.5
            result = PydanticInferenceResult(
                inference_chain=["Fallback analysis"],
                conclusion=conclusion,
                confidence=confidence
            )

        return result
    
    def _parse_full_response(self, text: str) -> InferenceResult:
        """Parse full analysis response into Pydantic model."""
        # Extract fields
        chain_section = self._extract_section(text, "INFERENCE_CHAIN")
        inference_chain = self._parse_bullet_list(chain_section) if chain_section else ["Analysis completed"]

        conclusion = self._extract_section(text, "CONCLUSION") or "Analysis completed but parsing was incomplete"
        confidence = self._extract_confidence(text) or 0.5
        improvements = self._extract_section(text, "IMPROVEMENTS")

        # Return Pydantic model
        return PydanticInferenceResult(
            inference_chain=inference_chain,
            conclusion=conclusion,
            confidence=confidence,
            improvements=improvements
        )
    
    def _parse_causal_response(self, text: str) -> InferenceResult:
        """Parse causal analysis response into Pydantic CausalAnalysis model."""
        # Extract fields (this is a fallback parser, rarely used with structured output)

        # Extract causal chain
        chain_section = self._extract_section(text, "CAUSAL_CHAIN")
        causal_chain = self._parse_numbered_list(chain_section) if chain_section else ["Causal analysis"]

        # Extract feedback loops
        loops_section = self._extract_section(text, "FEEDBACK_LOOPS")
        feedback_loops = self._parse_bullet_list(loops_section) if loops_section else []

        # Extract root cause
        root_cause = self._extract_section(text, "ROOT_CAUSE") or "Analysis completed"

        # Set conclusion based on root cause
        conclusion = f"Root cause analysis: {root_cause}"
        confidence = 0.8  # Default for causal analysis

        # Extract inference chain for base model
        inference_chain = causal_chain[:3] if len(causal_chain) > 0 else ["Causal analysis step 1"]

        # Return Pydantic CausalAnalysis model
        return CausalAnalysis(
            inference_chain=inference_chain,
            conclusion=conclusion,
            confidence=confidence,
            causal_chain=causal_chain,
            feedback_loops=feedback_loops,
            root_cause=root_cause
        )
    
    def _parse_constraint_response(self, text: str) -> InferenceResult:
        """Parse constraint satisfaction response into Pydantic ConstraintAnalysis model."""
        # Extract constraint analysis
        constraints_section = self._extract_section(text, "CONSTRAINT_ANALYSIS")
        raw_constraint_satisfaction = (
            self._parse_constraint_list(constraints_section)
            if constraints_section
            else {"general": 50.0}  # Default to 50% = 0.5 normalized
        )

        # Normalize constraint scores to 0.0-1.0 as expected by Pydantic schema
        constraint_satisfaction = {
            name: (value / 100.0 if value > 1 else value)
            for name, value in raw_constraint_satisfaction.items()
        }

        # Extract overall satisfaction and normalize to 0.0-1.0
        overall = self._extract_number(text, "OVERALL_SATISFACTION")
        raw_overall = overall if overall is not None else 50.0  # Default to 50%
        overall_satisfaction = raw_overall / 100.0 if raw_overall > 1 else raw_overall
        confidence = overall_satisfaction  # Already normalized

        # Extract trade-offs
        tradeoffs_section = self._extract_section(text, "TRADE_OFFS")
        trade_offs = self._parse_bullet_list(tradeoffs_section) if tradeoffs_section else []

        # Set conclusion (overall_satisfaction is already 0.0-1.0)
        conclusion = f"Constraints satisfied at {int(overall_satisfaction * 100)}% overall"

        # Extract inference chain
        inference_chain = ["Constraint analysis step 1", f"Evaluated {len(constraint_satisfaction)} constraints"]

        # Return Pydantic ConstraintAnalysis model
        return ConstraintAnalysis(
            inference_chain=inference_chain,
            conclusion=conclusion,
            confidence=confidence,
            constraint_satisfaction=constraint_satisfaction,
            overall_satisfaction=overall_satisfaction,
            trade_offs=trade_offs
        )
    
    def _parse_contradiction_response(self, text: str) -> InferenceResult:
        """Parse contradiction analysis response into Pydantic ContradictionAnalysis model."""
        contradictions = []

        # Check for contradictions count
        count_match = re.search(r'CONTRADICTIONS_FOUND:\s*(\d+)', text)
        if count_match and int(count_match.group(1)) > 0:
            # Parse each contradiction
            contradiction_sections = re.findall(
                r'CONTRADICTION_\d+:(.*?)(?=CONTRADICTION_\d+:|RESOLUTION:|$)',
                text, re.DOTALL
            )

            for section in contradiction_sections:
                contradiction = self._parse_contradiction_details(section)
                if contradiction:
                    contradictions.append(contradiction)

        # Extract resolution
        resolution = self._extract_section(text, "RESOLUTION") or "No resolution provided"

        # Set conclusion based on findings
        if contradictions:
            conclusion = f"Found {len(contradictions)} logical contradiction(s)"
            confidence = 0.6  # Lower confidence when contradictions exist
        else:
            conclusion = "No logical contradictions detected"
            confidence = 0.9

        # Extract inference chain
        inference_chain = [
            "Analyzed for logical contradictions",
            f"Found {len(contradictions)} potential issues"
        ]

        # Return Pydantic ContradictionAnalysis model
        return ContradictionAnalysis(
            inference_chain=inference_chain,
            conclusion=conclusion,
            confidence=confidence,
            contradictions=contradictions,
            resolution=resolution
        )
    
    def _parse_implications_response(self, text: str) -> InferenceResult:
        """Parse implications analysis response into Pydantic ImplicationsAnalysis model."""
        # Extract direct implications
        direct_section = self._extract_section(text, "DIRECT_IMPLICATIONS")
        implications = self._parse_numbered_list(direct_section) if direct_section else ["Analysis completed"]

        # Extract second-order effects
        second_section = self._extract_section(text, "SECOND_ORDER_EFFECTS")
        second_order_effects = self._parse_bullet_list(second_section) if second_section else []

        # Set conclusion
        conclusion = f"Analysis reveals {len(implications)} direct implications"
        confidence = 0.8

        # Extract inference chain
        inference_chain = [
            "Analyzed direct implications",
            f"Identified {len(second_order_effects)} second-order effects"
        ]

        # Return Pydantic ImplicationsAnalysis model
        return ImplicationsAnalysis(
            inference_chain=inference_chain,
            conclusion=conclusion,
            confidence=confidence,
            implications=implications,
            second_order_effects=second_order_effects
        )
    
    # Utility parsing methods
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract content of a named section."""
        # Limit character matching to prevent ReDoS attacks
        pattern = rf'{section_name}:\s*([^\n]{{0,5000}}.*?)(?=\n[A-Z_]+:|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence score from text."""
        match = re.search(r'CONFIDENCE:\s*([\d.]+)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_number(self, text: str, field_name: str) -> Optional[float]:
        """Extract a number associated with a field."""
        match = re.search(rf'{field_name}:\s*([\d.]+)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
    
    def _parse_bullet_list(self, text: str) -> List[str]:
        """Parse a bullet point list."""
        lines = text.strip().split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                items.append(line[1:].strip())
            elif line and not line[0].isspace():
                items.append(line)
        return items
    
    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse a numbered list."""
        items = []
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            # Match patterns like "1." or "1)" at start
            match = re.match(r'^\d+[.)]\s*(.+)', line)
            if match:
                items.append(match.group(1))
            elif line and not line[0].isspace():
                items.append(line)
        return items
    
    def _parse_constraint_list(self, text: str) -> Dict[str, float]:
        """Parse constraint satisfaction list."""
        constraints = {}
        lines = text.strip().split('\n')
        for line in lines:
            match = re.search(r'([^:]+):\s*\w+\s*\((\d+)%\)', line)
            if match:
                constraint_name = match.group(1).strip('- ')
                satisfaction = float(match.group(2))
                # Ensure percentage is within valid range
                satisfaction = max(0.0, min(100.0, satisfaction))
                constraints[constraint_name] = satisfaction
        return constraints
    
    def _parse_contradiction_details(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse details of a single contradiction."""
        details = {}
        
        # Extract conflict
        conflict_match = re.search(r'Conflict:\s*(.+?)(?=\n|$)', text)
        if conflict_match:
            details['conflict'] = conflict_match.group(1).strip()
        
        # Extract severity
        severity_match = re.search(r'Severity:\s*(HIGH|MEDIUM|LOW)', text)
        if severity_match:
            details['severity'] = severity_match.group(1)
        
        # Extract type
        type_match = re.search(r'Type:\s*(.+?)(?=\n|$)', text)
        if type_match:
            details['type'] = type_match.group(1).strip()
        
        # Extract explanation
        exp_match = re.search(r'Explanation:\s*(.+?)(?=\n|$)', text)
        if exp_match:
            details['explanation'] = exp_match.group(1).strip()
        
        return details if details else None
    
    def format_for_display(
        self,
        result: InferenceResult,
        verbosity: str = 'standard'
    ) -> str:
        """
        Format inference result for display.
        
        Args:
            result: InferenceResult to format
            verbosity: 'brief', 'standard', or 'detailed'
            
        Returns:
            Formatted string for display
        """
        if verbosity == 'brief':
            return self._format_brief(result)
        elif verbosity == 'detailed':
            return self._format_detailed(result)
        else:
            return self._format_standard(result)
    
    def _format_brief(self, result: InferenceResult) -> str:
        """Format brief display showing only conclusion and confidence."""
        output = []
        if result.conclusion:
            output.append(f"Conclusion: {result.conclusion}")
        output.append(f"Confidence: {result.confidence:.0%}")
        return '\n'.join(output)
    
    def _format_standard(self, result: InferenceResult) -> str:
        """Format standard display with inference chain and conclusion."""
        output = ["🧠 Logical Inference Analysis:"]
        
        if result.inference_chain:
            output.append("\nInference Chain:")
            for step in result.inference_chain:
                output.append(f"  → {step}")
        
        if result.conclusion:
            output.append(f"\nConclusion: {result.conclusion}")
        
        output.append(f"\nConfidence: {result.confidence:.0%}")
        
        if result.improvements:
            output.append(f"\nSuggested Improvements: {result.improvements}")
        
        return '\n'.join(output)
    
    def _format_detailed(self, result: InferenceResult) -> str:
        """Format detailed display with all available information."""
        output = ["🧠 Logical Inference Analysis (Detailed):"]
        
        # Standard inference chain
        if result.inference_chain:
            output.append("\nInference Chain:")
            for i, step in enumerate(result.inference_chain, 1):
                output.append(f"  {i}. {step}")
        
        # Causal analysis
        if result.causal_chain:
            output.append("\nCausal Analysis:")
            for cause in result.causal_chain:
                output.append(f"  • {cause}")
        
        if result.feedback_loops:
            output.append("\nFeedback Loops:")
            for loop in result.feedback_loops:
                output.append(f"  ↻ {loop}")
        
        # Constraints
        if result.constraint_satisfaction:
            output.append("\nConstraint Satisfaction:")
            for constraint, satisfaction in result.constraint_satisfaction.items():
                output.append(f"  • {constraint}: {satisfaction}%")
        
        # Contradictions
        if result.contradictions:
            output.append("\nContradictions Found:")
            for cont in result.contradictions:
                output.append(f"  ⚠️  {cont.get('conflict', 'Unknown conflict')}")
                if 'severity' in cont:
                    output.append(f"     Severity: {cont['severity']}")
        
        # Implications
        if result.implications:
            output.append("\nDirect Implications:")
            for imp in result.implications:
                output.append(f"  → {imp}")
        
        if result.second_order_effects:
            output.append("\nSecond-Order Effects:")
            for effect in result.second_order_effects:
                output.append(f"  ⟶ {effect}")
        
        # Conclusion and confidence
        if result.conclusion:
            output.append(f"\nConclusion: {result.conclusion}")
        
        output.append(f"\nConfidence Score: {result.confidence:.0%}")
        
        # Improvements
        if result.improvements:
            output.append(f"\nImprovements: {result.improvements}")
        
        # Error if any
        if result.error:
            output.append(f"\n⚠️  Error during analysis: {result.error}")
        
        return '\n'.join(output)