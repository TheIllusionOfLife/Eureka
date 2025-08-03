"""
Logical Inference Engine for MadSpark.

This module provides LLM-based logical inference capabilities to replace
the hardcoded templates with genuine logical analysis.
"""
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)


class InferenceType(Enum):
    """Types of logical inference analysis."""
    FULL = "full"
    CAUSAL = "causal"
    CONSTRAINTS = "constraints"
    CONTRADICTION = "contradiction"
    IMPLICATIONS = "implications"


@dataclass
class InferenceResult:
    """Result of logical inference analysis."""
    # Core fields
    inference_chain: List[str] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    improvements: Optional[str] = None
    
    # Analysis-specific fields
    causal_chain: Optional[List[str]] = None
    feedback_loops: Optional[List[str]] = None
    root_cause: Optional[str] = None
    
    constraint_satisfaction: Optional[Dict[str, float]] = None
    overall_satisfaction: Optional[float] = None
    trade_offs: Optional[List[str]] = None
    
    contradictions: Optional[List[Dict[str, Any]]] = None
    resolution: Optional[str] = None
    
    implications: Optional[List[str]] = None
    second_order_effects: Optional[List[str]] = None
    
    # Error handling
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, list) and len(value) == 0:
                    continue  # Skip empty lists
                result[key] = value
        return result


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
        theme: str,
        context: str,
        analysis_type: Union[InferenceType, str] = InferenceType.FULL
    ) -> InferenceResult:
        """
        Perform logical inference analysis on an idea.
        
        Args:
            idea: The generated idea to analyze
            theme: Original theme/topic
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
            prompt = self.prompts[analysis_type](idea, theme, context)
            
            # Call LLM using proper API pattern
            from madspark.agents.genai_client import get_model_name
            from google import genai
            
            config = genai.types.GenerateContentConfig(
                temperature=0.7,  # Moderate temperature for balanced reasoning
                system_instruction="You are a logical reasoning expert. Analyze ideas systematically and provide structured logical insights."
            )
            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=prompt,
                config=config
            )
            
            # Parse response
            return self._parse_response(response.text, analysis_type)
            
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
        theme: str,
        context: str,
        analysis_type: Union[InferenceType, str] = InferenceType.FULL
    ) -> List[InferenceResult]:
        """
        Perform logical inference analysis on multiple ideas in a single API call.
        
        This method significantly reduces API calls from O(N) to O(1) for logical inference,
        providing substantial performance improvements for batch processing.
        
        Args:
            ideas: List of generated ideas to analyze
            theme: Original theme/topic
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
            batch_prompt = self._get_batch_analysis_prompt(ideas, theme, context, analysis_type)
            
            # Call LLM using proper API pattern
            from madspark.agents.genai_client import get_model_name
            from google import genai
            
            config = genai.types.GenerateContentConfig(
                temperature=0.7,
                system_instruction="You are a logical reasoning expert. Analyze multiple ideas systematically and provide structured logical insights for each one."
            )
            
            response = self.genai_client.models.generate_content(
                model=get_model_name(),
                contents=batch_prompt,
                config=config
            )
            
            # Parse batch response
            return self._parse_batch_response(response.text, len(ideas), analysis_type)
            
        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Batch logical inference failed: {e}")
            # Return error results for all ideas
            return [
                InferenceResult(
                    conclusion="Unable to perform logical analysis due to an error",
                    confidence=0.0,
                    error=str(e)
                )
                for _ in ideas
            ]
    
    def _get_batch_analysis_prompt(
        self, 
        ideas: List[str], 
        theme: str, 
        context: str, 
        analysis_type: InferenceType
    ) -> str:
        """Generate batch prompt for logical analysis of multiple ideas."""
        ideas_section = ""
        for i, idea in enumerate(ideas, 1):
            ideas_section += f"\nIDEA_{i}:\n{idea}\n"
        
        if analysis_type == InferenceType.FULL:
            return f"""Perform comprehensive logical analysis on these {len(ideas)} ideas.

Theme: {theme}
Context/Constraints: {context}
{ideas_section}

For each idea, provide a structured logical analysis following this exact format:

=== ANALYSIS_FOR_IDEA_1 ===
INFERENCE_CHAIN:
- [Step 1]: [First logical step explaining why this addresses the theme]
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
        
        # Other analysis types not yet supported for batch processing
        else:
            raise NotImplementedError(
                f"Batch analysis for {analysis_type.value} type is not yet implemented. "
                f"Only {InferenceType.FULL.value} analysis supports batch processing."
            )
    
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
    
    def _get_full_analysis_prompt(self, idea: str, theme: str, context: str) -> str:
        """Generate prompt for full logical analysis."""
        return f"""Perform comprehensive logical analysis on this idea.

Theme: {theme}
Context/Constraints: {context}
Idea: {idea}

Provide a structured logical analysis following this exact format:

INFERENCE_CHAIN:
- [Step 1]: [First logical step explaining why this addresses the theme]
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
    
    def _get_causal_analysis_prompt(self, idea: str, theme: str, context: str) -> str:
        """Generate prompt for causal reasoning analysis."""
        return f"""Analyze the causal relationships in this idea.

Theme: {theme}
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
    
    def _get_constraint_analysis_prompt(self, idea: str, theme: str, context: str) -> str:
        """Generate prompt for constraint satisfaction analysis."""
        return f"""Analyze how well this idea satisfies the given constraints.

Theme: {theme}
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
    
    def _get_contradiction_analysis_prompt(self, idea: str, theme: str, context: str) -> str:
        """Generate prompt for contradiction detection."""
        return f"""Identify any logical contradictions in this idea.

Theme: {theme}
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
    
    def _get_implications_analysis_prompt(self, idea: str, theme: str, context: str) -> str:
        """Generate prompt for implications analysis."""
        return f"""Analyze the logical implications and consequences of this idea.

Theme: {theme}
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
    
    def _parse_response(self, response_text: str, analysis_type: InferenceType) -> InferenceResult:
        """Parse LLM response into structured InferenceResult."""
        result = InferenceResult()
        
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
            
        except (AttributeError, IndexError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse response fully: {e}")
            # Provide basic result even if parsing fails
            result.conclusion = self._extract_section(response_text, "CONCLUSION") or \
                               "Analysis completed but parsing was incomplete"
            result.confidence = self._extract_confidence(response_text) or 0.5
            
        return result
    
    def _parse_full_response(self, text: str) -> InferenceResult:
        """Parse full analysis response."""
        result = InferenceResult()
        
        # Extract inference chain
        chain_section = self._extract_section(text, "INFERENCE_CHAIN")
        if chain_section:
            result.inference_chain = self._parse_bullet_list(chain_section)
        
        # Extract conclusion
        result.conclusion = self._extract_section(text, "CONCLUSION") or ""
        
        # Extract confidence
        result.confidence = self._extract_confidence(text) or 0.5
        
        # Extract improvements
        result.improvements = self._extract_section(text, "IMPROVEMENTS")
        
        return result
    
    def _parse_causal_response(self, text: str) -> InferenceResult:
        """Parse causal analysis response."""
        result = InferenceResult()
        
        # Extract causal chain
        chain_section = self._extract_section(text, "CAUSAL_CHAIN")
        if chain_section:
            result.causal_chain = self._parse_numbered_list(chain_section)
        
        # Extract feedback loops
        loops_section = self._extract_section(text, "FEEDBACK_LOOPS")
        if loops_section:
            result.feedback_loops = self._parse_bullet_list(loops_section)
        
        # Extract root cause
        result.root_cause = self._extract_section(text, "ROOT_CAUSE")
        
        # Set conclusion based on root cause
        if result.root_cause:
            result.conclusion = f"Root cause analysis: {result.root_cause}"
            result.confidence = 0.8  # Default for causal analysis
        
        return result
    
    def _parse_constraint_response(self, text: str) -> InferenceResult:
        """Parse constraint satisfaction response."""
        result = InferenceResult()
        
        # Extract constraint analysis
        constraints_section = self._extract_section(text, "CONSTRAINT_ANALYSIS")
        if constraints_section:
            result.constraint_satisfaction = self._parse_constraint_list(constraints_section)
        
        # Extract overall satisfaction
        overall = self._extract_number(text, "OVERALL_SATISFACTION")
        if overall is not None:
            result.overall_satisfaction = overall
            result.confidence = overall / 100.0  # Convert percentage to confidence
        
        # Extract trade-offs
        tradeoffs_section = self._extract_section(text, "TRADE_OFFS")
        if tradeoffs_section:
            result.trade_offs = self._parse_bullet_list(tradeoffs_section)
        
        # Set conclusion
        if result.overall_satisfaction:
            result.conclusion = f"Constraints satisfied at {result.overall_satisfaction}% overall"
        
        return result
    
    def _parse_contradiction_response(self, text: str) -> InferenceResult:
        """Parse contradiction analysis response."""
        result = InferenceResult()
        result.contradictions = []
        
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
                    result.contradictions.append(contradiction)
        
        # Extract resolution
        result.resolution = self._extract_section(text, "RESOLUTION")
        
        # Set conclusion based on findings
        if result.contradictions:
            result.conclusion = f"Found {len(result.contradictions)} logical contradiction(s)"
            result.confidence = 0.6  # Lower confidence when contradictions exist
        else:
            result.conclusion = "No logical contradictions detected"
            result.confidence = 0.9
        
        return result
    
    def _parse_implications_response(self, text: str) -> InferenceResult:
        """Parse implications analysis response."""
        result = InferenceResult()
        
        # Extract direct implications
        direct_section = self._extract_section(text, "DIRECT_IMPLICATIONS")
        if direct_section:
            result.implications = self._parse_numbered_list(direct_section)
        
        # Extract second-order effects
        second_section = self._extract_section(text, "SECOND_ORDER_EFFECTS")
        if second_section:
            result.second_order_effects = self._parse_bullet_list(second_section)
        
        # Set conclusion
        if result.implications:
            result.conclusion = f"Analysis reveals {len(result.implications)} direct implications"
            result.confidence = 0.8
        
        return result
    
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