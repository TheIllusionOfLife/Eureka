"""Main enhanced reasoning engine that coordinates all reasoning components."""

import logging
from typing import Dict, List, Any, Optional, Union

from madspark.config.execution_constants import ThresholdConfig
from madspark.utils.logical_inference_engine import InferenceType

from .context_memory import ContextMemory
from .inference import LogicalInference
from .evaluator import MultiDimensionalEvaluator
from .tracker import AgentConversationTracker

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Main enhanced reasoning engine that coordinates all reasoning components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, genai_client=None):
        """Initialize reasoning engine with optional configuration.
        
        Args:
            config: Optional configuration dictionary
            genai_client: Optional GenAI client for multi-dimensional evaluation
        """
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.context_memory = ContextMemory(
            capacity=self.config.get('memory_capacity', 1000)
        )
        
        # Initialize logical inference with GenAI client if available
        self.logical_inference = LogicalInference(genai_client=genai_client)
        
        # Initialize multi-dimensional evaluator
        # Note: This requires genai_client to be functional
        if genai_client:
            try:
                self.multi_evaluator = MultiDimensionalEvaluator(
                    genai_client=genai_client,
                    dimensions=self.config.get('evaluation_dimensions')
                )
            except Exception as e:
                logger.warning(f"Failed to initialize MultiDimensionalEvaluator: {e}")
                self.multi_evaluator = None
        else:
            self.multi_evaluator = None
            
        self.conversation_tracker = AgentConversationTracker()
        
        # Expose logical inference engine directly for batch operations
        # This allows coordinators to access the engine without going through the wrapper
        if hasattr(self.logical_inference, 'inference_engine'):
            self.logical_inference_engine = self.logical_inference.inference_engine
        else:
            self.logical_inference_engine = None
            
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for reasoning engine."""
        return {
            'memory_capacity': 1000,
            'inference_depth': 3,
            'context_weight': 0.7,
            'evaluation_dimensions': None  # Use default dimensions
        }
        
    def process_with_context(self, current_input: Dict[str, Any], 
                           conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process current input with context awareness.
        
        Args:
            current_input: Current agent input/request
            conversation_history: Previous conversation history
            
        Returns:
            Enhanced reasoning results
        """
        # Store current interaction
        context_id = self.context_memory.store_context(current_input)
        
        # Find relevant historical context
        query = current_input.get('input', '') or current_input.get('content', '')
        relevant_contexts = self.context_memory.find_similar_contexts(
            query, threshold=ThresholdConfig.LOOSE_CONTEXT_THRESHOLD
        )
        
        # Calculate context awareness score
        context_score = self._calculate_context_awareness(
            current_input, relevant_contexts, conversation_history
        )
        
        # Generate enhanced reasoning
        enhanced_reasoning = self._generate_enhanced_reasoning(
            current_input, relevant_contexts
        )
        
        return {
            'context_id': context_id,
            'relevant_contexts': relevant_contexts,
            'context_awareness_score': context_score,
            'enhanced_reasoning': enhanced_reasoning,
            'reasoning_quality': self._calculate_reasoning_quality(enhanced_reasoning)
        }
        
    def generate_inference_chain(self, premises: List[str], conclusion: str,
                               theme: str = "", context: str = "",
                               analysis_type: Union[InferenceType, str] = InferenceType.FULL) -> Dict[str, Any]:
        """Generate logical inference chain from premises to conclusion.
        
        Args:
            premises: List of premise statements
            conclusion: Target conclusion
            theme: Optional theme for context
            context: Optional context/constraints
            analysis_type: Type of logical analysis to perform
            
        Returns:
            Dictionary containing inference chain and validity metrics
        """
        # Build chain
        chain_result = self.logical_inference.build_inference_chain(
            premises, theme=theme, context=context, analysis_type=analysis_type
        )
        
        # Analyze consistency
        consistency_result = self.logical_inference.analyze_consistency(premises + [conclusion])
        
        # Calculate confidence
        confidence_result = self.logical_inference.calculate_confidence(premises)
        
        return {
            'chain': chain_result,
            'consistency': consistency_result,
            'confidence': confidence_result,
            'validity_score': chain_result.get('validity_score', 0.0),
            'confidence_score': confidence_result.get('confidence', 0.0)
        }
        
    def process_complete_workflow(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a complete multi-agent workflow with enhanced reasoning.
        
        Args:
            conversation_data: Complete conversation context and current request
            
        Returns:
            Comprehensive reasoning analysis
        """
        # Extract components
        theme = conversation_data.get('theme', '')
        constraints = conversation_data.get('constraints', '')
        previous_interactions = conversation_data.get('previous_interactions', [])
        current_request = conversation_data.get('current_request', {})
        
        # Store interaction history
        for interaction in previous_interactions:
            self.conversation_tracker.add_interaction(interaction)
            
        # Analyze conversation flow
        flow_analysis = self.conversation_tracker.analyze_conversation_flow()
        
        # Process current request with context
        context_result = self.process_with_context(current_request, previous_interactions)
        
        # Generate logical inference if applicable
        logical_inference = {}
        if 'idea' in current_request and (current_request.get('enable_logical_inference') or 
                                         conversation_data.get('enable_logical_inference')):
            premises = [f"Theme: {theme}", f"Constraints: {constraints}"]
            premises.extend([inter.get('output', '') for inter in previous_interactions[-2:]])
            
            # Get analysis type if specified
            analysis_type = current_request.get('analysis_type', InferenceType.FULL)
            
            logical_inference = self.generate_inference_chain(
                premises, 
                f"Recommended approach for {current_request['idea']}",
                theme=theme,
                context=constraints,
                analysis_type=analysis_type
            )
            
        # Multi-dimensional evaluation if this is an evaluation request
        multi_dimensional_evaluation = {}
        if current_request.get('agent') in ['critic', 'advocate']:
            idea = current_request.get('idea', '')
            evaluation_context = {
                'theme': theme,
                'constraints': constraints,
                'previous_feedback': [inter.get('output', '') for inter in previous_interactions]
            }
            if self.multi_evaluator:
                multi_dimensional_evaluation = self.multi_evaluator.evaluate_idea(idea, evaluation_context)
            
        # Calculate overall reasoning quality
        reasoning_quality_score = self._calculate_overall_reasoning_quality(
            context_result, logical_inference, flow_analysis
        )
        
        return {
            'enhanced_reasoning': context_result.get('enhanced_reasoning', {}),
            'context_awareness': context_result,
            'logical_inference': logical_inference,
            'multi_dimensional_evaluation': multi_dimensional_evaluation,
            'conversation_flow': flow_analysis,
            'reasoning_quality_score': reasoning_quality_score
        }
        
    def process_agent_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single agent request with reasoning enhancement.
        
        Args:
            request: Agent request with context
            
        Returns:
            Enhanced processing results
        """
        agent = request.get('agent', 'unknown')
        input_data = request.get('input', '')
        context = request.get('context', {})
        
        # Find relevant historical context
        relevant_contexts = self.context_memory.find_similar_contexts(input_data, threshold=ThresholdConfig.LOOSE_CONTEXT_THRESHOLD)
        
        # Generate contextual insights
        contextual_insights = self._generate_contextual_insights(
            agent, input_data, context, relevant_contexts
        )
        
        # Calculate reasoning quality with conversation history bonus
        conversation_history = context.get('conversation_history', [])
        base_quality = len(relevant_contexts) * 0.1 + len(contextual_insights) * 0.1
        history_bonus = min(0.5, len(conversation_history) * 0.12)  # Up to 0.5 bonus for rich history
        
        # Additional bonus for input complexity in rich context
        if len(conversation_history) > 3 and len(input_data.split()) > 5:
            complexity_bonus = 0.2
        else:
            complexity_bonus = 0.0
            
        reasoning_quality = min(1.0, base_quality + history_bonus + complexity_bonus)
        
        return {
            'agent': agent,
            'enhanced_input': input_data,
            'contextual_insights': contextual_insights,
            'relevant_contexts': relevant_contexts,
            'reasoning_quality_score': reasoning_quality
        }
        
    def calculate_consistency_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate consistency score across multiple reasoning results.
        
        Args:
            results: List of reasoning results to analyze
            
        Returns:
            Consistency score between 0 and 1
        """
        if len(results) < 2:
            return 1.0
            
        # Extract reasoning quality scores
        quality_scores = [result.get('reasoning_quality_score', 0.5) for result in results]
        
        # Calculate variance in quality scores
        avg_quality = sum(quality_scores) / len(quality_scores)
        variance = sum((score - avg_quality) ** 2 for score in quality_scores) / len(quality_scores)
        
        # Convert variance to consistency score (lower variance = higher consistency)
        consistency_score = max(0.0, 1.0 - (variance * 4))  # Scale variance to 0-1 range
        
        return consistency_score
        
    def _calculate_context_awareness(self, current_input: Dict[str, Any], 
                                   relevant_contexts: List[Dict[str, Any]],
                                   conversation_history: List[Dict[str, Any]]) -> float:
        """Calculate context awareness score."""
        # Base score from relevant contexts
        context_score = min(1.0, len(relevant_contexts) * 0.2)
        
        # Bonus for conversation history length
        history_bonus = min(0.3, len(conversation_history) * 0.1)
        
        # Penalty for missing context
        if not relevant_contexts and conversation_history:
            context_score *= 0.5
            
        return min(1.0, context_score + history_bonus)
        
    def _generate_enhanced_reasoning(self, current_input: Dict[str, Any], 
                                   relevant_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate enhanced reasoning analysis."""
        reasoning = {
            'input_analysis': self._analyze_input_complexity(current_input),
            'context_integration': self._analyze_context_integration(relevant_contexts),
            'reasoning_depth': self._calculate_reasoning_depth(current_input, relevant_contexts)
        }
        
        return reasoning
        
    def _calculate_reasoning_quality(self, enhanced_reasoning: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various reasoning quality metrics."""
        return {
            'depth_score': enhanced_reasoning.get('reasoning_depth', 0.5),
            'context_integration_score': enhanced_reasoning.get('context_integration', {}).get('score', 0.5),
            'complexity_score': enhanced_reasoning.get('input_analysis', {}).get('complexity', 0.5)
        }
        
    def _calculate_overall_reasoning_quality(self, context_result: Dict[str, Any],
                                           logical_inference: Dict[str, Any],
                                           flow_analysis: Dict[str, Any]) -> float:
        """Calculate overall reasoning quality score."""
        scores = []
        
        # Context awareness contribution
        scores.append(context_result.get('context_awareness_score', 0.5))
        
        # Logical inference contribution
        if logical_inference:
            scores.append(logical_inference.get('confidence_score', 0.5))
            
        # Conversation flow contribution
        scores.append(flow_analysis.get('workflow_completeness', 0.5))
        
        return sum(scores) / len(scores) if scores else 0.5
        
    def _analyze_input_complexity(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complexity of input data."""
        text = f"{input_data.get('idea', '')} {input_data.get('context', '')}"
        
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        
        complexity = min(1.0, (word_count / 50) + (sentence_count / 10))
        
        return {
            'complexity': complexity,
            'word_count': word_count,
            'sentence_count': sentence_count
        }
        
    def _analyze_context_integration(self, relevant_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well contexts are integrated."""
        if not relevant_contexts:
            return {'score': 0.0, 'integration_count': 0}
            
        # Simple scoring based on number and relevance of contexts
        total_relevance = sum(ctx.get('similarity_score', 0) for ctx in relevant_contexts)
        integration_score = min(1.0, total_relevance)
        
        return {
            'score': integration_score,
            'integration_count': len(relevant_contexts),
            'average_relevance': total_relevance / len(relevant_contexts) if relevant_contexts else 0
        }
        
    def _calculate_reasoning_depth(self, current_input: Dict[str, Any], 
                                 relevant_contexts: List[Dict[str, Any]]) -> float:
        """Calculate reasoning depth score."""
        base_depth = 0.3  # Minimum reasoning depth
        
        # Add depth for context integration
        context_depth = min(0.4, len(relevant_contexts) * 0.1)
        
        # Add depth for input complexity
        input_complexity = self._analyze_input_complexity(current_input)['complexity']
        complexity_depth = input_complexity * 0.3
        
        return base_depth + context_depth + complexity_depth
        
    def _generate_contextual_insights(self, agent: str, input_data: str, 
                                    context: Dict[str, Any], 
                                    relevant_contexts: List[Dict[str, Any]]) -> List[str]:
        """Generate contextual insights based on agent type and history."""
        insights = []
        
        # Agent-specific insights
        if agent == 'idea_generator':
            insights.append("Consider building on previous successful concept patterns")
        elif agent == 'critic':
            insights.append("Evaluate against established criteria from previous assessments")
        elif agent == 'advocate':
            insights.append("Highlight unique benefits not covered in previous evaluations")
        elif agent == 'skeptic':
            insights.append("Consider risks that weren't addressed in advocacy")
            
        # Context-based insights
        if relevant_contexts:
            insights.append(f"Found {len(relevant_contexts)} related previous discussions")
            # Add more insights based on relevant context analysis
            for ctx in relevant_contexts[:2]:  # Top 2 relevant contexts
                if ctx.get('agent') == 'critic':
                    insights.append("Previous critical analysis available for reference")
                elif ctx.get('agent') == 'advocate':
                    insights.append("Previous advocacy insights can inform current approach")
            
        # Context conversation history insights
        conversation_history = context.get('conversation_history', [])
        if len(conversation_history) > 3:
            insights.append("Rich conversation context allows for deeper analysis")
            insights.append("Multiple previous interactions provide valuable patterns")
            
        if context.get('budget') == 'limited':
            insights.append("Cost-effectiveness should be a primary consideration")
            
        # Input complexity insights
        if len(input_data.split()) > 10:
            insights.append("Complex input requires multi-faceted analysis")
            
        return insights
