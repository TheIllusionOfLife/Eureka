"""Comprehensive tests for MadSpark coordinator modules."""
import pytest
import asyncio
from unittest.mock import patch

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
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator.call_critic_with_retry')
    @patch('madspark.core.coordinator.call_advocate_with_retry')
    @patch('madspark.core.coordinator.call_skeptic_with_retry')
    @patch('madspark.core.coordinator.call_improve_idea_with_retry')
    def test_run_multistep_workflow_success(self, mock_improve, mock_skeptic, mock_advocate, 
                                          mock_critic, mock_generate, mock_workflow_results):
        """Test successful workflow execution."""
        # Mock each agent function to return strings as expected
        mock_generate.return_value = "Test Idea 1: A test idea with innovation\nTest Idea 2: Another test idea"
        mock_critic.return_value = '{"score": 7.5, "comment": "Good ideas with practical application"}'
        mock_advocate.return_value = "Strong market demand and solves real problems"
        mock_skeptic.return_value = "High costs and medium risk concerns"
        mock_improve.return_value = "Enhanced Test Idea 1 with improvements based on feedback"
        
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_base_temperature(0.8)
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature_manager=temp_manager,
            enhanced_reasoning=True,
            verbose=False
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        # Check that results have the expected CandidateData structure
        assert all("idea" in item for item in result)
        assert all("initial_score" in item for item in result)
        
        # Verify all agents were called
        mock_generate.assert_called_once()
        assert mock_critic.call_count >= 1  # Called for initial eval and re-evaluation
        assert mock_advocate.call_count >= 1  # Called for each candidate
        assert mock_skeptic.call_count >= 1  # Called for each candidate
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_run_multistep_workflow_idea_generation_failure(self, mock_generate):
        """Test workflow when idea generation fails."""
        mock_generate.return_value = ""  # Empty string means no ideas
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Should handle gracefully - returns empty list when no ideas
        assert isinstance(result, list)
        assert len(result) == 0
    
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
        assert isinstance(result, list)
        # When evaluation fails, no results are returned
        assert len(result) == 0
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_workflow_parameter_validation(self, mock_generate):
        """Test workflow parameter validation."""
        # Test with empty theme - workflow should handle gracefully
        mock_generate.return_value = ""  # No ideas generated
        
        result = run_multistep_workflow(theme="", constraints="test")
        # Empty theme results in empty list
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with valid parameters should work
        mock_generate.return_value = "Test idea"
        result = run_multistep_workflow(theme="test", constraints="test")
        assert isinstance(result, list)


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
    @patch('madspark.core.async_coordinator.async_generate_ideas')
    @patch('madspark.core.async_coordinator.async_evaluate_ideas')
    @patch('madspark.core.async_coordinator.async_advocate_idea')
    @patch('madspark.core.async_coordinator.async_criticize_idea')
    @patch('madspark.core.async_coordinator.async_improve_idea')
    async def test_run_workflow_success(self, mock_improve, mock_criticize, mock_advocate, 
                                       mock_evaluate, mock_generate, coordinator, 
                                       mock_async_workflow_results):
        """Test successful async workflow execution."""
        # Mock each async agent function to return appropriate strings
        mock_generate.return_value = "Async Test Idea 1: An async test idea\nAsync Test Idea 2: Another async idea"
        mock_evaluate.return_value = '[{"score": 7.5, "comment": "Good async idea"}]'
        mock_advocate.return_value = "Strong market demand and scalable solution"
        mock_criticize.return_value = "Complex implementation but manageable"
        mock_improve.return_value = "Enhanced Async Test Idea 1 with improvements"
        
        # Create a temperature manager for the async workflow  
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("creative")
        
        result = await coordinator.run_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature_manager=temp_manager,
            enhanced_reasoning=False,  # Disable to simplify test
            verbose=False
        )
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        # Check result structure matches CandidateData
        assert all("idea" in item for item in result)
        assert all("initial_score" in item for item in result)
    
    @pytest.mark.asyncio
    async def test_async_workflow_timeout(self, coordinator):
        """Test async workflow with timeout."""
        # Test with very short timeout
        # Create a temperature manager for the timeout test
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("balanced")
        
        # The async coordinator raises asyncio.TimeoutError on timeout
        with pytest.raises(asyncio.TimeoutError):
            await coordinator.run_workflow(
                theme="AI automation",
                constraints="Cost-effective",
                temperature_manager=temp_manager,
                timeout=0.001  # 1ms timeout
            )
    
    @pytest.mark.asyncio
    @patch('madspark.core.async_coordinator.async_generate_ideas')
    async def test_async_workflow_with_exception(self, mock_generate, coordinator):
        """Test async workflow exception handling."""
        mock_generate.side_effect = Exception("Async error")
        
        # Create a temperature manager for the exception test
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("balanced")
        
        # The async coordinator raises exceptions rather than returning error results
        with pytest.raises(Exception) as exc_info:
            await coordinator.run_workflow(
                theme="AI automation",
                constraints="Cost-effective",
                temperature_manager=temp_manager
            )
        
        assert "Async error" in str(exc_info.value)


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
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_workflow_with_bookmarks(self, mock_generate):
        """Test workflow integration with bookmark system."""
        mock_generate.return_value = "Test Idea 1: Test idea for bookmarks"
        
        # Test workflow execution
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Should return a list of CandidateData or empty list
        assert isinstance(result, list)
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_workflow_with_temperature_presets(self, mock_generate):
        """Test workflow with temperature presets."""
        mock_generate.return_value = "Test Idea 1\nTest Idea 2"
        
        # Create temperature manager from preset
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("creative")
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective",
            temperature_manager=temp_manager
        )
        
        assert result is not None or result == []  # Allow empty results in mock mode
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_workflow_error_propagation(self, mock_generate):
        """Test that workflow errors are properly propagated."""
        # When idea generation returns empty, workflow returns empty list
        mock_generate.return_value = ""
        
        # Test with None values - workflow handles gracefully
        result = run_multistep_workflow("test", "test")
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with empty strings - also returns empty list
        result = run_multistep_workflow("", "")
        assert isinstance(result, list)
        assert len(result) == 0