"""Comprehensive test suite to establish baseline before refactoring.

This test suite captures the current behavior of the system to ensure
refactoring doesn't break existing functionality.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from coordinator import run_multistep_workflow, EvaluatedIdea, CandidateData
from temperature_control import TemperatureManager, TemperatureConfig
from novelty_filter import NoveltyFilter
from bookmark_system import BookmarkManager
from improved_idea_cleaner import clean_improved_idea
from utils import parse_json_with_fallback, exponential_backoff_retry
from constants import (
    DEFAULT_IDEA_TEMPERATURE,
    DEFAULT_EVALUATION_TEMPERATURE,
    DEFAULT_ADVOCACY_TEMPERATURE,
    DEFAULT_SKEPTICISM_TEMPERATURE
)

# Import agent modules for mocking
import agent_defs.idea_generator as idea_gen
import agent_defs.critic as critic
import agent_defs.advocate as advocate
import agent_defs.skeptic as skeptic


class TestCoreWorkflow:
    """Test the core multi-agent workflow."""
    
    @patch('agent_defs.idea_generator.generate_ideas')
    @patch('agent_defs.critic.evaluate_ideas')
    @patch('agent_defs.advocate.advocate_idea')
    @patch('agent_defs.skeptic.criticize_idea')
    @patch('agent_defs.idea_generator.improve_idea')
    def test_basic_workflow(self, mock_improve, mock_criticize, mock_advocate, mock_evaluate, mock_generate):
        """Test basic workflow execution with mocked agents."""
        # Setup mocks
        mock_generate.return_value = "1. Test idea one\n2. Test idea two"
        mock_evaluate.return_value = '{"score": 7.5, "critique": "Good idea"}\n{"score": 6.0, "critique": "Average idea"}'
        mock_advocate.return_value = "STRENGTHS:\n• Great potential\n• Easy to implement"
        mock_criticize.return_value = "CRITICAL FLAWS:\n• May not scale\n• Limited market"
        mock_improve.return_value = "Improved test idea with addressed concerns"
        
        # Run workflow
        results = run_multistep_workflow(
            theme="Test theme",
            constraints="Test constraints",
            num_top_candidates=1
        )
        
        # Assertions
        assert len(results) == 1
        assert isinstance(results[0], dict)
        assert results[0]['initial_score'] == 7.5
        assert results[0]['initial_critique'] == "Good idea"
        assert "Great potential" in results[0]['advocacy']
        assert "May not scale" in results[0]['skepticism']
        assert "Improved test idea" in results[0]['improved_idea']
        
    def test_temperature_manager_integration(self):
        """Test temperature manager integration with workflow."""
        temp_manager = TemperatureManager.from_base_temperature(0.8)
        
        with patch('agent_defs.idea_generator.generate_ideas') as mock_gen:
            mock_gen.return_value = "1. Test idea"
            
            with patch('agent_defs.critic.evaluate_ideas') as mock_eval:
                mock_eval.return_value = '{"score": 5.0, "critique": "Ok"}'
                
                run_multistep_workflow(
                    theme="Test",
                    constraints="Test",
                    num_top_candidates=1,
                    temperature_manager=temp_manager
                )
                
                # Verify temperatures were used correctly
                idea_temp = temp_manager.get_temperature_for_stage('idea_generation')
                assert mock_gen.call_args[1]['temperature'] == idea_temp


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_parse_json_with_fallback_valid(self):
        """Test JSON parsing with valid input."""
        valid_json = '{"score": 8.5, "critique": "Excellent"}'
        result = parse_json_with_fallback(valid_json, 1)
        assert len(result) == 1
        assert result[0]['score'] == 8.5
        assert result[0]['critique'] == "Excellent"
        
    def test_parse_json_with_fallback_invalid(self):
        """Test JSON parsing with invalid input."""
        invalid_json = 'Not a JSON'
        result = parse_json_with_fallback(invalid_json, 1)
        assert len(result) == 1
        assert result[0]['score'] == 0  # Default fallback
        assert 'comment' in result[0]
        
    def test_exponential_backoff_retry(self):
        """Test retry decorator."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=2, initial_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "Success"
        
        result = flaky_function()
        assert result == "Success"
        assert call_count == 2


class TestTemperatureControl:
    """Test temperature control system."""
    
    def test_temperature_presets(self):
        """Test all temperature presets."""
        for preset_name in TemperatureManager.PRESETS.keys():
            manager = TemperatureManager.from_preset(preset_name)
            expected_config = TemperatureManager.PRESETS[preset_name]
            assert manager.config.base_temperature == expected_config.base_temperature
            
    def test_stage_specific_temperatures(self):
        """Test stage-specific temperature calculations."""
        manager = TemperatureManager.from_base_temperature(0.7)
        
        # Test stage multipliers
        idea_temp = manager.get_temperature_for_stage('idea_generation')
        eval_temp = manager.get_temperature_for_stage('evaluation')
        
        assert idea_temp > eval_temp  # Ideas should be more creative
        assert idea_temp == min(1.0, 0.7 * 1.3)  # Idea multiplier with cap
        assert eval_temp == max(0.1, 0.7 * 0.4)  # Eval multiplier with floor


class TestNoveltyFilter:
    """Test novelty filtering system."""
    
    def test_duplicate_detection(self):
        """Test exact duplicate detection."""
        filter = NoveltyFilter(threshold=0.8)
        ideas = [
            "AI healthcare assistant",
            "AI healthcare assistant",  # Duplicate
            "Smart home system"
        ]
        
        novel_ideas = filter.filter_novel_ideas(ideas)
        assert len(novel_ideas) == 2
        assert "Smart home system" in novel_ideas
        
    def test_similarity_detection(self):
        """Test similar idea detection."""
        filter = NoveltyFilter(threshold=0.8)
        ideas = [
            "AI-powered healthcare assistant for elderly",
            "AI healthcare helper for seniors",  # Similar
            "Blockchain voting system"
        ]
        
        novel_ideas = filter.filter_novel_ideas(ideas)
        assert len(novel_ideas) == 2
        assert "Blockchain voting system" in novel_ideas


class TestBookmarkSystem:
    """Test bookmark functionality."""
    
    def test_bookmark_operations(self):
        """Test bookmark CRUD operations."""
        # Use temporary file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
            
        try:
            bookmarks = BookmarkManager(temp_file)
            
            # Test add
            bookmark_id = bookmarks.bookmark_idea(
                idea="Test idea",
                score=7.5,
                tags=["test", "demo"]
            )
            assert bookmark_id is not None
            
            # Test list
            all_bookmarks = bookmarks.list_bookmarks()
            assert len(all_bookmarks) == 1
            assert all_bookmarks[0].idea == "Test idea"
            
            # Test search
            results = bookmarks.search_bookmarks("Test")
            assert len(results) == 1
            
            # Test filter by tag
            tagged = bookmarks.list_bookmarks(tags=["test"])
            assert len(tagged) == 1
            
        finally:
            # Cleanup
            Path(temp_file).unlink(missing_ok=True)


class TestIdeaCleaner:
    """Test idea cleaning functionality."""
    
    def test_meta_header_removal(self):
        """Test removal of meta headers."""
        text = """ENHANCED CONCEPT: Test Framework
ORIGINAL THEME: Testing
Some actual content here."""
        
        cleaned = clean_improved_idea(text)
        assert "ENHANCED CONCEPT" not in cleaned
        assert "ORIGINAL THEME" not in cleaned
        assert "Some actual content here." in cleaned
        
    def test_improvement_language_removal(self):
        """Test removal of improvement references."""
        text = "Our enhanced approach improves the system."
        cleaned = clean_improved_idea(text)
        assert "enhanced" not in cleaned
        assert "This approach" in cleaned
        
    def test_score_removal(self):
        """Test removal of score references."""
        text = "Great idea (Score: 8.5) that works well."
        cleaned = clean_improved_idea(text)
        assert "Score" not in cleaned
        assert "8.5" not in cleaned
        assert "Great idea  that works well." in cleaned


class TestFeedbackLoop:
    """Test feedback loop enhancement."""
    
    @patch('agent_defs.idea_generator.generate_ideas')
    @patch('agent_defs.critic.evaluate_ideas')
    @patch('agent_defs.advocate.advocate_idea')
    @patch('agent_defs.skeptic.criticize_idea')
    @patch('agent_defs.idea_generator.improve_idea')
    def test_idea_improvement(self, mock_improve, mock_criticize, mock_advocate, mock_evaluate, mock_generate):
        """Test that ideas are improved based on feedback."""
        # Setup
        mock_generate.return_value = "1. Original idea"
        mock_evaluate.side_effect = [
            '{"score": 6.0, "critique": "Has potential"}',  # Initial
            '{"score": 8.5, "critique": "Much better"}'      # After improvement
        ]
        mock_advocate.return_value = "STRENGTHS:\n• Good foundation"
        mock_criticize.return_value = "CRITICAL FLAWS:\n• Needs refinement"
        mock_improve.return_value = "Refined idea addressing concerns"
        
        # Run
        results = run_multistep_workflow(
            theme="Test",
            constraints="Test",
            num_top_candidates=1
        )
        
        # Verify improvement
        assert results[0]['initial_score'] == 6.0
        assert results[0]['improved_score'] == 8.5
        assert results[0]['score_delta'] == 2.5
        assert mock_improve.called
        
        # Verify feedback was passed to improve_idea
        improve_call_args = mock_improve.call_args[0]
        assert "Good foundation" in improve_call_args[3]  # advocacy
        assert "Needs refinement" in improve_call_args[4]  # skepticism


class TestAsyncSupport:
    """Test async coordinator functionality."""
    
    @pytest.mark.asyncio
    async def test_async_workflow_basic(self):
        """Test basic async workflow execution."""
        from async_coordinator import AsyncCoordinator
        
        coordinator = AsyncCoordinator(max_concurrent_agents=2)
        
        with patch('async_coordinator.generate_ideas_with_retry') as mock_gen:
            mock_gen.return_value = "1. Async test idea"
            
            with patch('async_coordinator.evaluate_ideas_with_retry') as mock_eval:
                mock_eval.return_value = '{"score": 7.0, "critique": "Good"}'
                
                with patch('async_coordinator.advocate_idea_with_retry') as mock_adv:
                    mock_adv.return_value = "STRENGTHS:\n• Fast"
                    
                    with patch('async_coordinator.criticize_idea_with_retry') as mock_crit:
                        mock_crit.return_value = "FLAWS:\n• Complex"
                        
                        with patch('async_coordinator.improve_idea_with_retry') as mock_imp:
                            mock_imp.return_value = "Improved async idea"
                            
                            results = await coordinator.run_workflow(
                                theme="Async test",
                                constraints="Fast",
                                num_top_candidates=1
                            )
                            
                            assert len(results) == 1
                            assert results[0]['initial_score'] == 7.0


class TestConstants:
    """Test constants and configuration."""
    
    def test_temperature_constants(self):
        """Test temperature constants are valid."""
        assert 0 < DEFAULT_IDEA_TEMPERATURE <= 2.0
        assert 0 < DEFAULT_EVALUATION_TEMPERATURE <= 2.0
        assert 0 < DEFAULT_ADVOCACY_TEMPERATURE <= 2.0
        assert 0 < DEFAULT_SKEPTICISM_TEMPERATURE <= 2.0
        
    def test_all_presets_defined(self):
        """Test all temperature presets are properly defined."""
        required_attributes = ['base_temperature', 'idea_generation', 'evaluation', 'advocacy', 'skepticism']
        for preset_name, preset_config in TemperatureManager.PRESETS.items():
            for attr in required_attributes:
                assert hasattr(preset_config, attr)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])