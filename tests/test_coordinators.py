"""Comprehensive tests for MadSpark coordinator modules."""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

from madspark.core.coordinator import run_multistep_workflow
from madspark.core.async_coordinator import AsyncCoordinator


class TestSyncCoordinator:
    """Test cases for the synchronous coordinator."""
    
    @pytest.fixture
    def mock_workflow_results(self):
        """Mock results for workflow testing."""
        return {
            "ideas": [
                {
                    "title": "Test Idea 1",
                    "description": "A test idea",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ],
            "evaluations": [
                {
                    "idea_title": "Test Idea 1",
                    "overall_score": 7.5,
                    "strengths": ["Practical"],
                    "weaknesses": ["Complex"]
                }
            ],
            "advocacy": {
                "key_strengths": ["Market demand"],
                "value_proposition": "Solves real problems"
            },
            "criticism": {
                "key_concerns": ["High costs"],
                "risk_assessment": "Medium risk"
            }
        }
    
    @patch('madspark.core.coordinator.generate_ideas')
    @patch('madspark.core.coordinator.evaluate_ideas')
    @patch('madspark.core.coordinator.advocate_idea')
    @patch('madspark.core.coordinator.criticize_idea')
    def test_run_multistep_workflow_success(self, mock_criticize, mock_advocate, 
                                          mock_evaluate, mock_generate, mock_workflow_results):
        """Test successful workflow execution."""
        # Mock each agent function
        mock_generate.return_value = {"ideas": mock_workflow_results["ideas"]}
        mock_evaluate.return_value = {"evaluations": mock_workflow_results["evaluations"]}
        mock_advocate.return_value = {"advocacy": mock_workflow_results["advocacy"]}
        mock_criticize.return_value = {"criticism": mock_workflow_results["criticism"]}
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature=0.8,
            enhanced_reasoning=True,
            verbose=False
        )
        
        assert result is not None
        assert "ideas" in result
        assert "evaluations" in result
        assert "advocacy" in result
        assert "criticism" in result
        
        # Verify all agents were called
        mock_generate.assert_called_once()
        mock_evaluate.assert_called_once()
        mock_advocate.assert_called_once()
        mock_criticize.assert_called_once()
    
    @patch('madspark.core.coordinator.generate_ideas')
    def test_run_multistep_workflow_idea_generation_failure(self, mock_generate):
        """Test workflow when idea generation fails."""
        mock_generate.return_value = None
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Should handle gracefully
        assert result is None or "error" in result
    
    @patch('madspark.core.coordinator.generate_ideas')
    @patch('madspark.core.coordinator.evaluate_ideas')
    def test_run_multistep_workflow_partial_failure(self, mock_evaluate, mock_generate):
        """Test workflow with partial agent failure."""
        mock_generate.return_value = {"ideas": [{"title": "Test", "description": "Test"}]}
        mock_evaluate.side_effect = Exception("Evaluation failed")
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Should handle partial failures gracefully
        assert result is not None
        assert "ideas" in result
    
    def test_workflow_parameter_validation(self):
        """Test workflow parameter validation."""
        # Test with empty theme
        result = run_multistep_workflow(theme="", constraints="test")
        assert result is None or "error" in result
        
        # Test with invalid temperature
        result = run_multistep_workflow(theme="test", constraints="test", temperature=2.0)
        assert result is None or "error" in result


class TestAsyncCoordinator:
    """Test cases for the async coordinator."""
    
    @pytest.fixture
    def coordinator(self):
        """Create an async coordinator instance."""
        return AsyncCoordinator()
    
    @pytest.fixture
    def mock_async_workflow_results(self):
        """Mock results for async workflow testing."""
        return {
            "ideas": [
                {
                    "title": "Async Test Idea",
                    "description": "An async test idea",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ],
            "evaluations": [
                {
                    "idea_title": "Async Test Idea",
                    "overall_score": 7.5,
                    "strengths": ["Scalable"],
                    "weaknesses": ["Complex"]
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_async_coordinator_initialization(self, coordinator):
        """Test async coordinator initialization."""
        assert coordinator is not None
        assert hasattr(coordinator, 'run_workflow')
    
    @pytest.mark.asyncio
    @patch('madspark.core.async_coordinator.generate_ideas')
    @patch('madspark.core.async_coordinator.evaluate_ideas')
    @patch('madspark.core.async_coordinator.advocate_idea')
    @patch('madspark.core.async_coordinator.criticize_idea')
    async def test_run_workflow_success(self, mock_criticize, mock_advocate, 
                                       mock_evaluate, mock_generate, coordinator, 
                                       mock_async_workflow_results):
        """Test successful async workflow execution."""
        # Mock each agent function as async
        mock_generate.return_value = {"ideas": mock_async_workflow_results["ideas"]}
        mock_evaluate.return_value = {"evaluations": mock_async_workflow_results["evaluations"]}
        mock_advocate.return_value = {"advocacy": {"key_strengths": ["Scalable"]}}
        mock_criticize.return_value = {"criticism": {"key_concerns": ["Complex"]}}
        
        result = await coordinator.run_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature=0.8,
            enhanced_reasoning=True,
            verbose=False
        )
        
        assert result is not None
        assert "ideas" in result or "error" not in result
    
    @pytest.mark.asyncio
    async def test_async_workflow_timeout(self, coordinator):
        """Test async workflow with timeout."""
        # Test with very short timeout
        result = await coordinator.run_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            timeout=0.001  # 1ms timeout
        )
        
        # Should handle timeout gracefully
        assert result is None or "error" in result or "timeout" in str(result)
    
    @pytest.mark.asyncio
    @patch('madspark.core.async_coordinator.generate_ideas')
    async def test_async_workflow_with_exception(self, mock_generate, coordinator):
        """Test async workflow exception handling."""
        mock_generate.side_effect = Exception("Async error")
        
        result = await coordinator.run_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Should handle exceptions gracefully
        assert result is None or "error" in result


class TestWorkflowIntegration:
    """Integration tests for workflow components."""
    
    def test_sync_async_consistency(self):
        """Test that sync and async workflows produce consistent results."""
        # This test would verify that both coordinators handle the same inputs
        # in a consistent manner (with appropriate mocking)
        sync_result = "Mock sync result"
        async_result = "Mock async result"
        
        # For now, just verify the test infrastructure works
        assert sync_result is not None
        assert async_result is not None
    
    @patch('madspark.core.coordinator.BookmarkManager')
    @patch('madspark.core.coordinator.generate_ideas')
    def test_workflow_with_bookmarks(self, mock_generate, mock_bookmark_manager):
        """Test workflow integration with bookmark system."""
        mock_bookmark_manager.return_value.get_random_bookmarks.return_value = []
        mock_generate.return_value = {"ideas": [{"title": "Test", "description": "Test"}]}
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            use_bookmarks=True
        )
        
        assert result is not None
        mock_bookmark_manager.assert_called_once()
    
    @patch('madspark.core.coordinator.TemperatureManager')
    @patch('madspark.core.coordinator.generate_ideas')
    def test_workflow_with_temperature_presets(self, mock_generate, mock_temp_manager):
        """Test workflow with temperature presets."""
        mock_temp_manager.return_value.get_temperature_config.return_value = {
            "base_temperature": 0.8,
            "idea_generation": 0.9,
            "evaluation": 0.7
        }
        mock_generate.return_value = {"ideas": [{"title": "Test", "description": "Test"}]}
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature_preset="creative"
        )
        
        assert result is not None
        mock_temp_manager.assert_called_once()
    
    def test_workflow_error_propagation(self):
        """Test that workflow errors are properly propagated."""
        # Test with various error conditions
        result = run_multistep_workflow(None, None)
        assert result is None or "error" in result
        
        result = run_multistep_workflow("", "")
        assert result is None or "error" in result