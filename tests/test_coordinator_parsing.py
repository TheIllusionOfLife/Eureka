"""Test coordinator evaluation parsing to fix Issue #118."""
import json
from unittest.mock import patch, MagicMock
import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.utils import parse_json_with_fallback
from madspark.core.coordinator import run_multistep_workflow


class TestCoordinatorEvaluationParsing:
    """Test suite for coordinator evaluation parsing issues."""
    
    def test_parse_json_with_fallback_handles_critic_format(self):
        """Test parsing the exact format that Critic agent returns."""
        # This is the actual format we see from Critic in production
        raw_evaluations = """Evaluating ideas for sustainable urban living:

{"score": 8, "comment": "Vertical farming with air purification is highly innovative and addresses multiple urban challenges. The technology is proven and scalable."}

{"score": 7, "comment": "Community solar gardens show good potential for community engagement but require significant upfront investment and regulatory approvals."}

{"score": 9, "comment": "Smart traffic optimization using AI has excellent feasibility with existing infrastructure and can deliver immediate impact on congestion and emissions."}

{"score": 6, "comment": "Neighborhood composting hubs are simple to implement but have limited impact scope. Good for community building but not transformative."}

{"score": 7, "comment": "Green roof incentive programs offer moderate environmental benefits but require policy changes and ongoing maintenance support."}"""
        
        parsed = parse_json_with_fallback(raw_evaluations, expected_count=5)
        
        # Should extract all 5 evaluations
        assert len(parsed) == 5, f"Expected 5 evaluations but got {len(parsed)}"
        
        # Verify all scores are correct
        scores = [item['score'] for item in parsed]
        assert scores == [8, 7, 9, 6, 7], f"Expected scores [8,7,9,6,7] but got {scores}"
        
        # Verify comments contain key phrases
        assert "Vertical farming" in parsed[0]['comment']
        assert "Community solar" in parsed[1]['comment']
        assert "Smart traffic" in parsed[2]['comment']
    
    def test_parse_json_with_fallback_handles_multiple_evaluations(self):
        """Test that parse_json_with_fallback correctly parses all evaluations."""
        # Simulate a response with multiple evaluations like what Critic returns
        raw_evaluations = """Here are my evaluations for the ideas:

1. Vertical farming with air purification
   Score: 8
   Comment: Excellent feasibility with proven technology. The dual-purpose approach maximizes urban space efficiency.

2. Community solar gardens
   Score: 7
   Comment: Good community engagement potential but requires significant initial investment.

3. Smart traffic flow optimization
   Score: 9
   Comment: High impact potential with existing infrastructure. AI-driven approach is innovative.

4. Neighborhood composting hubs
   Score: 6
   Comment: Simple to implement but limited scalability. Good for community building.

5. Green roof incentive program
   Score: 7
   Comment: Moderate impact but requires policy changes. Cost-effective in long term."""
        
        # Parse the evaluations
        parsed = parse_json_with_fallback(raw_evaluations, expected_count=5)
        
        # Should extract all 5 evaluations
        assert len(parsed) == 5, f"Expected 5 evaluations but got {len(parsed)}"
        
        # Verify scores and comments were extracted
        assert parsed[0]['score'] == 8
        assert 'Excellent feasibility' in parsed[0]['comment']
        
        assert parsed[2]['score'] == 9
        assert 'High impact potential' in parsed[2]['comment']
        
    def test_parse_json_with_fallback_handles_json_array(self):
        """Test parsing of proper JSON array format."""
        raw_evaluations = json.dumps([
            {"score": 8, "comment": "Great idea with good feasibility"},
            {"score": 7, "comment": "Solid concept but needs refinement"},
            {"score": 9, "comment": "Excellent innovation and impact"}
        ])
        
        parsed = parse_json_with_fallback(raw_evaluations, expected_count=3)
        assert len(parsed) == 3
        assert all('score' in item and 'comment' in item for item in parsed)
        
    def test_parse_json_with_fallback_handles_mixed_format(self):
        """Test parsing of mixed format responses."""
        raw_evaluations = """{"score": 8, "comment": "First evaluation"}
Some narrative text here
Score: 7, Comment: Second evaluation is good
{"score": 9, "comment": "Third evaluation"}"""
        
        parsed = parse_json_with_fallback(raw_evaluations, expected_count=3)
        assert len(parsed) >= 2  # Should get at least the JSON objects
        
    def test_coordinator_generates_and_evaluates_all_ideas(self):
        """Test that coordinator properly evaluates all generated ideas."""
        # Mock the agent functions with minimal overhead
        with patch('madspark.core.coordinator.call_idea_generator_with_retry') as mock_generator, \
             patch('madspark.core.coordinator.call_critic_with_retry') as mock_critic, \
             patch('madspark.core.coordinator.call_advocate_with_retry') as mock_advocate, \
             patch('madspark.core.coordinator.call_skeptic_with_retry') as mock_skeptic, \
             patch('madspark.core.coordinator.call_improve_idea_with_retry') as mock_improve, \
             patch('madspark.core.coordinator.ReasoningEngine') as mock_engine:
            
            # Mock reasoning engine to avoid initialization overhead
            mock_engine_instance = MagicMock()
            mock_engine_instance.multi_evaluator = None  # Disable multi-dimensional eval for speed
            mock_engine.return_value = mock_engine_instance
            
            # Mock idea generation - return many ideas
            ideas_list = [f"Idea {i}: Creative solution for urban sustainability" for i in range(1, 11)]
            mock_generator.return_value = "\n".join(ideas_list)
            
            # Mock evaluation - return evaluations for ALL ideas
            evaluations = []
            for i in range(1, 11):
                evaluations.append({
                    "score": 5 + (i % 5),  # Scores from 5-9
                    "comment": f"Evaluation for idea {i}"
                })
            mock_critic.return_value = json.dumps(evaluations)
            
            # Mock other agents with simple responses
            mock_advocate.return_value = "Strong advocacy points"
            mock_skeptic.return_value = "Valid concerns raised"
            mock_improve.return_value = "Improved idea with enhancements"
            
            # Run workflow with reduced ideas
            results = run_multistep_workflow(
                theme="Sustainable Urban Living",
                constraints="Budget-friendly and community-focused",
                num_top_candidates=2,
                enable_novelty_filter=False,  # Disable to test all ideas
                enhanced_reasoning=False,  # Disable for speed
                multi_dimensional_eval=False,  # Disable for speed
                logical_inference=False  # Disable for speed
            )
            
            # Verify the generator was called once
            assert mock_generator.call_count == 1
            
            # Verify critic was called - it gets called twice (initial eval + improved eval)
            assert mock_critic.call_count >= 1
            
            # Get the first call to critic (for initial ideas evaluation)
            first_critic_call = mock_critic.call_args_list[0]
            critic_call_args = first_critic_call[1]
            assert 'ideas' in critic_call_args
            ideas_sent_to_critic = critic_call_args['ideas'].split('\n')
            assert len(ideas_sent_to_critic) == 10
            
            # Results should have top 2 candidates with proper evaluations
            assert len(results) == 2
            assert all(result['initial_score'] > 0 for result in results)
            assert all(result['initial_critique'] != "Evaluation missing from critic response." for result in results)
    
    def test_parse_handles_narrative_evaluation_format(self):
        """Test parsing of narrative format that Critic might return."""
        raw_evaluations = """Based on the criteria provided, here are my evaluations:

The first idea about vertical farming scores an 8 out of 10. Comment: This is highly feasible with current technology and addresses multiple urban challenges effectively.

For the second idea regarding community solar gardens, I give it a score of 7. Comment: Good potential but requires significant community buy-in and initial investment.

The third concept of smart traffic optimization deserves a 9. Comment: Excellent use of existing infrastructure with high impact potential.

The fourth idea about composting hubs gets a 6. Comment: Simple and practical but limited in scope.

Finally, the green roof program scores 7. Comment: Moderate complexity with good long-term benefits."""
        
        parsed = parse_json_with_fallback(raw_evaluations, expected_count=5)
        
        # Should extract evaluations even from narrative format
        assert len(parsed) >= 3, f"Expected at least 3 evaluations but got {len(parsed)}"
        
        # Check that scores were extracted
        scores = [item['score'] for item in parsed]
        assert 8 in scores or 9 in scores, "Should extract high scores from narrative"