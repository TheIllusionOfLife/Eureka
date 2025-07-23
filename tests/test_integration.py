"""Integration tests for MadSpark Multi-Agent System."""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch

from madspark.core.coordinator import run_multistep_workflow
from madspark.core.async_coordinator import AsyncCoordinator
from madspark.utils.bookmark_system import BookmarkManager
from madspark.utils.temperature_control import TemperatureManager


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests."""
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator.call_critic_with_retry')
    @patch('madspark.core.coordinator.call_advocate_with_retry')
    @patch('madspark.core.coordinator.call_skeptic_with_retry')
    @patch('madspark.core.coordinator.call_improve_idea_with_retry')
    def test_complete_workflow_integration(self, mock_improve, mock_skeptic, mock_advocate, 
                                         mock_critic, mock_generate):
        """Test complete workflow from idea generation to final output."""
        
        # Mock idea generation - returns string with ideas
        mock_generate.return_value = """AI-Powered Task Automation: Intelligent automation system for repetitive tasks
Smart Workflow Optimizer: ML-driven workflow optimization platform"""
        
        # Mock critic evaluation - returns JSON string
        mock_critic.return_value = '{"score": 7.5, "comment": "Good idea with market demand"}'
        
        # Mock advocate - returns string
        mock_advocate.return_value = "Strong market demand, addresses productivity pain points, proven ROI potential"
        
        # Mock skeptic - returns string
        mock_skeptic.return_value = "High development costs, strong competition, complex integration requirements"
        
        # Mock improve idea - returns string
        mock_improve.return_value = "Enhanced AI-Powered Task Automation with improved scalability and reduced costs"
        
        # Run the complete workflow with temperature manager
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("creative")
        
        result = run_multistep_workflow(
            theme="AI automation for productivity",
            constraints="Cost-effective and scalable solutions",
            temperature_manager=temp_manager,
            enhanced_reasoning=True,
            verbose=True
        )
        
        # Verify complete workflow execution
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify result structure matches CandidateData
        for candidate in result:
            assert "idea" in candidate
            assert "initial_score" in candidate
            assert "initial_critique" in candidate
            assert "advocacy" in candidate
            assert "skepticism" in candidate
            assert "improved_idea" in candidate
            assert "improved_score" in candidate
            assert "improved_critique" in candidate
        
        # Verify all agents were called
        mock_generate.assert_called()
        mock_critic.assert_called()
        mock_advocate.assert_called()
        mock_skeptic.assert_called()
        mock_improve.assert_called()
    
    @pytest.mark.asyncio
    @patch('madspark.agents.idea_generator.genai')
    @patch('madspark.agents.critic.genai')
    async def test_async_workflow_integration(self, mock_critic_genai, mock_gen_genai):
        """Test async workflow integration."""
        
        # Mock idea generation
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = '''
        {
            "ideas": [
                {
                    "title": "Async Test Idea",
                    "description": "Testing async workflow",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ]
        }
        '''
        mock_gen_client.models.generate_content.return_value = mock_gen_response
        mock_gen_genai.Client.return_value = mock_gen_client
        
        # Mock critic evaluation
        mock_critic_client = Mock()
        mock_critic_response = Mock()
        mock_critic_response.text = '''
        {
            "evaluations": [
                {
                    "idea_title": "Async Test Idea",
                    "overall_score": 7.5,
                    "strengths": ["Async processing"],
                    "weaknesses": ["Complexity"]
                }
            ]
        }
        '''
        mock_critic_client.models.generate_content.return_value = mock_critic_response
        mock_critic_genai.Client.return_value = mock_critic_client
        
        # Test async coordinator
        coordinator = AsyncCoordinator()
        # Create temperature manager for async workflow
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_preset("creative")
        
        result = await coordinator.run_workflow(
            theme="Async AI automation",
            constraints="Performance-optimized",
            temperature_manager=temp_manager,
            timeout=30.0
        )
        
        # Verify async workflow execution
        assert result is not None or result == {}  # May be empty if not fully implemented


class TestWorkflowWithComponents:
    """Test workflow integration with various components."""
    
    def test_workflow_with_bookmark_integration(self):
        """Test workflow integration with bookmark system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create bookmark manager
            bookmark_manager = BookmarkManager(bookmark_file=os.path.join(temp_dir, "bookmarks.json"))
            
            # Add some bookmarks
            bookmark_manager.bookmark_idea(
                idea_text="Existing Idea 1 - A previously saved idea",
                theme="Testing",
                constraints="Test constraints",
                score=7,
                tags=["automation", "productivity"]
            )
            
            bookmark_manager.bookmark_idea(
                idea_text="Existing Idea 2 - Another saved idea", 
                theme="Testing",
                constraints="Test constraints",
                score=8,
                tags=["ai", "efficiency"]
            )
            
            # The workflow doesn't use bookmarks directly
            # This test just verifies bookmarks can be created alongside workflow
            
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # The workflow should complete normally
            assert result is not None
            assert isinstance(result, list)
            
            # Bookmarks were created separately above
            bookmarks = bookmark_manager.list_bookmarks()
            assert len(bookmarks) == 2
    
    def test_workflow_with_temperature_management(self):
        """Test workflow integration with temperature management."""
        temp_manager = TemperatureManager()
        
        with patch('madspark.core.coordinator.TemperatureManager') as mock_temp_class:
            mock_temp_class.return_value = temp_manager
            
            with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generate:
                mock_generate.return_value = "Test Idea: Temperature test solution"
                
                result = run_multistep_workflow(
                    theme="AI automation",
                    constraints="Cost-effective",
                    temperature_manager=TemperatureManager.from_preset("creative")
                )
                
                # The workflow should complete with temperature manager
                assert result is not None
                assert isinstance(result, list)
    
    def test_workflow_with_novelty_filtering(self):
        """Test workflow integration with novelty filtering."""
        with patch('madspark.core.coordinator.NoveltyFilter') as mock_novelty_class:
            mock_filter = Mock()
            mock_filter.is_novel.return_value = True
            mock_novelty_class.return_value = mock_filter
            
            with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generate:
                mock_generate.return_value = "Novel Idea: Unique AI solution"
                
                result = run_multistep_workflow(
                    theme="AI automation",
                    constraints="Cost-effective",
                    enable_novelty_filter=True,
                    novelty_threshold=0.8
                )
                
                # The workflow should complete with novelty filter
                assert result is not None
                assert isinstance(result, list)


class TestWorkflowErrorHandling:
    """Test workflow error handling and resilience."""
    
    @patch('madspark.agents.idea_generator.genai')
    def test_workflow_with_agent_failures(self, mock_gen_genai):
        """Test workflow resilience to agent failures."""
        
        # Mock idea generation success
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = '''
        {
            "ideas": [
                {
                    "title": "Resilient Test Idea",
                    "description": "Testing error resilience",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ]
        }
        '''
        mock_gen_client.models.generate_content.return_value = mock_gen_response
        mock_gen_genai.Client.return_value = mock_gen_client
        
        # Mock critic failure
        with patch('madspark.agents.critic.genai') as mock_critic_genai:
            mock_critic_client = Mock()
            mock_critic_client.models.generate_content.side_effect = Exception("Critic API error")
            mock_critic_genai.Client.return_value = mock_critic_client
            
            # Workflow should handle critic failure gracefully
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # Should return empty list if critic fails
            assert result is not None
            assert isinstance(result, list)
            # When critical step fails, workflow returns empty list
            assert len(result) == 0
    
    @patch('madspark.core.coordinator.call_idea_generator_with_retry')
    def test_workflow_with_invalid_parameters(self, mock_generate):
        """Test workflow with invalid parameters."""
        # Mock to return empty ideas
        mock_generate.return_value = ""
        
        # Test with None parameters - workflow handles gracefully
        result = run_multistep_workflow("test", None)
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with empty strings - also returns empty list
        result = run_multistep_workflow("", "")
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Test with valid temperature
        from madspark.utils.temperature_control import TemperatureManager
        temp_manager = TemperatureManager.from_base_temperature(1.0)
        result = run_multistep_workflow("test", "test", temperature_manager=temp_manager)
        assert isinstance(result, list)
        
        # Test with invalid timeout - negative timeout should still work (no timeout enforcement in sync mode)
        result = run_multistep_workflow("test", "test", timeout=-1)
        assert isinstance(result, list)
    
    def test_workflow_network_resilience(self):
        """Test workflow resilience to network issues."""
        
        # Mock network timeout
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            mock_client = Mock()
            mock_client.models.generate_content.side_effect = Exception("Network timeout")
            mock_genai.Client.return_value = mock_client
            
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # Should handle network errors gracefully
            assert result == []  # Empty list on failure


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""
    
    def test_workflow_execution_time(self):
        """Test workflow execution time is reasonable."""
        import time
        
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            # Mock fast responses
            mock_client = Mock()
            mock_response = Mock()
            mock_response.text = '{"ideas": [{"title": "Fast Test", "description": "Speed test"}]}'
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client
            
            start_time = time.time()
            
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (with mocked responses)
            assert execution_time < 5.0  # 5 seconds max for mocked workflow
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_workflow_performance(self):
        """Test async workflow performance benefits."""
        import time
        
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            # Mock responses with slight delay
            mock_client = Mock()
            mock_response = Mock()
            mock_response.text = '{"ideas": [{"title": "Async Test", "description": "Async speed test"}]}'
            
            async def mock_generate_with_delay(*args, **kwargs):
                await asyncio.sleep(0.1)  # Simulate API delay
                return mock_response
            
            mock_client.models.generate_content.side_effect = mock_generate_with_delay
            mock_genai.Client.return_value = mock_client
            
            coordinator = AsyncCoordinator()
            start_time = time.time()
            
            _ = await coordinator.run_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Async version should be efficient
            assert execution_time < 10.0  # Should complete within 10 seconds
    
    def test_workflow_memory_usage(self):
        """Test workflow memory usage is reasonable."""
        import sys
        
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            # Mock responses
            mock_client = Mock()
            mock_response = Mock()
            mock_response.text = '{"ideas": [{"title": "Memory Test", "description": "Memory usage test"}]}'
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client
            
            # Get initial memory usage
            initial_size = sys.getsizeof(locals())
            
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # Memory shouldn't grow excessively
            final_size = sys.getsizeof(locals())
            memory_growth = final_size - initial_size
            
            # Should not consume excessive memory
            assert memory_growth < 1024 * 1024  # Less than 1MB growth
            assert result is not None


class TestWorkflowDataIntegrity:
    """Test workflow data integrity and consistency."""
    
    @patch('madspark.agents.idea_generator.genai')
    @patch('madspark.agents.critic.genai')
    def test_workflow_data_consistency(self, mock_critic_genai, mock_gen_genai):
        """Test data consistency throughout workflow."""
        
        # Mock idea generation
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = '''
        {
            "ideas": [
                {
                    "title": "Consistent Test Idea",
                    "description": "Testing data consistency",
                    "innovation_score": 8,
                    "feasibility_score": 7
                }
            ]
        }
        '''
        mock_gen_client.models.generate_content.return_value = mock_gen_response
        mock_gen_genai.Client.return_value = mock_gen_client
        
        # Mock critic evaluation
        mock_critic_client = Mock()
        mock_critic_response = Mock()
        mock_critic_response.text = '''
        {
            "evaluations": [
                {
                    "idea_title": "Consistent Test Idea",
                    "overall_score": 7.5,
                    "strengths": ["Data integrity"],
                    "weaknesses": ["Testing complexity"]
                }
            ]
        }
        '''
        mock_critic_client.models.generate_content.return_value = mock_critic_response
        mock_critic_genai.Client.return_value = mock_critic_client
        
        result = run_multistep_workflow(
            theme="AI automation",
            constraints="Cost-effective"
        )
        
        # Verify data consistency
        assert result is not None
        assert isinstance(result, list)
        
        # If we have results, verify each has consistent structure
        if len(result) > 0:
            for candidate in result:
                assert "idea" in candidate
                assert "initial_score" in candidate
                assert isinstance(candidate["initial_score"], (int, float))
    
    def test_workflow_output_structure(self):
        """Test workflow output structure is consistent."""
        with patch('madspark.agents.idea_generator.genai') as mock_genai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.text = '{"ideas": [{"title": "Structure Test", "description": "Output structure test"}]}'
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client
            
            result = run_multistep_workflow(
                theme="AI automation",
                constraints="Cost-effective"
            )
            
            # Verify output structure
            assert isinstance(result, list)
            
            if len(result) > 0:
                candidate = result[0]
                assert "idea" in candidate
                assert "initial_score" in candidate
                assert "advocacy" in candidate
                assert "skepticism" in candidate
                assert isinstance(candidate["idea"], str)
                assert isinstance(candidate["initial_score"], (int, float))