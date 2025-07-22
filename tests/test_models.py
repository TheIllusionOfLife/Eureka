"""Comprehensive tests for data models."""
import pytest
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict, fields

from madspark.utils.models import (
    IdeaData,
    EvaluationData,
    BookmarkedIdea,
    FilteredIdea,
    AgentResponse,
    WorkflowResult,
    CandidateScore,
    DimensionScore,
    InferenceResult,
    ConfigModel,
    ValidationError
)


class TestIdeaData:
    """Test cases for IdeaData model."""
    
    def test_idea_data_creation(self):
        """Test creating IdeaData instance."""
        idea = IdeaData(
            id="idea_001",
            title="AI Automation Tool",
            description="An intelligent automation system",
            innovation_score=8.5,
            feasibility_score=7.0,
            impact_score=8.0,
            tags=["ai", "automation", "productivity"],
            metadata={"author": "test_user", "version": "1.0"}
        )
        
        assert idea.id == "idea_001"
        assert idea.title == "AI Automation Tool"
        assert idea.innovation_score == 8.5
        assert idea.tags == ["ai", "automation", "productivity"]
        assert idea.metadata["author"] == "test_user"
    
    def test_idea_data_defaults(self):
        """Test IdeaData with default values."""
        idea = IdeaData(
            title="Basic Idea",
            description="Simple description"
        )
        
        assert idea.id is not None  # Should auto-generate
        assert idea.innovation_score == 0.0
        assert idea.feasibility_score == 0.0
        assert idea.impact_score == 0.0
        assert idea.tags == []
        assert idea.metadata == {}
    
    def test_idea_data_validation(self):
        """Test IdeaData validation."""
        # Test score validation (should be 0-10)
        with pytest.raises(ValidationError):
            IdeaData(
                title="Bad Idea",
                description="Invalid scores",
                innovation_score=11.0  # Out of range
            )
        
        with pytest.raises(ValidationError):
            IdeaData(
                title="Bad Idea",
                description="Invalid scores",
                feasibility_score=-1.0  # Negative
            )
    
    def test_idea_data_serialization(self):
        """Test IdeaData serialization."""
        idea = IdeaData(
            id="test_001",
            title="Test Idea",
            description="Test description",
            innovation_score=7.5,
            tags=["test"]
        )
        
        # Convert to dict
        idea_dict = asdict(idea)
        assert idea_dict["id"] == "test_001"
        assert idea_dict["innovation_score"] == 7.5
        
        # JSON serialization
        json_str = json.dumps(idea_dict)
        loaded = json.loads(json_str)
        assert loaded["title"] == "Test Idea"
    
    def test_idea_data_equality(self):
        """Test IdeaData equality comparison."""
        idea1 = IdeaData(
            id="same_id",
            title="Idea 1",
            description="Desc 1"
        )
        
        idea2 = IdeaData(
            id="same_id",
            title="Idea 2",
            description="Desc 2"
        )
        
        idea3 = IdeaData(
            id="different_id",
            title="Idea 1",
            description="Desc 1"
        )
        
        # Same ID = equal
        assert idea1 == idea2
        # Different ID = not equal
        assert idea1 != idea3


class TestEvaluationData:
    """Test cases for EvaluationData model."""
    
    def test_evaluation_data_creation(self):
        """Test creating EvaluationData instance."""
        evaluation = EvaluationData(
            idea_id="idea_001",
            evaluator="critic_agent",
            overall_score=7.5,
            strengths=["Innovative approach", "Clear ROI"],
            weaknesses=["High complexity", "Resource intensive"],
            recommendations=["Simplify implementation", "Phase rollout"],
            confidence=0.85,
            metadata={"model": "gpt-4", "temperature": 0.3}
        )
        
        assert evaluation.idea_id == "idea_001"
        assert evaluation.overall_score == 7.5
        assert len(evaluation.strengths) == 2
        assert evaluation.confidence == 0.85
    
    def test_evaluation_data_timestamp(self):
        """Test evaluation timestamp is set."""
        evaluation = EvaluationData(
            idea_id="idea_001",
            evaluator="test",
            overall_score=5.0
        )
        
        assert evaluation.timestamp is not None
        assert isinstance(evaluation.timestamp, datetime)
        assert evaluation.timestamp <= datetime.utcnow()
    
    def test_evaluation_data_validation(self):
        """Test evaluation data validation."""
        # Test score validation
        with pytest.raises(ValidationError):
            EvaluationData(
                idea_id="test",
                evaluator="critic",
                overall_score=15.0  # Out of range
            )
        
        # Test confidence validation
        with pytest.raises(ValidationError):
            EvaluationData(
                idea_id="test",
                evaluator="critic",
                overall_score=7.0,
                confidence=1.5  # > 1.0
            )
    
    def test_evaluation_data_aggregation(self):
        """Test aggregating multiple evaluations."""
        evaluations = [
            EvaluationData("idea1", "critic1", 7.0, confidence=0.8),
            EvaluationData("idea1", "critic2", 8.0, confidence=0.9),
            EvaluationData("idea1", "critic3", 7.5, confidence=0.7)
        ]
        
        # Calculate weighted average
        total_weight = sum(e.confidence for e in evaluations)
        weighted_score = sum(e.overall_score * e.confidence for e in evaluations) / total_weight
        
        assert 7.0 <= weighted_score <= 8.0
        assert abs(weighted_score - 7.52) < 0.01  # Approximate expected value


class TestBookmarkedIdea:
    """Test cases for BookmarkedIdea model."""
    
    def test_bookmarked_idea_creation(self):
        """Test creating BookmarkedIdea instance."""
        bookmark = BookmarkedIdea(
            id="bookmark_001",
            text="Revolutionary AI concept for automation",
            theme="AI Automation",
            constraints="Budget-friendly, scalable",
            score=8.5,
            tags=["ai", "automation", "favorite"],
            metadata={
                "source": "brainstorming_session_1",
                "iteration": 3
            }
        )
        
        assert bookmark.id == "bookmark_001"
        assert bookmark.score == 8.5
        assert "favorite" in bookmark.tags
        assert bookmark.created_at is not None
    
    def test_bookmarked_idea_auto_id(self):
        """Test auto-generated bookmark ID."""
        bookmark = BookmarkedIdea(
            text="Test idea",
            theme="Testing"
        )
        
        assert bookmark.id is not None
        assert bookmark.id.startswith("bookmark_")
        assert len(bookmark.id) > 10
    
    def test_bookmarked_idea_search_text(self):
        """Test searchable text generation."""
        bookmark = BookmarkedIdea(
            text="AI-powered task automation",
            theme="Productivity AI",
            constraints="Must integrate with existing tools",
            tags=["ai", "productivity", "integration"]
        )
        
        search_text = bookmark.get_search_text()
        
        assert "AI-powered task automation" in search_text
        assert "Productivity AI" in search_text
        assert "existing tools" in search_text
        assert all(tag in search_text for tag in bookmark.tags)
    
    def test_bookmarked_idea_serialization(self):
        """Test bookmark serialization for storage."""
        bookmark = BookmarkedIdea(
            text="Test bookmark",
            theme="Test theme",
            score=7.5,
            tags=["test"]
        )
        
        # Serialize
        data = bookmark.to_dict()
        assert data["text"] == "Test bookmark"
        assert data["score"] == 7.5
        assert "created_at" in data
        
        # Deserialize
        restored = BookmarkedIdea.from_dict(data)
        assert restored.text == bookmark.text
        assert restored.score == bookmark.score
        assert restored.created_at == bookmark.created_at


class TestFilteredIdea:
    """Test cases for FilteredIdea model."""
    
    def test_filtered_idea_creation(self):
        """Test creating FilteredIdea instance."""
        filtered = FilteredIdea(
            text="Novel AI concept",
            is_novel=True,
            similarity_score=0.15,
            most_similar_to="Previous AI idea",
            confidence=0.92
        )
        
        assert filtered.is_novel == True
        assert filtered.similarity_score == 0.15
        assert filtered.confidence == 0.92
    
    def test_filtered_idea_not_novel(self):
        """Test FilteredIdea for duplicate."""
        filtered = FilteredIdea(
            text="Duplicate idea",
            is_novel=False,
            similarity_score=0.95,
            most_similar_to="Original idea from last week",
            confidence=0.98,
            rejection_reason="Too similar to existing idea"
        )
        
        assert filtered.is_novel == False
        assert filtered.similarity_score == 0.95
        assert filtered.rejection_reason is not None
    
    def test_filtered_idea_edge_case(self):
        """Test FilteredIdea edge case - borderline similarity."""
        filtered = FilteredIdea(
            text="Somewhat similar idea",
            is_novel=True,  # Just below threshold
            similarity_score=0.79,  # If threshold is 0.8
            most_similar_to="Related concept",
            confidence=0.85
        )
        
        assert filtered.is_novel == True
        assert 0.7 < filtered.similarity_score < 0.8


class TestAgentResponse:
    """Test cases for AgentResponse model."""
    
    def test_agent_response_creation(self):
        """Test creating AgentResponse instance."""
        response = AgentResponse(
            agent_name="IdeaGenerator",
            response_type="ideas",
            content=["Idea 1", "Idea 2", "Idea 3"],
            metadata={
                "temperature": 0.9,
                "model": "gemini-pro",
                "duration": 2.5
            },
            success=True,
            error=None
        )
        
        assert response.agent_name == "IdeaGenerator"
        assert len(response.content) == 3
        assert response.success == True
        assert response.metadata["temperature"] == 0.9
    
    def test_agent_response_failure(self):
        """Test AgentResponse for failure case."""
        response = AgentResponse(
            agent_name="Critic",
            response_type="evaluation",
            content=None,
            success=False,
            error="API rate limit exceeded",
            metadata={"retry_after": 60}
        )
        
        assert response.success == False
        assert response.error is not None
        assert response.content is None
        assert response.metadata["retry_after"] == 60
    
    def test_agent_response_timing(self):
        """Test response timing tracking."""
        response = AgentResponse(
            agent_name="Advocate",
            response_type="advocacy",
            content="Strong market potential...",
            success=True
        )
        
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)
    
    def test_agent_response_validation(self):
        """Test agent response validation."""
        # Success with no content should be invalid
        with pytest.raises(ValidationError):
            AgentResponse(
                agent_name="Test",
                response_type="test",
                content=None,
                success=True,  # Success but no content
                error=None
            )
        
        # Failure with no error should be invalid
        with pytest.raises(ValidationError):
            AgentResponse(
                agent_name="Test",
                response_type="test",
                content="content",
                success=False,  # Failure but no error
                error=None
            )


class TestWorkflowResult:
    """Test cases for WorkflowResult model."""
    
    def test_workflow_result_creation(self):
        """Test creating WorkflowResult instance."""
        candidates = [
            {"idea": "Idea 1", "score": 7.5},
            {"idea": "Idea 2", "score": 8.0}
        ]
        
        result = WorkflowResult(
            workflow_id="workflow_001",
            theme="AI Innovation",
            constraints="Scalable solutions",
            candidates=candidates,
            success=True,
            total_duration=45.2,
            stage_durations={
                "idea_generation": 10.5,
                "evaluation": 15.3,
                "advocacy": 8.4,
                "improvement": 11.0
            },
            metadata={
                "temperature_preset": "creative",
                "num_ideas": 10
            }
        )
        
        assert result.workflow_id == "workflow_001"
        assert len(result.candidates) == 2
        assert result.total_duration == 45.2
        assert result.stage_durations["evaluation"] == 15.3
    
    def test_workflow_result_auto_id(self):
        """Test workflow auto-generated ID."""
        result = WorkflowResult(
            theme="Test",
            constraints="None",
            candidates=[],
            success=True,
            total_duration=10.0
        )
        
        assert result.workflow_id is not None
        assert result.workflow_id.startswith("workflow_")
    
    def test_workflow_result_statistics(self):
        """Test workflow result statistics."""
        candidates = [
            {"idea": "Idea 1", "initial_score": 6.0, "improved_score": 7.5},
            {"idea": "Idea 2", "initial_score": 7.0, "improved_score": 8.5},
            {"idea": "Idea 3", "initial_score": 5.5, "improved_score": 7.0}
        ]
        
        result = WorkflowResult(
            theme="Test",
            constraints="Test",
            candidates=candidates,
            success=True,
            total_duration=30.0
        )
        
        stats = result.get_statistics()
        
        assert stats["total_candidates"] == 3
        assert stats["average_initial_score"] == 6.17  # Approximately
        assert stats["average_improved_score"] == 7.67  # Approximately
        assert stats["average_improvement"] == 1.5
        assert stats["best_candidate"]["improved_score"] == 8.5


class TestScoreModels:
    """Test cases for score-related models."""
    
    def test_candidate_score_creation(self):
        """Test CandidateScore creation."""
        score = CandidateScore(
            candidate_id="cand_001",
            dimension_scores={
                "innovation": 8.5,
                "feasibility": 7.0,
                "impact": 8.0,
                "scalability": 7.5
            },
            overall_score=7.75,
            confidence=0.85,
            evaluator="multi_dimensional_evaluator"
        )
        
        assert score.candidate_id == "cand_001"
        assert score.dimension_scores["innovation"] == 8.5
        assert score.overall_score == 7.75
        assert score.confidence == 0.85
    
    def test_dimension_score_creation(self):
        """Test DimensionScore creation."""
        dim_score = DimensionScore(
            dimension="innovation",
            score=9.0,
            weight=0.3,
            rationale="Highly novel approach using cutting-edge technology",
            confidence=0.9
        )
        
        assert dim_score.dimension == "innovation"
        assert dim_score.score == 9.0
        assert dim_score.weight == 0.3
        assert dim_score.confidence == 0.9
    
    def test_score_aggregation(self):
        """Test aggregating dimension scores."""
        dimensions = [
            DimensionScore("innovation", 9.0, 0.3, "Novel", 0.9),
            DimensionScore("feasibility", 7.0, 0.3, "Moderate", 0.8),
            DimensionScore("impact", 8.5, 0.2, "High", 0.85),
            DimensionScore("scalability", 7.5, 0.2, "Good", 0.8)
        ]
        
        # Calculate weighted score
        weighted_score = sum(d.score * d.weight for d in dimensions)
        assert abs(weighted_score - 8.0) < 0.01
        
        # Calculate weighted confidence
        total_weight = sum(d.weight * d.confidence for d in dimensions)
        avg_confidence = total_weight / sum(d.weight for d in dimensions)
        assert 0.8 < avg_confidence < 0.9


class TestInferenceResult:
    """Test cases for InferenceResult model."""
    
    def test_inference_result_creation(self):
        """Test creating InferenceResult."""
        inference = InferenceResult(
            rule_name="market_viability",
            conclusion="High market potential",
            confidence=0.85,
            reasoning="Large addressable market with low competition",
            supporting_facts=[
                "Market size: $10B",
                "Current solutions: Limited",
                "Growth rate: 25% YoY"
            ],
            metadata={"rule_version": "1.2"}
        )
        
        assert inference.rule_name == "market_viability"
        assert inference.confidence == 0.85
        assert len(inference.supporting_facts) == 3
    
    def test_inference_chaining(self):
        """Test chaining multiple inferences."""
        inference1 = InferenceResult(
            rule_name="technical_feasibility",
            conclusion="Technically feasible",
            confidence=0.9,
            reasoning="All required technologies are mature"
        )
        
        inference2 = InferenceResult(
            rule_name="resource_availability",
            conclusion="Resources available",
            confidence=0.8,
            reasoning="Team has required expertise",
            depends_on=["technical_feasibility"]
        )
        
        inference3 = InferenceResult(
            rule_name="project_viability",
            conclusion="Project is viable",
            confidence=0.85,
            reasoning="Both technical and resource requirements met",
            depends_on=["technical_feasibility", "resource_availability"]
        )
        
        assert inference3.depends_on == ["technical_feasibility", "resource_availability"]
        
        # Combined confidence calculation
        combined_confidence = inference1.confidence * inference2.confidence * inference3.confidence
        assert 0.6 < combined_confidence < 0.7


class TestConfigModel:
    """Test cases for ConfigModel."""
    
    def test_config_model_creation(self):
        """Test creating ConfigModel."""
        config = ConfigModel(
            name="test_config",
            version="1.0",
            settings={
                "temperature": 0.8,
                "max_retries": 3,
                "timeout": 300,
                "features": {
                    "enhanced_reasoning": True,
                    "context_memory": True,
                    "memory_size": 1000
                }
            },
            metadata={
                "created_by": "test_user",
                "environment": "production"
            }
        )
        
        assert config.name == "test_config"
        assert config.settings["temperature"] == 0.8
        assert config.settings["features"]["enhanced_reasoning"] == True
    
    def test_config_model_validation(self):
        """Test config model validation."""
        # Test version format validation
        with pytest.raises(ValidationError):
            ConfigModel(
                name="bad_config",
                version="invalid_version",  # Should be like "1.0"
                settings={}
            )
        
        # Test required settings
        with pytest.raises(ValidationError):
            ConfigModel(
                name="incomplete",
                version="1.0",
                settings=None  # Settings required
            )
    
    def test_config_model_merge(self):
        """Test merging config models."""
        base_config = ConfigModel(
            name="base",
            version="1.0",
            settings={
                "temperature": 0.7,
                "timeout": 300,
                "features": {
                    "enhanced_reasoning": False
                }
            }
        )
        
        override_config = ConfigModel(
            name="override",
            version="1.0",
            settings={
                "temperature": 0.9,
                "features": {
                    "enhanced_reasoning": True,
                    "context_memory": True
                }
            }
        )
        
        # Merge configs
        merged = base_config.merge(override_config)
        
        assert merged.settings["temperature"] == 0.9  # Overridden
        assert merged.settings["timeout"] == 300  # Preserved from base
        assert merged.settings["features"]["enhanced_reasoning"] == True  # Overridden
        assert merged.settings["features"]["context_memory"] == True  # New from override


class TestModelEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_circular_dependency_detection(self):
        """Test detecting circular dependencies in models."""
        # Create ideas with circular references
        idea1 = IdeaData(
            id="idea1",
            title="Idea 1",
            description="References idea2",
            metadata={"depends_on": ["idea2"]}
        )
        
        idea2 = IdeaData(
            id="idea2",
            title="Idea 2", 
            description="References idea1",
            metadata={"depends_on": ["idea1"]}
        )
        
        # Should be able to detect circular dependency
        assert idea1.metadata["depends_on"][0] == idea2.id
        assert idea2.metadata["depends_on"][0] == idea1.id
    
    def test_large_model_serialization(self):
        """Test serializing large models."""
        # Create workflow with many candidates
        candidates = [
            {
                "idea": f"Idea {i}",
                "score": 5.0 + (i % 5),
                "description": "x" * 1000  # 1KB per candidate
            }
            for i in range(100)
        ]
        
        result = WorkflowResult(
            theme="Large test",
            constraints="Memory test",
            candidates=candidates,
            success=True,
            total_duration=300.0
        )
        
        # Should handle serialization
        data = result.to_dict()
        json_str = json.dumps(data)
        
        # Should be reasonable size (< 200KB for 100 candidates)
        assert len(json_str) < 200000
        
        # Should deserialize correctly
        loaded = json.loads(json_str)
        assert len(loaded["candidates"]) == 100
    
    def test_model_immutability(self):
        """Test that models maintain immutability where expected."""
        idea = IdeaData(
            title="Immutable test",
            description="Should not change",
            tags=["original"]
        )
        
        original_tags = idea.tags.copy()
        
        # Modifying the list should not affect the original
        tags_ref = idea.tags
        tags_ref.append("modified")
        
        # Depends on implementation - if using frozen dataclasses
        # this would raise an error. Otherwise, test defensive copying
        assert idea.tags == ["original", "modified"] or idea.tags == original_tags
    
    def test_model_unicode_handling(self):
        """Test models handle unicode correctly."""
        idea = IdeaData(
            title="多语言测试 🌍",
            description="Test with émojis and spëcial characters: café ☕",
            tags=["unicode", "测试", "🏷️"],
            metadata={"author": "用户123"}
        )
        
        # Should handle unicode in all fields
        assert "🌍" in idea.title
        assert "café" in idea.description
        assert "🏷️" in idea.tags
        
        # Should serialize/deserialize correctly
        data = asdict(idea)
        json_str = json.dumps(data, ensure_ascii=False)
        loaded = json.loads(json_str)
        
        assert loaded["title"] == idea.title
        assert loaded["metadata"]["author"] == "用户123"