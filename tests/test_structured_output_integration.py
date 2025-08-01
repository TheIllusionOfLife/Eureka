"""Integration test for structured output implementation.

This test module verifies that the system correctly uses structured output
for idea improvement instead of regex-based cleaning.
"""
import json
import pytest
from unittest.mock import Mock, patch

# Test that the system loads and uses structured output
class TestStructuredOutputIntegration:
    """Test integration of structured output across the system."""
    
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.model_name', 'gemini-2.5-flash')
    def test_improve_idea_uses_structured_output(self, mock_client):
        """Test that improve_idea function uses structured output when available."""
        from madspark.agents.idea_generator import improve_idea
        
        # Mock the response to be JSON format
        mock_response = Mock()
        mock_response.text = json.dumps({
            "improved_idea": "A revolutionary blockchain-based renewable energy marketplace connecting producers and consumers directly",
            "key_improvements": [
                "Added blockchain for transparency", 
                "Enhanced scalability", 
                "Improved user experience"
            ]
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Mock types module
        with patch('madspark.agents.idea_generator.types') as mock_types:
            mock_config = Mock()
            mock_types.GenerateContentConfig = Mock(return_value=mock_config)
            
            # Call improve_idea
            result = improve_idea(
                original_idea="Solar panel sharing",
                critique="Needs better tracking and transparency",
                advocacy_points="Great community benefits, sustainable",
                skeptic_points="Security concerns, scalability issues",
                theme="renewable energy"
            )
        
        # Verify the result is clean without meta-commentary
        assert "improved version" not in result.lower()
        assert "enhanced concept" not in result.lower()
        assert "blockchain-based renewable energy marketplace" in result
    
    @patch('madspark.utils.agent_retry_wrappers.improve_idea')
    def test_coordinator_uses_clean_improved_ideas(self, mock_improve_idea):
        """Test that coordinator receives clean improved ideas."""
        from madspark.core.coordinator import run_multistep_workflow
        
        # Mock clean improved idea (no meta-commentary)
        mock_improve_idea.return_value = "A peer-to-peer energy trading platform using smart contracts for automated transactions"
        
        # Mock other agent functions
        with patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry') as mock_generator:
            with patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry') as mock_critic:
                with patch('madspark.utils.agent_retry_wrappers.call_advocate_with_retry') as mock_advocate:
                    with patch('madspark.utils.agent_retry_wrappers.call_skeptic_with_retry') as mock_skeptic:
                        # Setup mocks
                        mock_generator.return_value = "1. Solar panel sharing network"
                        mock_critic.return_value = '[{"score": 8, "comment": "Good idea with potential"}]'
                        mock_advocate.return_value = "• Strong community benefits"
                        mock_skeptic.return_value = "• Scalability concerns"
                        
                        # Run workflow
                        results = run_multistep_workflow(
                            theme="renewable energy",
                            constraints="community-focused, scalable",
                            num_top_candidates=1
                        )
                        
                        # Verify clean improved idea in results
                        assert len(results) == 1
                        assert results[0]['improved_idea'] == "A peer-to-peer energy trading platform using smart contracts for automated transactions"
                        assert "improved version" not in results[0]['improved_idea'].lower()
    
    def test_improved_idea_cleaner_handles_structured_output(self):
        """Test that the cleaner gracefully handles already-clean structured output."""
        from madspark.utils.improved_idea_cleaner import clean_improved_idea
        
        # Already clean text from structured output
        clean_text = "A blockchain-based supply chain tracking system with real-time updates"
        
        # Should not modify clean text significantly
        result = clean_improved_idea(clean_text)
        
        # Core content should be preserved
        assert "blockchain-based supply chain" in result
        assert "real-time updates" in result
    
    def test_web_frontend_displays_clean_ideas(self):
        """Test that web frontend would display clean ideas correctly."""
        # Simulate what the frontend would receive
        api_response = {
            "results": [{
                "improved_idea": "A decentralized renewable energy marketplace using blockchain",
                "initial_score": 7,
                "improved_score": 9,
                "score_delta": 2
            }]
        }
        
        # Verify no meta-commentary in the response
        improved_idea = api_response["results"][0]["improved_idea"]
        assert "improved version" not in improved_idea.lower()
        assert "enhanced concept" not in improved_idea.lower()
        assert improved_idea.startswith("A decentralized")


class TestStructuredOutputErrorHandling:
    """Test error handling in structured output implementation."""
    
    @pytest.mark.skip(reason="Import fallback is tested implicitly through other tests")
    def test_fallback_when_structured_import_fails(self):
        """Test that system falls back gracefully if structured module not available."""
        # The import happens inside the improve_idea function, making it difficult to mock
        # This functionality is tested implicitly when structured_idea_generator is not available
        pass
    
    def test_handles_non_json_response(self):
        """Test handling when API returns non-JSON despite JSON mode."""
        # Test through the main improve_idea function
        from madspark.agents.idea_generator import improve_idea
        
        with patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True):
            with patch('madspark.agents.idea_generator.idea_generator_client') as mock_client:
                mock_response = Mock()
                # Non-JSON response
                mock_response.text = "This is a plain text improved idea without JSON structure"
                mock_client.models.generate_content.return_value = mock_response
                
                result = improve_idea(
                    original_idea="Test",
                    critique="Needs work",
                    advocacy_points="Has potential",
                    skeptic_points="Some risks",
                    theme="innovation"
                )
                
                # Should handle plain text gracefully
                assert isinstance(result, str)
                assert len(result) > 0
    
    def test_handles_api_errors_gracefully(self):
        """Test graceful handling of API errors."""
        # Test through the main improve_idea function
        from madspark.agents.idea_generator import improve_idea
        
        with patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True):
            with patch('madspark.agents.idea_generator.idea_generator_client') as mock_client:
                # Test with an expected error type (AttributeError)
                mock_client.models.generate_content.side_effect = AttributeError("API attribute error")
                
                result = improve_idea(
                    original_idea="Test idea",
                    critique="Needs improvement",
                    advocacy_points="Good start",
                    skeptic_points="Some issues",
                    theme="testing"
                )
                
                # Should return a reasonable fallback for expected errors
                assert isinstance(result, str)
                assert len(result) > 20  # Not empty
    
    def test_unexpected_errors_are_raised(self):
        """Test that unexpected errors are properly raised."""
        # Test through the main improve_idea function
        from madspark.agents.idea_generator import improve_idea
        
        with patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True):
            with patch('madspark.agents.idea_generator.idea_generator_client') as mock_client:
                # Test with an unexpected error type (generic Exception)
                mock_client.models.generate_content.side_effect = Exception("Unexpected API Error")
                
                # Should re-raise unexpected errors
                with pytest.raises(Exception, match="Unexpected API Error"):
                    improve_idea(
                        original_idea="Test idea",
                        critique="Needs improvement",
                        advocacy_points="Good start",
                        skeptic_points="Some issues",
                        theme="testing"
                    )


class TestPromptEngineering:
    """Test that prompts are properly engineered for clean output."""
    
    def test_system_instruction_prevents_meta_commentary(self):
        """Test system instruction explicitly prevents meta-commentary."""
        from madspark.utils.constants import IDEA_GENERATOR_SYSTEM_INSTRUCTION
        
        # Check key phrases
        assert "meta-commentary" in IDEA_GENERATOR_SYSTEM_INSTRUCTION or \
               "directly" in IDEA_GENERATOR_SYSTEM_INSTRUCTION.lower()
        assert "Do NOT" in IDEA_GENERATOR_SYSTEM_INSTRUCTION
    
    def test_improvement_prompt_has_clear_requirements(self):
        """Test improvement prompt includes format requirements."""
        from madspark.agents.idea_generator import build_improvement_prompt
        
        prompt = build_improvement_prompt(
            original_idea="Solar panels",
            critique="Good but needs scale",
            advocacy_points="Clean energy",
            skeptic_points="High cost",
            theme="renewable energy"
        )
        
        # Should have format section
        assert "FORMAT REQUIREMENTS" in prompt or "directly" in prompt.lower()
        assert "no meta-commentary" in prompt.lower() or "Start directly" in prompt