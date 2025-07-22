"""Comprehensive tests for enhanced reasoning functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from madspark.core.enhanced_reasoning import (
    EnhancedReasoning,
    ContextMemory,
    LogicalInference,
    MultiDimensionalEvaluator,
    CandidateData
)


class TestContextMemory:
    """Test cases for context memory management."""
    
    def test_context_memory_initialization(self):
        """Test ContextMemory initialization."""
        memory = ContextMemory(max_size=100)
        assert memory.max_size == 100
        assert len(memory.memories) == 0
        assert memory.current_context == {}
    
    def test_add_memory(self):
        """Test adding memories to context."""
        memory = ContextMemory(max_size=5)
        
        # Add memories
        memory.add_memory("idea", "AI automation tool")
        memory.add_memory("evaluation", "Score: 7.5")
        memory.add_memory("feedback", "Needs scalability improvements")
        
        assert len(memory.memories) == 3
        assert memory.memories[0] == ("idea", "AI automation tool")
        assert memory.memories[1] == ("evaluation", "Score: 7.5")
    
    def test_memory_size_limit(self):
        """Test memory size limit enforcement."""
        memory = ContextMemory(max_size=3)
        
        # Add more than max_size memories
        memory.add_memory("memory1", "value1")
        memory.add_memory("memory2", "value2")
        memory.add_memory("memory3", "value3")
        memory.add_memory("memory4", "value4")  # Should evict oldest
        
        assert len(memory.memories) == 3
        # Oldest (memory1) should be evicted
        assert ("memory1", "value1") not in memory.memories
        assert ("memory4", "value4") in memory.memories
    
    def test_update_context(self):
        """Test updating current context."""
        memory = ContextMemory()
        
        # Update context
        memory.update_context("theme", "AI automation")
        memory.update_context("constraints", "Budget-friendly")
        memory.update_context("score", 8.5)
        
        assert memory.current_context["theme"] == "AI automation"
        assert memory.current_context["constraints"] == "Budget-friendly"
        assert memory.current_context["score"] == 8.5
    
    def test_get_relevant_memories(self):
        """Test retrieving relevant memories."""
        memory = ContextMemory()
        
        # Add various memories
        memory.add_memory("idea", "AI task automation")
        memory.add_memory("idea", "ML optimization tool")
        memory.add_memory("evaluation", "Good feasibility")
        memory.add_memory("idea", "Data analytics platform")
        
        # Get memories by type
        idea_memories = memory.get_relevant_memories(memory_type="idea")
        assert len(idea_memories) == 3
        assert all(m[0] == "idea" for m in idea_memories)
        
        eval_memories = memory.get_relevant_memories(memory_type="evaluation")
        assert len(eval_memories) == 1
        assert eval_memories[0][1] == "Good feasibility"
    
    def test_get_relevant_memories_with_limit(self):
        """Test retrieving limited number of memories."""
        memory = ContextMemory()
        
        # Add many memories
        for i in range(10):
            memory.add_memory("idea", f"Idea {i}")
        
        # Get limited memories
        recent_ideas = memory.get_relevant_memories(memory_type="idea", limit=3)
        assert len(recent_ideas) == 3
        # Should get most recent ones
        assert recent_ideas[0][1] == "Idea 9"
        assert recent_ideas[1][1] == "Idea 8"
        assert recent_ideas[2][1] == "Idea 7"
    
    def test_clear_memories(self):
        """Test clearing all memories."""
        memory = ContextMemory()
        
        # Add memories and context
        memory.add_memory("test", "value")
        memory.update_context("key", "value")
        
        # Clear
        memory.clear()
        
        assert len(memory.memories) == 0
        assert memory.current_context == {}


class TestLogicalInference:
    """Test cases for logical inference engine."""
    
    def test_logical_inference_initialization(self):
        """Test LogicalInference initialization."""
        inference = LogicalInference(confidence_threshold=0.6)
        assert inference.confidence_threshold == 0.6
        assert len(inference.rules) > 0  # Should have default rules
    
    def test_add_rule(self):
        """Test adding inference rules."""
        inference = LogicalInference()
        
        # Add custom rule
        def custom_rule(context):
            if context.get("score", 0) > 8:
                return {"conclusion": "Highly promising", "confidence": 0.9}
            return None
        
        inference.add_rule("high_score_rule", custom_rule)
        assert "high_score_rule" in inference.rules
    
    def test_apply_rules_basic(self):
        """Test applying inference rules."""
        inference = LogicalInference(confidence_threshold=0.5)
        
        # Add simple rule
        def score_rule(context):
            score = context.get("score", 0)
            if score >= 7:
                return {
                    "conclusion": "Good candidate",
                    "confidence": score / 10,
                    "reasoning": f"Score of {score} indicates quality"
                }
            return None
        
        inference.add_rule("score_assessment", score_rule)
        
        # Apply rules
        context = {"score": 8.5}
        inferences = inference.apply_rules(context)
        
        assert len(inferences) >= 1
        assert any(inf["conclusion"] == "Good candidate" for inf in inferences)
        assert any(inf["confidence"] == 0.85 for inf in inferences)
    
    def test_confidence_threshold_filtering(self):
        """Test that low confidence inferences are filtered."""
        inference = LogicalInference(confidence_threshold=0.7)
        
        # Add rules with different confidence levels
        def high_conf_rule(context):
            return {"conclusion": "High confidence", "confidence": 0.9}
        
        def low_conf_rule(context):
            return {"conclusion": "Low confidence", "confidence": 0.4}
        
        inference.add_rule("high", high_conf_rule)
        inference.add_rule("low", low_conf_rule)
        
        inferences = inference.apply_rules({})
        
        # Only high confidence inference should pass threshold
        assert len(inferences) == 1
        assert inferences[0]["conclusion"] == "High confidence"
    
    def test_default_rules(self):
        """Test default inference rules."""
        inference = LogicalInference()
        
        # Test feasibility inference
        context = {
            "feasibility_score": 9,
            "technical_complexity": "low"
        }
        inferences = inference.apply_rules(context)
        assert any("feasible" in inf.get("conclusion", "").lower() for inf in inferences)
        
        # Test innovation inference
        context = {
            "innovation_score": 9.5,
            "novelty": "high"
        }
        inferences = inference.apply_rules(context)
        assert any("innovative" in inf.get("conclusion", "").lower() for inf in inferences)
    
    def test_complex_rule_chaining(self):
        """Test complex rule interactions."""
        inference = LogicalInference()
        
        # Add interdependent rules
        def market_rule(context):
            if context.get("market_size", 0) > 1000000:
                return {
                    "conclusion": "Large market opportunity",
                    "confidence": 0.8,
                    "market_analysis": True
                }
            return None
        
        def investment_rule(context):
            # Depends on market analysis
            if context.get("market_analysis") and context.get("roi_potential", 0) > 2:
                return {
                    "conclusion": "Strong investment candidate",
                    "confidence": 0.85
                }
            return None
        
        inference.add_rule("market", market_rule)
        inference.add_rule("investment", investment_rule)
        
        context = {
            "market_size": 5000000,
            "roi_potential": 3.5
        }
        
        # First pass
        inferences = inference.apply_rules(context)
        
        # Update context with inferences
        for inf in inferences:
            if "market_analysis" in inf:
                context["market_analysis"] = inf["market_analysis"]
        
        # Second pass with updated context
        inferences = inference.apply_rules(context)
        
        assert any(inf["conclusion"] == "Strong investment candidate" for inf in inferences)


class TestMultiDimensionalEvaluator:
    """Test cases for multi-dimensional evaluation."""
    
    def test_evaluator_initialization(self):
        """Test MultiDimensionalEvaluator initialization."""
        evaluator = MultiDimensionalEvaluator()
        assert len(evaluator.dimensions) > 0
        assert "feasibility" in evaluator.dimensions
        assert "innovation" in evaluator.dimensions
        assert "impact" in evaluator.dimensions
    
    def test_evaluate_basic(self):
        """Test basic multi-dimensional evaluation."""
        evaluator = MultiDimensionalEvaluator()
        
        candidate = CandidateData(
            idea="AI automation tool",
            initial_score=7.5,
            initial_critique="Good potential",
            advocacy="Strong market demand",
            skepticism="High competition",
            improved_idea="Enhanced AI automation",
            improved_score=8.5,
            improved_critique="Better differentiation",
            confidence=0.8,
            dimension_scores={}
        )
        
        scores = evaluator.evaluate(candidate, {})
        
        assert "feasibility" in scores
        assert "innovation" in scores
        assert "impact" in scores
        assert "scalability" in scores
        assert all(0 <= score <= 10 for score in scores.values())
    
    def test_evaluate_with_context(self):
        """Test evaluation with context influence."""
        evaluator = MultiDimensionalEvaluator()
        
        candidate = CandidateData(
            idea="Budget AI solution",
            initial_score=6.0,
            initial_critique="Limited features",
            advocacy="Cost-effective",
            skepticism="Feature limitations",
            improved_idea="Modular budget AI",
            improved_score=7.0,
            improved_critique="Better value proposition",
            confidence=0.7,
            dimension_scores={}
        )
        
        context = {
            "constraints": "Budget-friendly, quick deployment",
            "target_market": "Small businesses",
            "priority": "cost_effectiveness"
        }
        
        scores = evaluator.evaluate(candidate, context)
        
        # Cost effectiveness should be weighted higher due to context
        assert "cost_effectiveness" in scores
        assert scores["cost_effectiveness"] >= 7.0  # Should be high due to context
    
    def test_custom_dimensions(self):
        """Test adding custom evaluation dimensions."""
        evaluator = MultiDimensionalEvaluator()
        
        # Add custom dimension
        def sustainability_evaluator(candidate, context):
            # Evaluate environmental sustainability
            if "green" in candidate.idea.lower() or "sustainable" in candidate.idea.lower():
                return 9.0
            return 5.0
        
        evaluator.add_dimension("sustainability", sustainability_evaluator)
        
        candidate = CandidateData(
            idea="Green energy optimization system",
            initial_score=7.0,
            initial_critique="Good",
            advocacy="Eco-friendly",
            skepticism="Initial costs",
            improved_idea="Sustainable energy platform",
            improved_score=8.0,
            improved_critique="Better",
            confidence=0.8,
            dimension_scores={}
        )
        
        scores = evaluator.evaluate(candidate, {})
        
        assert "sustainability" in scores
        assert scores["sustainability"] == 9.0
    
    def test_score_aggregation(self):
        """Test aggregating multi-dimensional scores."""
        evaluator = MultiDimensionalEvaluator()
        
        scores = {
            "feasibility": 8.0,
            "innovation": 9.0,
            "impact": 7.5,
            "scalability": 8.5,
            "cost_effectiveness": 7.0
        }
        
        # Test weighted average
        weights = {
            "feasibility": 0.3,
            "innovation": 0.2,
            "impact": 0.2,
            "scalability": 0.2,
            "cost_effectiveness": 0.1
        }
        
        weighted_score = evaluator.aggregate_scores(scores, weights)
        expected = (8.0*0.3 + 9.0*0.2 + 7.5*0.2 + 8.5*0.2 + 7.0*0.1)
        assert abs(weighted_score - expected) < 0.01
        
        # Test unweighted average
        unweighted_score = evaluator.aggregate_scores(scores)
        expected = sum(scores.values()) / len(scores)
        assert abs(unweighted_score - expected) < 0.01


class TestEnhancedReasoning:
    """Test cases for the main EnhancedReasoning system."""
    
    def test_enhanced_reasoning_initialization(self):
        """Test EnhancedReasoning initialization."""
        reasoning = EnhancedReasoning(
            enable_context_memory=True,
            enable_logical_inference=True,
            memory_size=500
        )
        
        assert reasoning.enable_context_memory == True
        assert reasoning.enable_logical_inference == True
        assert reasoning.context_memory.max_size == 500
        assert reasoning.logical_inference is not None
        assert reasoning.evaluator is not None
    
    def test_process_candidate_basic(self):
        """Test processing a single candidate."""
        reasoning = EnhancedReasoning()
        
        candidate = CandidateData(
            idea="Test idea",
            initial_score=7.0,
            initial_critique="Good",
            advocacy="Strong",
            skepticism="Some risks",
            improved_idea="Better test idea",
            improved_score=8.0,
            improved_critique="Improved",
            confidence=0.8,
            dimension_scores={}
        )
        
        enhanced = reasoning.process_candidate(candidate, {"theme": "Testing"})
        
        assert enhanced.dimension_scores is not None
        assert len(enhanced.dimension_scores) > 0
        assert enhanced.confidence >= 0.8  # Should maintain or improve confidence
    
    def test_process_candidate_with_memory(self):
        """Test processing with context memory enabled."""
        reasoning = EnhancedReasoning(enable_context_memory=True)
        
        # Process first candidate
        candidate1 = CandidateData(
            idea="AI tool v1",
            initial_score=6.0,
            initial_critique="Needs work",
            advocacy="Potential",
            skepticism="Limited",
            improved_idea="AI tool v2",
            improved_score=7.0,
            improved_critique="Better",
            confidence=0.7,
            dimension_scores={}
        )
        
        enhanced1 = reasoning.process_candidate(candidate1, {"theme": "AI tools"})
        
        # Process second candidate - should have memory of first
        candidate2 = CandidateData(
            idea="AI tool advanced",
            initial_score=7.5,
            initial_critique="Good iteration",
            advocacy="Builds on v2",
            skepticism="Complexity",
            improved_idea="AI tool pro",
            improved_score=8.5,
            improved_critique="Excellent",
            confidence=0.8,
            dimension_scores={}
        )
        
        enhanced2 = reasoning.process_candidate(candidate2, {"theme": "AI tools"})
        
        # Second candidate should benefit from context
        assert enhanced2.confidence > candidate2.confidence
        
        # Check memory was updated
        memories = reasoning.context_memory.get_relevant_memories("candidate")
        assert len(memories) >= 2
    
    def test_process_candidate_with_inference(self):
        """Test processing with logical inference enabled."""
        reasoning = EnhancedReasoning(enable_logical_inference=True)
        
        candidate = CandidateData(
            idea="Revolutionary AI platform",
            initial_score=9.0,
            initial_critique="Groundbreaking",
            advocacy="Game-changing potential",
            skepticism="Very ambitious",
            improved_idea="Phased revolutionary AI",
            improved_score=9.5,
            improved_critique="More feasible approach",
            confidence=0.85,
            dimension_scores={"innovation": 9.5, "feasibility": 7.0}
        )
        
        context = {
            "market_size": 10000000,
            "competition": "low",
            "technical_readiness": "high"
        }
        
        enhanced = reasoning.process_candidate(candidate, context)
        
        # Should have inferences
        assert hasattr(enhanced, 'inferences') or enhanced.confidence > 0.85
        # High scores should boost confidence
        assert enhanced.confidence >= 0.9
    
    def test_batch_processing(self):
        """Test processing multiple candidates."""
        reasoning = EnhancedReasoning(
            enable_context_memory=True,
            enable_logical_inference=True
        )
        
        candidates = [
            CandidateData(
                idea=f"Idea {i}",
                initial_score=6.0 + i * 0.5,
                initial_critique="OK",
                advocacy="Good",
                skepticism="Some issues",
                improved_idea=f"Better idea {i}",
                improved_score=7.0 + i * 0.5,
                improved_critique="Improved",
                confidence=0.7,
                dimension_scores={}
            )
            for i in range(5)
        ]
        
        context = {"theme": "Batch processing test"}
        enhanced_candidates = reasoning.process_batch(candidates, context)
        
        assert len(enhanced_candidates) == 5
        # All should be enhanced
        assert all(c.dimension_scores for c in enhanced_candidates)
        
        # Later candidates should benefit from earlier context
        assert enhanced_candidates[-1].confidence >= enhanced_candidates[0].confidence
    
    def test_generate_insights(self):
        """Test insight generation from processed candidates."""
        reasoning = EnhancedReasoning()
        
        candidates = [
            CandidateData(
                idea="Blockchain solution",
                initial_score=8.0,
                initial_critique="Innovative",
                advocacy="Decentralized benefits",
                skepticism="Complexity",
                improved_idea="Simplified blockchain",
                improved_score=8.5,
                improved_critique="More accessible",
                confidence=0.8,
                dimension_scores={
                    "innovation": 9.0,
                    "feasibility": 6.5,
                    "impact": 8.0,
                    "scalability": 7.0
                }
            ),
            CandidateData(
                idea="AI analytics",
                initial_score=7.5,
                initial_critique="Practical",
                advocacy="Clear ROI",
                skepticism="Competition",
                improved_idea="Specialized AI analytics",
                improved_score=8.0,
                improved_critique="Better positioning",
                confidence=0.75,
                dimension_scores={
                    "innovation": 7.0,
                    "feasibility": 8.5,
                    "impact": 7.5,
                    "scalability": 8.0
                }
            )
        ]
        
        insights = reasoning.generate_insights(candidates)
        
        assert "patterns" in insights
        assert "recommendations" in insights
        assert "top_dimensions" in insights
        
        # Should identify innovation as a key dimension
        assert any("innovation" in dim.lower() for dim in insights.get("top_dimensions", []))
    
    def test_reasoning_with_disabled_features(self):
        """Test reasoning with features disabled."""
        reasoning = EnhancedReasoning(
            enable_context_memory=False,
            enable_logical_inference=False
        )
        
        candidate = CandidateData(
            idea="Simple idea",
            initial_score=7.0,
            initial_critique="Good",
            advocacy="Positive",
            skepticism="Minor issues",
            improved_idea="Better idea",
            improved_score=7.5,
            improved_critique="Improved",
            confidence=0.7,
            dimension_scores={}
        )
        
        enhanced = reasoning.process_candidate(candidate, {})
        
        # Should still work but with basic enhancement only
        assert enhanced.dimension_scores is not None
        assert enhanced.confidence == 0.7  # No boost without features
    
    def test_clear_context(self):
        """Test clearing reasoning context."""
        reasoning = EnhancedReasoning(enable_context_memory=True)
        
        # Add some context
        candidate = CandidateData(
            idea="Test",
            initial_score=7.0,
            initial_critique="OK",
            advocacy="Good",
            skepticism="Bad",
            improved_idea="Better",
            improved_score=8.0,
            improved_critique="Good",
            confidence=0.8,
            dimension_scores={}
        )
        
        reasoning.process_candidate(candidate, {"test": "data"})
        
        # Verify context exists
        assert len(reasoning.context_memory.memories) > 0
        
        # Clear context
        reasoning.clear_context()
        
        # Verify context is cleared
        assert len(reasoning.context_memory.memories) == 0


class TestEnhancedReasoningEdgeCases:
    """Test edge cases and error handling."""
    
    def test_process_candidate_with_missing_fields(self):
        """Test processing candidate with missing optional fields."""
        reasoning = EnhancedReasoning()
        
        # Minimal candidate
        candidate = CandidateData(
            idea="Minimal idea",
            initial_score=5.0,
            initial_critique=None,
            advocacy=None,
            skepticism=None,
            improved_idea="Slightly better",
            improved_score=5.5,
            improved_critique=None,
            confidence=None,
            dimension_scores=None
        )
        
        enhanced = reasoning.process_candidate(candidate, {})
        
        # Should handle gracefully
        assert enhanced.dimension_scores is not None
        assert enhanced.confidence is not None
        assert enhanced.confidence > 0
    
    def test_process_empty_batch(self):
        """Test processing empty candidate batch."""
        reasoning = EnhancedReasoning()
        
        enhanced = reasoning.process_batch([], {})
        
        assert enhanced == []
    
    def test_very_large_memory(self):
        """Test with very large memory size."""
        reasoning = EnhancedReasoning(
            enable_context_memory=True,
            memory_size=10000
        )
        
        # Add many memories
        for i in range(100):
            candidate = CandidateData(
                idea=f"Idea {i}",
                initial_score=7.0,
                initial_critique="OK",
                advocacy="Good",
                skepticism="Bad",
                improved_idea=f"Better {i}",
                improved_score=8.0,
                improved_critique="Good",
                confidence=0.8,
                dimension_scores={}
            )
            reasoning.process_candidate(candidate, {"index": i})
        
        # Should handle large memory efficiently
        assert len(reasoning.context_memory.memories) <= 10000
        
        # Should still be able to retrieve relevant memories
        memories = reasoning.context_memory.get_relevant_memories("candidate", limit=10)
        assert len(memories) == 10
    
    def test_invalid_confidence_threshold(self):
        """Test with invalid confidence thresholds."""
        # Should handle gracefully
        reasoning1 = EnhancedReasoning(
            enable_logical_inference=True,
            inference_confidence_threshold=-0.5  # Invalid negative
        )
        assert reasoning1.logical_inference.confidence_threshold == 0.0  # Should clamp
        
        reasoning2 = EnhancedReasoning(
            enable_logical_inference=True,
            inference_confidence_threshold=2.0  # Invalid > 1
        )
        assert reasoning2.logical_inference.confidence_threshold == 1.0  # Should clamp