"""Integration tests for batch coordinator with real mock data."""
import pytest
from unittest.mock import Mock, patch
import json

try:
    from madspark.core.coordinator_batch import run_multistep_workflow_batch
    from madspark.utils.errors import ConfigurationError
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.core.coordinator_batch import run_multistep_workflow_batch
    from madspark.utils.errors import ConfigurationError


class TestCoordinatorBatchIntegration:
    """Integration tests for the batch coordinator."""
    
    @patch('madspark.core.coordinator_batch.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator_batch.call_critic_with_retry')
    @patch('madspark.core.coordinator_batch.advocate_ideas_batch')
    @patch('madspark.core.coordinator_batch.criticize_ideas_batch')
    @patch('madspark.core.coordinator_batch.improve_ideas_batch')
    def test_full_workflow_with_batch_processing(
        self,
        mock_improve_batch,
        mock_criticize_batch,
        mock_advocate_batch,
        mock_critic,
        mock_idea_gen
    ):
        """Test complete workflow with batch processing."""
        # Mock idea generation
        mock_idea_gen.return_value = """Idea 1: AI-powered smart traffic lights that adapt to real-time traffic patterns
Idea 2: Vertical farming towers integrated into apartment buildings
Idea 3: Community solar gardens with blockchain-based energy sharing"""
        
        # Mock critic evaluation (batch)
        mock_critic.side_effect = [
            # Initial evaluation
            """{"score": 8, "comment": "Strong technical feasibility and high impact potential"}
{"score": 7, "comment": "Good environmental benefits but requires significant infrastructure"}
{"score": 9, "comment": "Excellent community engagement and scalability"}""",
            # Re-evaluation after improvement
            """{"score": 9, "comment": "Enhanced implementation plan addresses initial concerns"}
{"score": 8, "comment": "Phased approach improves feasibility"}
{"score": 9, "comment": "Maintained strengths while addressing challenges"}"""
        ]
        
        # Mock batch advocate
        mock_advocate_batch.return_value = [
            {
                "idea_index": 0,
                "strengths": ["Reduces congestion by 30%", "AI learns traffic patterns"],
                "opportunities": ["Smart city integration", "Emergency vehicle prioritization"],
                "addressing_concerns": ["Gradual rollout plan", "Public-private partnership"],
                "formatted": "STRENGTHS:\n• Reduces congestion by 30%\n• AI learns traffic patterns"
            },
            {
                "idea_index": 1,
                "strengths": ["Local food production", "Reduces carbon footprint"],
                "opportunities": ["Job creation", "Educational programs"],
                "addressing_concerns": ["Modular design reduces costs", "Grants available"],
                "formatted": "STRENGTHS:\n• Local food production\n• Reduces carbon footprint"
            },
            {
                "idea_index": 2,
                "strengths": ["Community ownership", "Transparent energy trading"],
                "opportunities": ["Scalable model", "Energy independence"],
                "addressing_concerns": ["Proven blockchain tech", "Regulatory compliance"],
                "formatted": "STRENGTHS:\n• Community ownership\n• Transparent energy trading"
            }
        ]
        
        # Mock batch skeptic
        mock_criticize_batch.return_value = [
            {
                "idea_index": 0,
                "critical_flaws": ["High initial cost", "Complex AI systems"],
                "risks_challenges": ["Maintenance complexity", "Cybersecurity vulnerabilities"],
                "questionable_assumptions": ["Full city adoption", "Consistent funding"],
                "missing_considerations": ["Privacy concerns", "Power outages"],
                "formatted": "CRITICAL FLAWS:\n• High initial cost\n• Complex AI systems"
            },
            {
                "idea_index": 1,
                "critical_flaws": ["Space constraints", "Water usage"],
                "risks_challenges": ["Structural modifications needed", "Pest management"],
                "questionable_assumptions": ["Resident participation", "Crop yield estimates"],
                "missing_considerations": ["Building codes", "Insurance issues"],
                "formatted": "CRITICAL FLAWS:\n• Space constraints\n• Water usage"
            },
            {
                "idea_index": 2,
                "critical_flaws": ["Regulatory hurdles", "Technical complexity"],
                "risks_challenges": ["Grid integration challenges", "User adoption"],
                "questionable_assumptions": ["Blockchain scalability", "Community buy-in"],
                "missing_considerations": ["Maintenance costs", "Weather dependencies"],
                "formatted": "CRITICAL FLAWS:\n• Regulatory hurdles\n• Technical complexity"
            }
        ]
        
        # Mock batch improvement
        mock_improve_batch.return_value = [
            {
                "idea_index": 0,
                "improved_idea": "AI-powered smart traffic system with edge computing for reliability, phased deployment starting with high-traffic intersections, and open-source components for transparency",
                "key_improvements": ["Added edge computing", "Phased deployment", "Open-source approach"]
            },
            {
                "idea_index": 1,
                "improved_idea": "Modular vertical farming units with smart water recycling, integrated pest management using beneficial insects, and community education center",
                "key_improvements": ["Water recycling system", "Natural pest control", "Education component"]
            },
            {
                "idea_index": 2,
                "improved_idea": "Hybrid solar garden with battery storage, simplified peer-to-peer energy trading app, and weather-resilient design with backup grid connection",
                "key_improvements": ["Battery storage added", "Simplified trading", "Weather resilience"]
            }
        ]
        
        # Run the workflow
        results = run_multistep_workflow_batch(
            theme="Sustainable Urban Innovation",
            constraints="Must be implementable within 5 years, community-focused, and environmentally beneficial",
            num_top_candidates=3,
            verbose=False
        )
        
        # Verify results
        assert len(results) == 3
        
        # Check first candidate
        candidate1 = results[0]
        assert "AI-powered smart traffic" in candidate1["idea"]
        assert candidate1["initial_score"] == 8
        assert candidate1["improved_score"] == 9
        assert candidate1["score_delta"] == 1
        assert "STRENGTHS:" in candidate1["advocacy"]
        assert "CRITICAL FLAWS:" in candidate1["skepticism"]
        assert "edge computing" in candidate1["improved_idea"]
        
        # Verify batch functions were called correctly
        assert mock_advocate_batch.call_count == 1
        assert mock_criticize_batch.call_count == 1
        assert mock_improve_batch.call_count == 1
        
        # Verify batch sizes
        advocate_call = mock_advocate_batch.call_args[0][0]
        assert len(advocate_call) == 3
        
        # Verify only 7 total API calls (not 13 which would be old way)
        # 1 generate + 2 critic (initial + re-eval) + 1 advocate + 1 skeptic + 1 improve = 6
        total_api_calls = (
            mock_idea_gen.call_count +      # 1
            mock_critic.call_count +         # 2
            mock_advocate_batch.call_count + # 1
            mock_criticize_batch.call_count +# 1
            mock_improve_batch.call_count    # 1
        )
        assert total_api_calls == 6
    
    @patch('madspark.core.coordinator_batch.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator_batch.call_critic_with_retry')
    @patch('madspark.core.coordinator_batch.advocate_ideas_batch')
    @patch('madspark.core.coordinator_batch.criticize_ideas_batch')
    @patch('madspark.core.coordinator_batch.improve_ideas_batch')
    def test_batch_processing_with_failures(
        self,
        mock_improve_batch,
        mock_criticize_batch,
        mock_advocate_batch,
        mock_critic,
        mock_idea_gen
    ):
        """Test batch processing handles partial failures gracefully."""
        # Mock idea generation
        mock_idea_gen.return_value = "Idea 1: Test idea"
        
        # Mock critic evaluation
        mock_critic.side_effect = [
            '{"score": 8, "comment": "Good"}',
            '{"score": 9, "comment": "Better"}'
        ]
        
        # Mock advocate batch failure
        mock_advocate_batch.side_effect = Exception("API Error")
        
        # Mock skeptic success
        mock_criticize_batch.return_value = [{
            "idea_index": 0,
            "critical_flaws": ["Issue"],
            "risks_challenges": ["Risk"],
            "questionable_assumptions": ["Assumption"],
            "missing_considerations": ["Missing"],
            "formatted": "CRITICAL FLAWS:\n• Issue"
        }]
        
        # Mock improvement success
        mock_improve_batch.return_value = [{
            "idea_index": 0,
            "improved_idea": "Better idea",
            "key_improvements": ["Improved"]
        }]
        
        # Run workflow - should handle advocate failure gracefully
        results = run_multistep_workflow_batch(
            theme="Test",
            constraints="Test constraints",
            num_top_candidates=1
        )
        
        assert len(results) == 1
        assert results[0]["advocacy"] == "N/A (Batch advocate failed)"
        assert "CRITICAL FLAWS:" in results[0]["skepticism"]
        assert results[0]["improved_idea"] == "Better idea"