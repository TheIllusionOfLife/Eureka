"""Tests for coordinator with batch processing."""
import os
from unittest.mock import Mock, patch

try:
    from madspark.core.coordinator_batch import run_multistep_workflow_batch as run_multistep_workflow
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.core.coordinator_batch import run_multistep_workflow_batch as run_multistep_workflow


class TestCoordinatorBatchProcessing:
    """Test coordinator uses batch API calls efficiently."""
    
    @patch('madspark.core.coordinator_batch.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator_batch.call_critic_with_retry')
    @patch('madspark.core.coordinator_batch.advocate_ideas_batch')
    @patch('madspark.core.coordinator_batch.criticize_ideas_batch')
    @patch('madspark.core.coordinator_batch.improve_ideas_batch')
    def test_coordinator_uses_batch_processing_single_candidate(
        self, 
        mock_improve_batch, 
        mock_criticize_batch,
        mock_advocate_batch,
        mock_evaluate,
        mock_generate
    ):
        """Test coordinator uses batch functions for single candidate."""
        # Mock idea generation
        mock_generate.return_value = "Idea 1: Smart traffic system"
        
        # Mock critic evaluation (already batched)
        mock_evaluate.return_value = '{"score": 8, "comment": "Good feasibility"}'
        
        # Mock batch advocate
        mock_advocate_batch.return_value = ([{
            "idea_index": 0,
            "strengths": ["Innovative", "Scalable"],
            "opportunities": ["Reduce congestion", "Save fuel"],
            "addressing_concerns": ["Phased implementation", "Public-private partnership"],
            "formatted": "STRENGTHS:\n• Innovative\n• Scalable"
        }], 100)
        
        # Mock batch skeptic
        mock_criticize_batch.return_value = ([{
            "idea_index": 0,
            "critical_flaws": ["High cost", "Technical complexity"],
            "risks_challenges": ["Maintenance issues", "Public resistance"],
            "questionable_assumptions": ["Full adoption", "Tech reliability"],
            "missing_considerations": ["Privacy concerns", "Cybersecurity"],
            "formatted": "CRITICAL FLAWS:\n• High cost\n• Technical complexity"
        }], 100)
        
        # Mock batch improvement
        mock_improve_batch.return_value = ([{
            "idea_index": 0,
            "improved_idea": "Smart traffic system with AI optimization and privacy protection",
            "key_improvements": ["Added privacy safeguards", "Phased rollout plan"]
        }], 100)
        
        # Run workflow
        run_multistep_workflow(
            theme="Urban Innovation",
            constraints="Budget-friendly",
            num_top_candidates=1
        )
        
        # Verify batch functions were called
        assert mock_advocate_batch.called
        assert mock_criticize_batch.called
        assert mock_improve_batch.called
        
        # Verify correct arguments
        advocate_args = mock_advocate_batch.call_args[0][0]
        assert len(advocate_args) == 1
        assert "idea" in advocate_args[0]
        assert "evaluation" in advocate_args[0]
        
        # Verify batch functions were called
        assert mock_advocate_batch.call_count == 1
        assert mock_criticize_batch.call_count == 1
        assert mock_improve_batch.call_count == 1
        
        # In mock mode, the idea generator and critic may not be called through mocks
        # because they return mock data directly. Check if we're in mock mode.
        if os.getenv('MADSPARK_MODE') != 'mock':
            # Only check these in non-mock mode
            assert mock_generate.call_count == 1
            assert mock_evaluate.call_count == 2  # Initial + re-eval after improvement
    
    @patch('madspark.core.coordinator_batch.call_idea_generator_with_retry')
    @patch('madspark.core.coordinator_batch.call_critic_with_retry')
    @patch('madspark.core.coordinator_batch.advocate_ideas_batch')
    @patch('madspark.core.coordinator_batch.criticize_ideas_batch')
    @patch('madspark.core.coordinator_batch.improve_ideas_batch')
    def test_coordinator_uses_batch_processing_multiple_candidates(
        self, 
        mock_improve_batch, 
        mock_criticize_batch,
        mock_advocate_batch,
        mock_evaluate,
        mock_generate
    ):
        """Test coordinator uses batch functions for multiple candidates."""
        # Mock idea generation
        mock_generate.return_value = """Idea 1: Smart traffic system
Idea 2: Green rooftop gardens
Idea 3: Community bike sharing"""
        
        # Mock critic evaluation (already batched)
        mock_evaluate.return_value = """{"score": 8, "comment": "Good feasibility"}
{"score": 7, "comment": "Moderate impact"}
{"score": 9, "comment": "Excellent potential"}"""
        
        # Mock batch advocate for 3 ideas - returns tuple
        mock_advocate_batch.return_value = ([
            {
                "idea_index": 0,
                "strengths": ["Innovative"],
                "opportunities": ["Reduce congestion"],
                "addressing_concerns": ["Phased implementation"],
                "formatted": "STRENGTHS:\n• Innovative"
            },
            {
                "idea_index": 1,
                "strengths": ["Environmental"],
                "opportunities": ["Urban cooling"],
                "addressing_concerns": ["Incentives available"],
                "formatted": "STRENGTHS:\n• Environmental"
            },
            {
                "idea_index": 2,
                "strengths": ["Community-focused"],
                "opportunities": ["Health benefits"],
                "addressing_concerns": ["Low cost"],
                "formatted": "STRENGTHS:\n• Community-focused"
            }
        ], 1500)
        
        # Mock batch skeptic for 3 ideas - returns tuple
        mock_criticize_batch.return_value = ([
            {
                "idea_index": i,
                "critical_flaws": [f"Flaw {i+1}"],
                "risks_challenges": [f"Risk {i+1}"],
                "questionable_assumptions": [f"Assumption {i+1}"],
                "missing_considerations": [f"Missing {i+1}"],
                "formatted": f"CRITICAL FLAWS:\n• Flaw {i+1}"
            }
            for i in range(3)
        ], 1200)
        
        # Mock batch improvement for 3 ideas - returns tuple
        mock_improve_batch.return_value = ([
            {
                "idea_index": i,
                "improved_idea": f"Improved idea {i+1} with enhancements",
                "key_improvements": [f"Enhancement {i+1}"]
            }
            for i in range(3)
        ], 1800)
        
        # Run workflow with 3 candidates
        run_multistep_workflow(
            theme="Urban Innovation",
            constraints="Budget-friendly",
            num_top_candidates=3
        )
        
        # Verify batch functions were called once each
        assert mock_advocate_batch.call_count == 1
        assert mock_criticize_batch.call_count == 1
        assert mock_improve_batch.call_count == 1
        
        # Verify batch sizes
        advocate_args = mock_advocate_batch.call_args[0][0]
        # Should always be 3 since we mocked generation to return 3 ideas
        assert len(advocate_args) == 3
        
        criticize_args = mock_criticize_batch.call_args[0][0]
        assert len(criticize_args) == 3
        
        improve_args = mock_improve_batch.call_args[0][0]
        assert len(improve_args) == 3
        
        # In mock mode, only batch functions are called through mocks
        if os.getenv('MADSPARK_MODE') != 'mock':
            # Verify total API calls (not 17 which would be old way for 3 candidates)
            # 1 generate + 2 critic (initial + re-eval) + 1 advocate + 1 skeptic + 1 improve = 6
            total_api_calls = (
                mock_generate.call_count +
                mock_evaluate.call_count +
                mock_advocate_batch.call_count +
                mock_criticize_batch.call_count +
                mock_improve_batch.call_count
            )
            assert total_api_calls == 6
    
    @patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry')
    @patch('madspark.utils.agent_retry_wrappers.call_critic_with_retry')
    @patch('madspark.core.coordinator_batch.advocate_ideas_batch')
    @patch('madspark.core.coordinator_batch.criticize_ideas_batch')
    @patch('madspark.core.coordinator_batch.improve_ideas_batch')
    @patch('madspark.core.coordinator_batch.ReasoningEngine')
    def test_coordinator_batch_with_multi_dimensional_eval(
        self,
        mock_reasoning_engine_class,
        mock_improve_batch,
        mock_criticize_batch,
        mock_advocate_batch,
        mock_evaluate,
        mock_generate
    ):
        """Test coordinator uses batch multi-dimensional evaluation."""
        # Setup reasoning engine mock
        mock_engine = Mock()
        mock_evaluator = Mock()
        mock_engine.multi_evaluator = mock_evaluator
        mock_reasoning_engine_class.return_value = mock_engine
        
        # Mock batch multi-dimensional evaluation
        mock_evaluator.evaluate_ideas_batch.return_value = [
            {
                "idea_index": 0,
                "overall_score": 7.5,
                "weighted_score": 7.8,
                "feasibility": 8,
                "innovation": 7,
                "impact": 8,
                "cost_effectiveness": 7,
                "scalability": 8,
                "risk_assessment": 7,
                "timeline": 6,
                "dimension_scores": {
                    "feasibility": 8,
                    "innovation": 7,
                    "impact": 8,
                    "cost_effectiveness": 7,
                    "scalability": 8,
                    "risk_assessment": 7,
                    "timeline": 6
                },
                "confidence_interval": 0.85,
                "evaluation_summary": "Strong potential"
            }
        ]
        
        # Mock other calls
        mock_generate.return_value = "Idea 1: Smart traffic system"
        mock_evaluate.return_value = '{"score": 8, "comment": "Good"}'
        
        mock_advocate_batch.return_value = ([{
            "idea_index": 0,
            "strengths": ["Good"],
            "opportunities": ["Great"],
            "addressing_concerns": ["Handled"],
            "formatted": "STRENGTHS:\n• Good"
        }], 100)
        
        mock_criticize_batch.return_value = ([{
            "idea_index": 0,
            "critical_flaws": ["Issue"],
            "risks_challenges": ["Risk"],
            "questionable_assumptions": ["Assumption"],
            "missing_considerations": ["Missing"],
            "formatted": "CRITICAL FLAWS:\n• Issue"
        }], 100)
        
        mock_improve_batch.return_value = ([{
            "idea_index": 0,
            "improved_idea": "Better idea",
            "key_improvements": ["Improved"]
        }], 100)
        
        # Run workflow with multi-dimensional eval
        run_multistep_workflow(
            theme="Urban Innovation",
            constraints="Budget-friendly",
            num_top_candidates=1,
            multi_dimensional_eval=True,
            enable_reasoning=True
        )
        
        # Verify batch multi-dimensional evaluation was called
        assert mock_evaluator.evaluate_ideas_batch.called
        
        # Should be called twice (initial + after improvement)
        assert mock_evaluator.evaluate_ideas_batch.call_count == 2
        
        # Verify the ideas were evaluated in batch
        first_call_args = mock_evaluator.evaluate_ideas_batch.call_args_list[0][0][0]
        assert isinstance(first_call_args, list)
        assert len(first_call_args) == 1  # One idea