"""Tests for removing manual formatting from prompts.

This test suite ensures that:
1. Prompts use structured output instead of manual formatting
2. Parsing logic is removed in favor of structured responses
3. Error handling is more robust with structured output
4. Legacy parsing is still supported for backward compatibility
"""
import json
import pytest
from unittest.mock import Mock, patch


class TestStructuredIdeaGeneration:
    """Test that idea generation uses structured output."""
    
    def test_idea_generator_uses_structured_output(self):
        """Test that idea generator requests structured output format."""
        from src.madspark.agents.idea_generator import generate_ideas
        
        with patch('src.madspark.agents.idea_generator.idea_generator_client') as mock_client:
            # Mock structured response
            mock_response = Mock()
            mock_response.text = json.dumps({
                "ideas": [
                    {"idea_number": 1, "description": "Test idea 1"},
                    {"idea_number": 2, "description": "Test idea 2"}
                ]
            })
            mock_client.models.generate_content.return_value = mock_response
            
            generate_ideas(
                topic="test topic",
                context="test context",
                temperature=0.7,
                use_structured_output=True
            )
            
            # Verify structured output was requested
            call_args = mock_client.models.generate_content.call_args
            config = call_args[1]['config']
            
            # Check that response_mime_type is set for JSON
            assert hasattr(config, 'response_mime_type')
            assert config.response_mime_type == "application/json"
            
            # Check that response_schema is provided
            assert hasattr(config, 'response_schema')
    
    def test_idea_generator_prompt_no_manual_formatting(self):
        """Test that idea generation prompt doesn't include manual formatting instructions."""
        from src.madspark.agents.idea_generator import build_generation_prompt
        
        prompt = build_generation_prompt(
            topic="test topic",
            context="test context"
        )
        
        # Check that prompt doesn't contain manual formatting instructions
        assert "Format:" not in prompt
        assert "**Idea" not in prompt
        assert "JSON format:" not in prompt
        
        # Should focus on content, not format
        assert "creative" in prompt.lower()
        assert "innovative" in prompt.lower()


class TestStructuredEvaluation:
    """Test that evaluation uses structured output."""
    
    def test_critic_uses_structured_output(self):
        """Test that critic requests structured output format."""
        from src.madspark.agents.critic import evaluate_ideas
        
        with patch('src.madspark.agents.critic.critic_client') as mock_client:
            # Mock structured response
            mock_response = Mock()
            mock_response.text = json.dumps([
                {"score": 8, "comment": "Good idea"},
                {"score": 7, "comment": "Needs work"}
            ])
            mock_client.models.generate_content.return_value = mock_response
            
            evaluate_ideas(
                ideas="Idea 1\nIdea 2",
                criteria="test criteria",
                context="test context",
                temperature=0.3,
                use_structured_output=True
            )
            
            # Verify structured output was requested
            call_args = mock_client.models.generate_content.call_args
            config = call_args[1]['config']
            
            # Check that response_mime_type is set for JSON
            assert hasattr(config, 'response_mime_type')
            assert config.response_mime_type == "application/json"


class TestStructuredAdvocacy:
    """Test that advocacy uses structured output."""
    
    def test_advocate_batch_uses_structured_output(self):
        """Test that advocate batch function uses structured output."""
        from src.madspark.agents.advocate import advocate_ideas_batch
        
        ideas_with_evaluations = [
            {"idea": "Test idea", "evaluation": "Good", "context": "test context"}
        ]
        
        with patch('src.madspark.agents.advocate.advocate_client') as mock_client:
            # Mock structured response
            mock_response = Mock()
            mock_response.text = json.dumps([{
                "idea_index": 0,
                "advocacy": "Strong advocacy",
                "key_strengths": ["Innovation", "Feasibility"],
                "strengths": "Innovative and feasible",
                "opportunities": "Market potential",
                "addressing_concerns": "Risk mitigation"
            }])
            mock_response.usage_metadata = Mock(total_token_count=100)
            mock_client.models.generate_content.return_value = mock_response
            
            results, tokens = advocate_ideas_batch(ideas_with_evaluations, topic="test", context="test context", temperature=0.5
            )
            
            # Verify structured output was requested
            call_args = mock_client.models.generate_content.call_args
            config = call_args[1]['config']
            
            # Check configuration
            assert hasattr(config, 'response_mime_type')
            assert config.response_mime_type == "application/json"


class TestStructuredSkepticism:
    """Test that skepticism uses structured output."""
    
    def test_skeptic_batch_uses_structured_output(self):
        """Test that skeptic batch function uses structured output."""
        from src.madspark.agents.skeptic import criticize_ideas_batch
        
        ideas_with_advocacy = [
            {"idea": "Test idea", "advocacy": "Strong points"}
        ]
        
        with patch('src.madspark.agents.skeptic.skeptic_client') as mock_client:
            # Mock structured response
            mock_response = Mock()
            mock_response.text = json.dumps([{
                "idea_index": 0,
                "skepticism": "Critical analysis",
                "concerns": ["Risk 1", "Risk 2"],
                "critical_flaws": "Major issue",
                "missing_considerations": "Overlooked aspect",
                "risks_challenges": "Implementation risk",
                "questionable_assumptions": "Assumption critique"
            }])
            mock_response.usage_metadata = Mock(total_token_count=100)
            mock_client.models.generate_content.return_value = mock_response
            
            results, tokens = criticize_ideas_batch(
                ideas_with_advocacy,
                context="test context",
                temperature=0.5
            )
            
            # Verify structured output was requested
            call_args = mock_client.models.generate_content.call_args
            config = call_args[1]['config']
            
            # Check configuration
            assert hasattr(config, 'response_mime_type')
            assert config.response_mime_type == "application/json"


class TestStructuredImprovement:
    """Test that improvement uses structured output."""
    
    def test_improvement_batch_uses_structured_output(self):
        """Test that improvement batch function uses structured output."""
        from src.madspark.agents.idea_generator import improve_ideas_batch
        
        ideas_with_feedback = [
            {
                "idea": "Original idea",
                "critique": "Needs work",
                "advocacy": "Has potential",
                "skepticism": "Some risks"
            }
        ]
        
        with patch('src.madspark.agents.idea_generator.idea_generator_client') as mock_client:
            # Mock structured response
            mock_response = Mock()
            mock_response.text = json.dumps([{
                "idea_index": 0,
                "improved_idea": "Enhanced idea with improvements",
                "key_improvements": ["Added feature X", "Mitigated risk Y"]
            }])
            mock_response.usage_metadata = Mock(total_token_count=100)
            mock_client.models.generate_content.return_value = mock_response
            
            results, tokens = improve_ideas_batch(
                ideas_with_feedback,
                context="test context",
                temperature=0.9
            )
            
            # Verify structured output was requested
            call_args = mock_client.models.generate_content.call_args
            config = call_args[1]['config']
            
            # Check configuration
            assert hasattr(config, 'response_mime_type')
            assert config.response_mime_type == "application/json"


class TestLegacyParsingRemoval:
    """Test that legacy parsing is removed when using structured output."""
    
    def test_no_manual_parsing_with_structured_output(self):
        """Test that manual parsing is bypassed with structured output."""
        from src.madspark.utils.json_parsers import parse_idea_generator_response
        
        # When given already-parsed JSON, should return as-is
        structured_response = json.dumps({
            "ideas": [
                {"idea_number": 1, "description": "Idea 1"},
                {"idea_number": 2, "description": "Idea 2"}
            ]
        })
        
        result = parse_idea_generator_response(structured_response)
        
        # Should extract and format the ideas
        assert len(result) == 2
        assert "Idea 1" in result[0]
        assert "Idea 2" in result[1]
        
    def test_legacy_parsing_still_works(self):
        """Test that legacy text parsing still works for backward compatibility."""
        from src.madspark.utils.json_parsers import parse_idea_generator_response
        
        # Legacy formatted response
        legacy_response = """
        **Idea 1:** This is the first idea
        **Idea 2:** This is the second idea
        """
        
        result = parse_idea_generator_response(legacy_response)
        
        # Should still parse legacy format
        assert len(result) == 2
        assert "This is the first idea" in result[0]
        assert "This is the second idea" in result[1]


class TestPromptSimplification:
    """Test that prompts are simplified without formatting instructions."""
    
    def test_prompts_focus_on_content_not_format(self):
        """Test that all prompts focus on content rather than formatting."""
        from src.madspark.agents.idea_generator import build_generation_prompt
        
        # Check idea generation prompt with structured output
        idea_prompt = build_generation_prompt("topic", "context", use_structured_output=True)
        assert "json" not in idea_prompt.lower()
        assert "format requirements" not in idea_prompt.lower()
        
        # Verify prompt contains content-focused keywords
        assert any(word in idea_prompt.lower() for word in ["creative", "innovative", "practical"])
        
        # Legacy prompt should still have formatting for backward compatibility
        legacy_prompt = build_generation_prompt("topic", "context", use_structured_output=False)
        assert "format requirements" in legacy_prompt.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])