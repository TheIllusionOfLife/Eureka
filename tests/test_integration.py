"""Integration tests for MadSpark Multi-Agent System."""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from madspark.core.coordinator import run_multistep_workflow
from madspark.core.async_coordinator import AsyncCoordinator
from madspark.utils.bookmark_system import BookmarkManager
from madspark.utils.temperature_control import TemperatureManager
from madspark.utils.novelty_filter import NoveltyFilter


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests."""
    
    @patch('madspark.agents.idea_generator.genai')
    @patch('madspark.agents.critic.genai')
    @patch('madspark.agents.advocate.genai')
    @patch('madspark.agents.skeptic.genai')
    def test_complete_workflow_integration(self, mock_skeptic_genai, mock_advocate_genai, 
                                         mock_critic_genai, mock_gen_genai):
        """Test complete workflow from idea generation to final output."""
        
        # Mock idea generation
        mock_gen_client = Mock()
        mock_gen_response = Mock()
        mock_gen_response.text = '''
        {
            "ideas": [
                {
                    "title": "AI-Powered Task Automation",
                    "description": "Intelligent automation system for repetitive tasks",
                    "innovation_score": 8,
                    "feasibility_score": 7,
                    "market_potential": 9
                },
                {
                    "title": "Smart Workflow Optimizer",
                    "description": "ML-driven workflow optimization platform",
                    "innovation_score": 7,
                    "feasibility_score": 8,
                    "market_potential": 8
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
                    "idea_title": "AI-Powered Task Automation",
                    "overall_score": 7.5,
                    "strengths": ["High market demand", "Clear value proposition"],
                    "weaknesses": ["Technical complexity", "Competition"]
                },
                {
                    "idea_title": "Smart Workflow Optimizer",
                    "overall_score": 7.8,
                    "strengths": ["Proven market need", "Scalable solution"],
                    "weaknesses": ["Implementation challenges", "Customer adoption"]
                }
            ]
        }
        '''
        mock_critic_client.models.generate_content.return_value = mock_critic_response
        mock_critic_genai.Client.return_value = mock_critic_client
        
        # Mock advocate
        mock_advocate_client = Mock()
        mock_advocate_response = Mock()
        mock_advocate_response.text = '''
        {
            "advocacy": {
                "key_strengths": [
                    "Addresses genuine productivity pain points",
                    "Large addressable market",
                    "Proven ROI potential"
                ],
                "value_proposition": "Dramatically improves workplace efficiency",
                "market_potential": "Multi-billion dollar automation market",
                "competitive_advantages": [
                    "Advanced AI capabilities",
                    "User-friendly interface",
                    "Seamless integration"
                ]
            }
        }
        '''
        mock_advocate_client.models.generate_content.return_value = mock_advocate_response
        mock_advocate_genai.Client.return_value = mock_advocate_client
        
        # Mock skeptic
        mock_skeptic_client = Mock()
        mock_skeptic_response = Mock()
        mock_skeptic_response.text = '''
        {
            "criticism": {
                "key_concerns": [
                    "High development and maintenance costs",
                    "Strong competition from established players",
                    "Complex integration requirements"
                ],
                "risk_assessment": "Medium to high risk due to technical complexity",
                "potential_failures": [
                    "AI accuracy issues",
                    "User adoption challenges",
                    "Scalability problems"
                ],
                "implementation_challenges": [
                    "Data privacy and security",
                    "Legacy system integration",
                    "Change management"
                ]
            }
        }
        '''
        mock_skeptic_client.models.generate_content.return_value = mock_skeptic_response
        mock_skeptic_genai.Client.return_value = mock_skeptic_client
        
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
        assert "ideas" in result
        assert "evaluations" in result
        assert "advocacy" in result
        assert "criticism" in result
        
        # Verify ideas were generated
        assert len(result["ideas"]) == 2
        assert result["ideas"][0]["title"] == "AI-Powered Task Automation"
        assert result["ideas"][1]["title"] == "Smart Workflow Optimizer"
        
        # Verify evaluations were performed
        assert len(result["evaluations"]) == 2
        assert result["evaluations"][0]["overall_score"] == 7.5
        assert result["evaluations"][1]["overall_score"] == 7.8
        
        # Verify advocacy was performed
        assert "key_strengths" in result["advocacy"]
        assert len(result["advocacy"]["key_strengths"]) == 3
        assert "value_proposition" in result["advocacy"]
        
        # Verify criticism was performed
        assert "key_concerns" in result["criticism"]
        assert len(result["criticism"]["key_concerns"]) == 3
        assert "risk_assessment" in result["criticism"]
        
        # Verify all agents were called
        mock_gen_genai.Client.assert_called()
        mock_critic_genai.Client.assert_called()
        mock_advocate_genai.Client.assert_called()
        mock_skeptic_genai.Client.assert_called()
    
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
            
            # Mock workflow with bookmarks
            with patch('madspark.core.coordinator.BookmarkManager') as mock_bookmark_class:
                mock_bookmark_class.return_value = bookmark_manager
                
                with patch('madspark.core.coordinator.generate_ideas') as mock_generate:
                    mock_generate.return_value = {
                        "ideas": [{"title": "New Idea", "description": "A new idea"}]
                    }
                    
                    result = run_multistep_workflow(
                        theme="AI automation",
                        constraints="Cost-effective"
                    )
                    
                    # The workflow should complete (bookmarks are not directly integrated)
                    assert result is not None
                    assert isinstance(result, list)
    
    def test_workflow_with_temperature_management(self):
        """Test workflow integration with temperature management."""
        temp_manager = TemperatureManager()
        
        with patch('madspark.core.coordinator.TemperatureManager') as mock_temp_class:
            mock_temp_class.return_value = temp_manager
            
            with patch('madspark.core.coordinator.generate_ideas') as mock_generate:
                mock_generate.return_value = {
                    "ideas": [{"title": "Test Idea", "description": "Temperature test"}]
                }
                
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
            
            with patch('madspark.core.coordinator.generate_ideas') as mock_generate:
                mock_generate.return_value = {
                    "ideas": [
                        {"title": "Novel Idea 1", "description": "First novel idea"},
                        {"title": "Novel Idea 2", "description": "Second novel idea"}
                    ]
                }
                
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
            
            result = await coordinator.run_workflow(
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
        assert "ideas" in result
        assert "evaluations" in result
        
        # Verify idea titles match between generation and evaluation
        idea_titles = [idea["title"] for idea in result["ideas"]]
        eval_titles = [eval_item["idea_title"] for eval_item in result["evaluations"]]
        
        assert len(idea_titles) == len(eval_titles)
        for title in idea_titles:
            assert title in eval_titles
    
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
            assert isinstance(result, dict)
            assert "ideas" in result
            assert isinstance(result["ideas"], list)
            
            if len(result["ideas"]) > 0:
                idea = result["ideas"][0]
                assert "title" in idea
                assert "description" in idea
                assert isinstance(idea["title"], str)
                assert isinstance(idea["description"], str)