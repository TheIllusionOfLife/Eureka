"""Tests for enhanced reasoning system for Phase 2 agent behaviors.

This module tests the enhanced reasoning capabilities including:
- Context awareness across agent interactions
- Logical inference chains
- Multi-dimensional evaluation metrics
- Agent memory system
"""
import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import the enhanced reasoning components (to be implemented)
from enhanced_reasoning import (
    ReasoningEngine,
    ContextMemory,
    LogicalInference,
    MultiDimensionalEvaluator,
    AgentConversationTracker
)


class TestReasoningEngine:
    """Test cases for the enhanced reasoning engine."""
    
    def test_reasoning_engine_initialization(self):
        """Test that ReasoningEngine initializes with proper configuration."""
        engine = ReasoningEngine()
        
        assert engine is not None
        assert hasattr(engine, 'context_memory')
        assert hasattr(engine, 'logical_inference')
        assert hasattr(engine, 'conversation_tracker')
        
    def test_reasoning_engine_with_custom_config(self):
        """Test ReasoningEngine initialization with custom configuration."""
        config = {
            'memory_capacity': 100,
            'inference_depth': 5,
            'context_weight': 0.8
        }
        engine = ReasoningEngine(config=config)
        
        assert engine.config['memory_capacity'] == 100
        assert engine.config['inference_depth'] == 5
        assert engine.config['context_weight'] == 0.8
        
    def test_process_with_context_awareness(self):
        """Test that reasoning engine processes ideas with context awareness."""
        engine = ReasoningEngine()
        
        # Simulate a conversation history
        conversation_history = [
            {"agent": "idea_generator", "input": "AI healthcare", "output": "Smart diagnostic tools"},
            {"agent": "critic", "input": "Smart diagnostic tools", "output": "Score: 8, feasible but needs validation"}
        ]
        
        current_input = {
            "agent": "advocate",
            "idea": "Smart diagnostic tools",
            "context": "Budget-friendly healthcare solutions"
        }
        
        result = engine.process_with_context(current_input, conversation_history)
        
        assert result is not None
        assert 'enhanced_reasoning' in result
        assert 'context_awareness_score' in result
        assert result['context_awareness_score'] >= 0.0
        assert result['context_awareness_score'] <= 1.0
        
    def test_logical_inference_chain(self):
        """Test logical inference chain generation."""
        engine = ReasoningEngine()
        
        premises = [
            "AI diagnostic tools can reduce medical errors",
            "Reducing medical errors saves lives",
            "Budget-friendly solutions increase accessibility"
        ]
        
        conclusion = "Budget-friendly AI diagnostic tools save lives and increase accessibility"
        
        inference_chain = engine.generate_inference_chain(premises, conclusion)
        
        assert inference_chain is not None
        assert len(inference_chain) > 0
        assert 'logical_steps' in inference_chain
        assert 'confidence_score' in inference_chain
        assert inference_chain['confidence_score'] >= 0.0
        assert inference_chain['confidence_score'] <= 1.0


class TestContextMemory:
    """Test cases for context memory system."""
    
    def test_context_memory_initialization(self):
        """Test ContextMemory initialization."""
        memory = ContextMemory(capacity=50)
        
        assert memory.capacity == 50
        assert len(memory.get_all_contexts()) == 0
        
    def test_store_and_retrieve_context(self):
        """Test storing and retrieving context information."""
        memory = ContextMemory()
        
        context_data = {
            "agent": "idea_generator",
            "timestamp": "2025-07-03T10:00:00",
            "input": "AI healthcare",
            "output": "Smart diagnostic tools",
            "metadata": {"temperature": 0.8, "model": "gemini-1.5-flash"}
        }
        
        context_id = memory.store_context(context_data)
        retrieved = memory.get_context(context_id)
        
        assert retrieved == context_data
        assert context_id is not None
        
    def test_context_search_by_agent(self):
        """Test searching contexts by agent type."""
        memory = ContextMemory()
        
        # Store multiple contexts
        memory.store_context({"agent": "idea_generator", "output": "Idea 1"})
        memory.store_context({"agent": "critic", "output": "Critique 1"})
        memory.store_context({"agent": "idea_generator", "output": "Idea 2"})
        
        idea_contexts = memory.search_by_agent("idea_generator")
        critic_contexts = memory.search_by_agent("critic")
        
        assert len(idea_contexts) == 2
        assert len(critic_contexts) == 1
        
    def test_context_similarity_search(self):
        """Test finding similar contexts based on content."""
        memory = ContextMemory()
        
        # Store contexts with similar themes
        memory.store_context({"content": "AI healthcare diagnostic tools", "theme": "healthcare"})
        memory.store_context({"content": "Machine learning medical diagnosis", "theme": "healthcare"})
        memory.store_context({"content": "Blockchain supply chain", "theme": "logistics"})
        
        similar_contexts = memory.find_similar_contexts("medical AI diagnosis", threshold=0.5)
        
        assert len(similar_contexts) >= 1
        # Should find the healthcare-related contexts
        healthcare_found = any("healthcare" in str(ctx) for ctx in similar_contexts)
        assert healthcare_found


class TestLogicalInference:
    """Test cases for logical inference capabilities."""
    
    def test_inference_initialization(self):
        """Test LogicalInference initialization."""
        inference = LogicalInference()
        
        assert inference is not None
        assert hasattr(inference, 'inference_rules')
        
    def test_simple_logical_chain(self):
        """Test simple logical inference chain."""
        inference = LogicalInference()
        
        premises = [
            "If AI reduces errors, then outcomes improve",
            "AI reduces medical errors",
            "Better outcomes save lives"
        ]
        
        chain = inference.build_inference_chain(premises)
        
        assert chain is not None
        assert len(chain['steps']) > 0
        assert 'conclusion' in chain
        assert chain['validity_score'] >= 0.0
        
    def test_contradictory_premises_detection(self):
        """Test detection of contradictory premises."""
        inference = LogicalInference()
        
        contradictory_premises = [
            "AI always improves healthcare outcomes",
            "AI sometimes worsens healthcare outcomes",
            "Budget constraints limit AI implementation"
        ]
        
        result = inference.analyze_consistency(contradictory_premises)
        
        assert result is not None
        assert 'contradictions' in result
        assert len(result['contradictions']) > 0
        assert result['consistency_score'] < 0.8  # Should detect inconsistency
        
    def test_inference_confidence_scoring(self):
        """Test confidence scoring for logical inferences."""
        inference = LogicalInference()
        
        strong_premises = [
            "Evidence shows AI reduces diagnostic errors by 30%",
            "Reduced diagnostic errors directly improve patient outcomes",
            "Improved patient outcomes save lives"
        ]
        
        weak_premises = [
            "AI might potentially help healthcare",
            "Some people think outcomes could improve",
            "Maybe lives are saved"
        ]
        
        strong_result = inference.calculate_confidence(strong_premises)
        weak_result = inference.calculate_confidence(weak_premises)
        
        assert strong_result['confidence'] > weak_result['confidence']
        assert strong_result['confidence'] >= 0.7
        assert weak_result['confidence'] <= 0.5


class TestMultiDimensionalEvaluator:
    """Test cases for multi-dimensional evaluation system."""
    
    def test_evaluator_initialization(self):
        """Test MultiDimensionalEvaluator initialization."""
        evaluator = MultiDimensionalEvaluator()
        
        assert evaluator is not None
        assert hasattr(evaluator, 'evaluation_dimensions')
        assert len(evaluator.evaluation_dimensions) > 0
        
    def test_default_evaluation_dimensions(self):
        """Test that default evaluation dimensions are properly set."""
        evaluator = MultiDimensionalEvaluator()
        
        expected_dimensions = [
            'feasibility', 'innovation', 'impact', 'cost_effectiveness', 
            'scalability', 'risk_assessment', 'timeline'
        ]
        
        for dimension in expected_dimensions:
            assert dimension in evaluator.evaluation_dimensions
            
    def test_custom_evaluation_dimensions(self):
        """Test evaluator with custom dimensions."""
        custom_dimensions = {
            'technical_complexity': {'weight': 0.3, 'range': (1, 10)},
            'market_potential': {'weight': 0.4, 'range': (1, 10)},
            'regulatory_compliance': {'weight': 0.3, 'range': (1, 10)}
        }
        
        evaluator = MultiDimensionalEvaluator(dimensions=custom_dimensions)
        
        assert evaluator.evaluation_dimensions == custom_dimensions
        
    def test_multi_dimensional_scoring(self):
        """Test multi-dimensional scoring of an idea."""
        evaluator = MultiDimensionalEvaluator()
        
        idea = "AI-powered diagnostic tool for rural healthcare"
        context = {
            'budget': 'limited',
            'timeline': '6 months',
            'target_audience': 'rural communities',
            'regulatory_requirements': 'FDA approval needed'
        }
        
        evaluation = evaluator.evaluate_idea(idea, context)
        
        assert evaluation is not None
        assert 'overall_score' in evaluation
        assert 'dimension_scores' in evaluation
        assert 'weighted_score' in evaluation
        assert 'confidence_interval' in evaluation
        
        # Check that all dimensions are evaluated
        for dimension in evaluator.evaluation_dimensions:
            assert dimension in evaluation['dimension_scores']
            
        # Check score ranges
        assert 1 <= evaluation['overall_score'] <= 10
        assert 0.0 <= evaluation['confidence_interval'] <= 1.0
        
    def test_comparative_evaluation(self):
        """Test comparative evaluation between multiple ideas."""
        evaluator = MultiDimensionalEvaluator()
        
        ideas = [
            "AI diagnostic tool for hospitals",
            "Telemedicine platform for rural areas", 
            "Wearable health monitoring device"
        ]
        
        context = {'budget': 'medium', 'timeline': '12 months'}
        
        comparison = evaluator.compare_ideas(ideas, context)
        
        assert comparison is not None
        assert 'rankings' in comparison
        assert 'relative_scores' in comparison
        assert len(comparison['rankings']) == len(ideas)
        
        # Check that rankings are properly ordered
        rankings = comparison['rankings']
        for i in range(len(rankings) - 1):
            assert rankings[i]['score'] >= rankings[i + 1]['score']


class TestAgentConversationTracker:
    """Test cases for agent conversation tracking system."""
    
    def test_tracker_initialization(self):
        """Test AgentConversationTracker initialization."""
        tracker = AgentConversationTracker()
        
        assert tracker is not None
        assert hasattr(tracker, 'conversation_history')
        assert len(tracker.conversation_history) == 0
        
    def test_track_agent_interaction(self):
        """Test tracking of agent interactions."""
        tracker = AgentConversationTracker()
        
        interaction = {
            'agent': 'idea_generator',
            'input': 'AI healthcare',
            'output': 'Smart diagnostic tools',
            'timestamp': '2025-07-03T10:00:00',
            'metadata': {'temperature': 0.8}
        }
        
        interaction_id = tracker.add_interaction(interaction)
        retrieved = tracker.get_interaction(interaction_id)
        
        assert retrieved == interaction
        assert len(tracker.conversation_history) == 1
        
    def test_conversation_flow_analysis(self):
        """Test analysis of conversation flow patterns."""
        tracker = AgentConversationTracker()
        
        # Simulate a complete workflow
        interactions = [
            {'agent': 'idea_generator', 'output': 'Idea A'},
            {'agent': 'critic', 'input': 'Idea A', 'output': 'Score: 8'},
            {'agent': 'advocate', 'input': 'Idea A', 'output': 'Strong benefits'},
            {'agent': 'skeptic', 'input': 'Idea A', 'output': 'Potential risks'}
        ]
        
        for interaction in interactions:
            tracker.add_interaction(interaction)
            
        flow_analysis = tracker.analyze_conversation_flow()
        
        assert flow_analysis is not None
        assert 'agent_sequence' in flow_analysis
        assert 'interaction_count' in flow_analysis
        assert 'workflow_completeness' in flow_analysis
        assert flow_analysis['interaction_count'] == 4
        
    def test_context_extraction_from_history(self):
        """Test extraction of relevant context from conversation history."""
        tracker = AgentConversationTracker()
        
        # Add multiple interactions
        interactions = [
            {'agent': 'idea_generator', 'input': 'healthcare AI', 'output': 'diagnostic tool'},
            {'agent': 'critic', 'output': 'feasible but needs validation'},
            {'agent': 'idea_generator', 'input': 'education AI', 'output': 'learning platform'}
        ]
        
        for interaction in interactions:
            tracker.add_interaction(interaction)
            
        # Extract context for healthcare-related query
        relevant_context = tracker.extract_relevant_context('healthcare diagnostic validation')
        
        assert relevant_context is not None
        assert len(relevant_context) > 0
        # Should find healthcare-related interactions
        healthcare_found = any('healthcare' in str(ctx) or 'diagnostic' in str(ctx) 
                              for ctx in relevant_context)
        assert healthcare_found


# Integration Tests
class TestEnhancedReasoningIntegration:
    """Integration tests for the enhanced reasoning system."""
    
    @pytest.fixture
    def reasoning_system(self):
        """Create a complete reasoning system for testing."""
        config = {
            'memory_capacity': 100,
            'inference_depth': 3,
            'evaluation_dimensions': {
                'feasibility': {'weight': 0.4},
                'innovation': {'weight': 0.3},
                'impact': {'weight': 0.3}
            }
        }
        return ReasoningEngine(config=config)
        
    def test_full_reasoning_workflow(self, reasoning_system):
        """Test complete reasoning workflow with all components."""
        # Simulate a multi-agent conversation
        conversation_data = {
            'theme': 'AI healthcare solutions',
            'constraints': 'Budget-friendly, rural deployment',
            'previous_interactions': [
                {'agent': 'idea_generator', 'output': 'Telemedicine platform'},
                {'agent': 'critic', 'output': 'Score: 7, good concept but implementation challenges'}
            ],
            'current_request': {
                'agent': 'advocate',
                'idea': 'Telemedicine platform',
                'context': 'Rural healthcare access'
            }
        }
        
        result = reasoning_system.process_complete_workflow(conversation_data)
        
        assert result is not None
        assert 'enhanced_reasoning' in result
        assert 'context_awareness' in result
        assert 'logical_inference' in result
        assert 'multi_dimensional_evaluation' in result
        
        # Check reasoning quality metrics
        assert 'reasoning_quality_score' in result
        assert 0.0 <= result['reasoning_quality_score'] <= 1.0
        
    def test_reasoning_consistency_across_agents(self, reasoning_system):
        """Test that reasoning remains consistent across different agent interactions."""
        base_context = {
            'theme': 'sustainable technology',
            'constraints': 'cost-effective, scalable'
        }
        
        # Test consistency across multiple agent calls
        agents = ['idea_generator', 'critic', 'advocate', 'skeptic']
        results = []
        
        for agent in agents:
            request = {
                'agent': agent,
                'context': base_context,
                'input': 'solar-powered water purification'
            }
            result = reasoning_system.process_agent_request(request)
            results.append(result)
            
        # Check consistency metrics
        consistency_score = reasoning_system.calculate_consistency_score(results)
        assert consistency_score >= 0.7  # Should maintain reasonable consistency
        
    def test_reasoning_improvement_over_time(self, reasoning_system):
        """Test that reasoning quality improves with more conversation history."""
        # Simulate minimal context
        minimal_context = {'agent': 'critic', 'input': 'AI tool'}
        result_minimal = reasoning_system.process_agent_request(minimal_context)
        
        # Simulate rich context with conversation history
        rich_context = {
            'agent': 'critic',
            'input': 'AI diagnostic tool for rural healthcare',
            'conversation_history': [
                {'agent': 'idea_generator', 'theme': 'healthcare accessibility'},
                {'constraint': 'rural deployment challenges'},
                {'previous_evaluation': 'feasibility concerns about connectivity'},
                {'market_analysis': 'high demand in underserved areas'}
            ]
        }
        result_rich = reasoning_system.process_agent_request(rich_context)
        
        # Rich context should produce higher quality reasoning
        assert result_rich['reasoning_quality_score'] > result_minimal['reasoning_quality_score']
        assert len(result_rich.get('contextual_insights', [])) > len(result_minimal.get('contextual_insights', []))