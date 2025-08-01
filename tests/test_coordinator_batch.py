"""Tests for coordinator with batch processing."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from typing import List, Dict, Any

try:
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.utils.errors import ConfigurationError
except ImportError:
    import sys
    sys.path.insert(0, 'src')
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.utils.errors import ConfigurationError


class TestCoordinatorBatchProcessing:
    """Test coordinator uses batch API calls efficiently."""
    
    @patch('madspark.core.coordinator.generate_ideas_with_retry')
    @patch('madspark.core.coordinator.evaluate_ideas_with_retry')
    @patch('madspark.core.coordinator.advocate_ideas_batch')
    @patch('madspark.core.coordinator.criticize_ideas_batch')
    @patch('madspark.core.coordinator.improve_ideas_batch')
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
        mock_advocate_batch.return_value = [{
            "idea_index": 0,
            "strengths": ["Innovative", "Scalable"],
            "opportunities": ["Reduce congestion", "Save fuel"],
            "addressing_concerns": ["Phased implementation", "Public-private partnership"],
            "formatted": "STRENGTHS:\n• Innovative\n• Scalable"
        }]
        
        # Mock batch skeptic
        mock_criticize_batch.return_value = [{
            "idea_index": 0,
            "critical_flaws": ["High cost", "Technical complexity"],
            "risks_challenges": ["Maintenance issues", "Public resistance"],
            "questionable_assumptions": ["Full adoption", "Tech reliability"],
            "missing_considerations": ["Privacy concerns", "Cybersecurity"],
            "formatted": "CRITICAL FLAWS:\n• High cost\n• Technical complexity"
        }]
        
        # Mock batch improvement
        mock_improve_batch.return_value = [{
            "idea_index": 0,
            "improved_idea": "Smart traffic system with AI optimization and privacy protection",
            "key_improvements": ["Added privacy safeguards", "Phased rollout plan"]
        }]
        
        # Run workflow
        results = run_multistep_workflow(
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
        
        # Verify only 5 API calls total (gen, eval, advocate, skeptic, improve)
        total_api_calls = (
            mock_generate.call_count +
            mock_evaluate.call_count +
            mock_advocate_batch.call_count +
            mock_criticize_batch.call_count +
            mock_improve_batch.call_count
        )
        assert total_api_calls == 5
    
    @patch('madspark.core.coordinator.generate_ideas_with_retry')
    @patch('madspark.core.coordinator.evaluate_ideas_with_retry')
    @patch('madspark.core.coordinator.advocate_ideas_batch')
    @patch('madspark.core.coordinator.criticize_ideas_batch')
    @patch('madspark.core.coordinator.improve_ideas_batch')
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
        
        # Mock batch advocate for 3 ideas
        mock_advocate_batch.return_value = [
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
        ]
        
        # Mock batch skeptic for 3 ideas
        mock_criticize_batch.return_value = [
            {
                "idea_index": i,
                "critical_flaws": [f"Flaw {i+1}"],
                "risks_challenges": [f"Risk {i+1}"],
                "questionable_assumptions": [f"Assumption {i+1}"],
                "missing_considerations": [f"Missing {i+1}"],
                "formatted": f"CRITICAL FLAWS:\n• Flaw {i+1}"
            }
            for i in range(3)
        ]
        
        # Mock batch improvement for 3 ideas
        mock_improve_batch.return_value = [
            {
                "idea_index": i,
                "improved_idea": f"Improved idea {i+1} with enhancements",
                "key_improvements": [f"Enhancement {i+1}"]
            }
            for i in range(3)
        ]
        
        # Run workflow with 3 candidates
        results = run_multistep_workflow(
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
        assert len(advocate_args) == 3
        
        criticize_args = mock_criticize_batch.call_args[0][0]
        assert len(criticize_args) == 3
        
        improve_args = mock_improve_batch.call_args[0][0]
        assert len(improve_args) == 3
        
        # Verify only 5 API calls total (not 11 which would be old way)
        total_api_calls = (
            mock_generate.call_count +
            mock_evaluate.call_count +
            mock_advocate_batch.call_count +
            mock_criticize_batch.call_count +
            mock_improve_batch.call_count
        )
        assert total_api_calls == 5
    
    @patch('madspark.core.coordinator.generate_ideas_with_retry')
    @patch('madspark.core.coordinator.evaluate_ideas_with_retry')
    @patch('madspark.core.coordinator.advocate_ideas_batch')
    @patch('madspark.core.coordinator.criticize_ideas_batch')
    @patch('madspark.core.coordinator.improve_ideas_batch')
    @patch('madspark.core.coordinator.ReasoningEngine')
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
        
        mock_advocate_batch.return_value = [{
            "idea_index": 0,
            "strengths": ["Good"],
            "opportunities": ["Great"],
            "addressing_concerns": ["Handled"],
            "formatted": "STRENGTHS:\n• Good"
        }]
        
        mock_criticize_batch.return_value = [{
            "idea_index": 0,
            "critical_flaws": ["Issue"],
            "risks_challenges": ["Risk"],
            "questionable_assumptions": ["Assumption"],
            "missing_considerations": ["Missing"],
            "formatted": "CRITICAL FLAWS:\n• Issue"
        }]
        
        mock_improve_batch.return_value = [{
            "idea_index": 0,
            "improved_idea": "Better idea",
            "key_improvements": ["Improved"]
        }]
        
        # Run workflow with multi-dimensional eval
        results = run_multistep_workflow(
            theme="Urban Innovation",
            constraints="Budget-friendly",
            num_top_candidates=1,
            multi_dimensional_eval=True
        )
        
        # Verify batch multi-dimensional evaluation was called
        assert mock_evaluator.evaluate_ideas_batch.called
        
        # Should be called twice (initial + after improvement)
        assert mock_evaluator.evaluate_ideas_batch.call_count == 2
        
        # Verify the ideas were evaluated in batch
        first_call_args = mock_evaluator.evaluate_ideas_batch.call_args_list[0][0][0]
        assert isinstance(first_call_args, list)
        assert len(first_call_args) == 1  # One idea