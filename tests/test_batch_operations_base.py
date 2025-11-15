"""Test suite for BatchOperationsBase - shared batch processing functionality.

This module tests the unified batch operations that eliminate code duplication
between async_coordinator.py and coordinator_batch.py.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from concurrent.futures import TimeoutError as FutureTimeoutError

from src.madspark.core.batch_operations_base import BatchOperationsBase


class TestBatchOperationsBase:
    """Test cases for the unified batch operations base class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.batch_ops = BatchOperationsBase()
    
    def test_init(self):
        """Test proper initialization of BatchOperationsBase."""
        assert self.batch_ops.executor is not None
        assert hasattr(self.batch_ops, 'executor')
    
    def test_prepare_advocacy_input(self):
        """Test preparation of advocacy input from candidates."""
        candidates = [
            {"text": "Idea 1", "critique": "Critique 1"},
            {"text": "Idea 2", "critique": "Critique 2"}
        ]
        
        result = self.batch_ops.prepare_advocacy_input(candidates)
        
        expected = [
            {"idea": "Idea 1", "evaluation": "Critique 1"},
            {"idea": "Idea 2", "evaluation": "Critique 2"}
        ]
        assert result == expected
    
    def test_prepare_skepticism_input(self):
        """Test preparation of skepticism input from candidates."""
        candidates = [
            {"text": "Idea 1", "critique": "Critique 1", "advocacy": "Advocacy 1"},
            {"text": "Idea 2", "critique": "Critique 2"}  # Missing advocacy
        ]
        
        result = self.batch_ops.prepare_skepticism_input(candidates)
        
        # Skeptic batch function expects 'idea' and 'advocacy' keys
        expected = [
            {"idea": "Idea 1", "advocacy": "Advocacy 1"},
            {"idea": "Idea 2", "advocacy": "N/A"}  # N/A for missing advocacy
        ]
        assert result == expected
    
    def test_prepare_improvement_input(self):
        """Test preparation of improvement input from candidates."""
        candidates = [
            {
                "text": "Idea 1", 
                "critique": "Critique 1",
                "advocacy": "Advocacy 1",
                "skepticism": "Skepticism 1"
            },
            {
                "text": "Idea 2", 
                "critique": "Critique 2"
                # Missing advocacy and skepticism
            }
        ]
        
        result = self.batch_ops.prepare_improvement_input(candidates)
        
        # Improvement batch function expects 'idea', 'critique', 'advocacy', 'skepticism' keys
        expected = [
            {
                "idea": "Idea 1",
                "critique": "Critique 1", 
                "advocacy": "Advocacy 1",
                "skepticism": "Skepticism 1"
            },
            {
                "idea": "Idea 2",
                "critique": "Critique 2",
                "advocacy": "N/A",  # N/A for missing values
                "skepticism": "N/A"
            }
        ]
        assert result == expected
    
    def test_update_candidates_with_batch_results(self):
        """Test updating candidates with batch processing results."""
        candidates = [
            {"text": "Idea 1"},
            {"text": "Idea 2"}
        ]
        batch_results = ["Result 1", "Result 2"]
        result_key = "advocacy"
        
        updated = self.batch_ops.update_candidates_with_batch_results(
            candidates, batch_results, result_key
        )
        
        assert updated[0]["advocacy"] == "Result 1"
        assert updated[1]["advocacy"] == "Result 2"
    
    def test_update_candidates_with_empty_results(self):
        """Test handling of empty batch results."""
        candidates = [
            {"text": "Idea 1"},
            {"text": "Idea 2"}
        ]
        batch_results = ["Result 1", ""]  # Second result is empty
        result_key = "advocacy"
        
        with patch('src.madspark.core.batch_operations_base.logger') as mock_logger:
            updated = self.batch_ops.update_candidates_with_batch_results(
                candidates, batch_results, result_key
            )
            
            assert updated[0]["advocacy"] == "Result 1"
            assert updated[1]["advocacy"] == "No advocacy generated"
            mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_batch_with_timeout_async_success(self):
        """Test successful async batch operation with timeout."""
        # Mock the batch function
        mock_batch_func = Mock(return_value="batch_result")
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS', 
                       {'test_batch': mock_batch_func}):
            result = await self.batch_ops.run_batch_with_timeout(
                'test_batch', 'arg1', 'arg2', timeout=30, is_async=True
            )
            
            assert result == "batch_result"
            mock_batch_func.assert_called_once_with('arg1', 'arg2')
    
    @pytest.mark.asyncio 
    async def test_run_batch_with_timeout_async_timeout(self):
        """Test async batch operation timeout handling."""
        # Mock a slow batch function
        def slow_batch_func(*args):
            import time
            time.sleep(2)  # Simulate slow operation
            return "result"
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'slow_batch': slow_batch_func}):
            with pytest.raises(asyncio.TimeoutError):
                await self.batch_ops.run_batch_with_timeout(
                    'slow_batch', timeout=0.1, is_async=True
                )
    
    def test_run_batch_with_timeout_sync_success(self):
        """Test successful sync batch operation."""
        mock_batch_func = Mock(return_value="sync_result")
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'sync_batch': mock_batch_func}):
            result = asyncio.run(self.batch_ops.run_batch_with_timeout(
                'sync_batch', 'arg1', timeout=30, is_async=False
            ))
            
            assert result == "sync_result"
            mock_batch_func.assert_called_once_with('arg1')
    
    def test_run_batch_with_timeout_sync_timeout(self):
        """Test sync batch operation timeout handling."""
        def slow_sync_func(*args):
            import time
            time.sleep(2)
            return "result"
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'slow_sync': slow_sync_func}):
            
            with pytest.raises(FutureTimeoutError):
                asyncio.run(self.batch_ops.run_batch_with_timeout(
                    'slow_sync', timeout=0.1, is_async=False
                ))
    
    @pytest.mark.asyncio
    async def test_run_batch_with_timeout_unknown_function(self):
        """Test handling of unknown batch function."""
        with pytest.raises(ValueError, match="Unknown batch function"):
            await self.batch_ops.run_batch_with_timeout('unknown_batch')


class TestBatchOperationsIntegration:
    """Integration tests for batch operations with real batch functions."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.batch_ops = BatchOperationsBase()
    
    @pytest.mark.asyncio
    async def test_advocacy_batch_integration(self):
        """Test integration with real advocacy batch function."""
        # Mock the advocacy batch function to simulate real behavior
        mock_advocacy_batch = Mock(return_value=[
            "Strong advocacy for idea 1", 
            "Strong advocacy for idea 2"
        ])
        
        candidates = [
            {"text": "Solar panels", "critique": "Good but expensive"},
            {"text": "Wind turbines", "critique": "Effective but noisy"}
        ]
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'advocate_ideas_batch': mock_advocacy_batch}):
            
            # Prepare input
            advocacy_input = self.batch_ops.prepare_advocacy_input(candidates)
            
            # Run batch operation
            batch_results = await self.batch_ops.run_batch_with_timeout(
                'advocate_ideas_batch', advocacy_input, "renewable energy", 0.7
            )
            
            # Update candidates
            updated = self.batch_ops.update_candidates_with_batch_results(
                candidates, batch_results, 'advocacy'
            )
            
            # Verify results
            assert updated[0]["advocacy"] == "Strong advocacy for idea 1"
            assert updated[1]["advocacy"] == "Strong advocacy for idea 2"
            mock_advocacy_batch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_skepticism_batch_integration(self):
        """Test integration with real skepticism batch function."""
        mock_skepticism_batch = Mock(return_value=[
            "Critical analysis of idea 1",
            "Critical analysis of idea 2"
        ])
        
        candidates = [
            {"text": "Idea 1", "critique": "Critique 1", "advocacy": "Advocacy 1"},
            {"text": "Idea 2", "critique": "Critique 2", "advocacy": "Advocacy 2"}
        ]
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'criticize_ideas_batch': mock_skepticism_batch}):
            
            skepticism_input = self.batch_ops.prepare_skepticism_input(candidates)
            batch_results = await self.batch_ops.run_batch_with_timeout(
                'criticize_ideas_batch', skepticism_input, "theme", 0.8
            )
            updated = self.batch_ops.update_candidates_with_batch_results(
                candidates, batch_results, 'skepticism'
            )
            
            assert updated[0]["skepticism"] == "Critical analysis of idea 1"
            assert updated[1]["skepticism"] == "Critical analysis of idea 2"
    
    @pytest.mark.asyncio
    async def test_improvement_batch_integration(self):
        """Test integration with real improvement batch function."""
        mock_improvement_batch = Mock(return_value=[
            "Improved version of idea 1",
            "Improved version of idea 2"
        ])
        
        candidates = [
            {
                "text": "Original 1", 
                "critique": "Critique 1",
                "advocacy": "Advocacy 1", 
                "skepticism": "Skepticism 1"
            },
            {
                "text": "Original 2",
                "critique": "Critique 2", 
                "advocacy": "Advocacy 2",
                "skepticism": "Skepticism 2"
            }
        ]
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS',
                       {'improve_ideas_batch': mock_improvement_batch}):
            
            improvement_input = self.batch_ops.prepare_improvement_input(candidates)
            batch_results = await self.batch_ops.run_batch_with_timeout(
                'improve_ideas_batch', improvement_input, "theme", "context", 0.7
            )
            updated = self.batch_ops.update_candidates_with_batch_results(
                candidates, batch_results, 'improved_text'
            )
            
            assert updated[0]["improved_text"] == "Improved version of idea 1"
            assert updated[1]["improved_text"] == "Improved version of idea 2"


@pytest.mark.slow
class TestBatchOperationsPerformance:
    """Performance tests for batch operations."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.batch_ops = BatchOperationsBase()
    
    @pytest.mark.asyncio
    async def test_concurrent_batch_operations(self):
        """Test concurrent execution of multiple batch operations."""
        import time
        
        # Mock batch functions with delay
        def mock_batch_1(*args):
            time.sleep(0.1)
            return ["result1_1", "result1_2"]
        
        def mock_batch_2(*args):
            time.sleep(0.1) 
            return ["result2_1", "result2_2"]
        
        candidates = [
            {"text": "Idea 1", "critique": "Critique 1"},
            {"text": "Idea 2", "critique": "Critique 2"}
        ]
        
        with patch.dict('src.madspark.core.batch_operations_base.BATCH_FUNCTIONS', {
            'batch_1': mock_batch_1,
            'batch_2': mock_batch_2
        }):
            
            start_time = time.time()
            
            # Run operations concurrently
            advocacy_task = self.batch_ops.run_batch_with_timeout('batch_1', candidates)
            skepticism_task = self.batch_ops.run_batch_with_timeout('batch_2', candidates)
            
            advocacy_results, skepticism_results = await asyncio.gather(
                advocacy_task, skepticism_task
            )
            
            elapsed = time.time() - start_time
            
            # Should complete in ~0.1s (concurrent) not ~0.2s (sequential)
            # Allow more time in CI environments
            assert elapsed < 0.25, f"Concurrent execution too slow: {elapsed}s"
            assert advocacy_results == ["result1_1", "result1_2"]
            assert skepticism_results == ["result2_1", "result2_2"]


class TestAgentResponseNormalization:
    """Test suite for agent response normalization (Phase 3, Task 3)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.batch_ops = BatchOperationsBase()

    def test_normalize_pydantic_model_to_dict(self):
        """Test normalization of Pydantic model responses to dict."""
        from madspark.schemas.generation import ImprovementResponse

        # Create Pydantic model response
        pydantic_response = ImprovementResponse(
            improved_title="Test Title",
            improved_description="Test Description",
            key_improvements=["Improvement 1", "Improvement 2"],
            implementation_steps=["Step 1", "Step 2"],
            differentiators=["Unique feature 1"]
        )

        # Normalize to dict
        result = self.batch_ops.normalize_agent_response(pydantic_response, expected_type="dict")

        assert isinstance(result, dict)
        assert result["improved_title"] == "Test Title"
        assert result["improved_description"] == "Test Description"
        assert len(result["key_improvements"]) == 2

    def test_normalize_json_string_to_dict(self):
        """Test normalization of JSON string responses to dict."""
        import json

        # JSON string response
        json_response = json.dumps({
            "score": 8.5,
            "comment": "Good idea with strong potential",
            "strengths": ["Innovative", "Scalable"],
            "weaknesses": ["High cost"]
        })

        # Normalize to dict
        result = self.batch_ops.normalize_agent_response(json_response, expected_type="dict")

        assert isinstance(result, dict)
        assert result["score"] == 8.5
        assert result["comment"] == "Good idea with strong potential"
        assert len(result["strengths"]) == 2

    def test_normalize_dict_passthrough(self):
        """Test that dict responses are passed through unchanged."""
        dict_response = {
            "idea": "Test idea",
            "score": 7.0,
            "evaluation": "Good potential"
        }

        # Normalize (should pass through)
        result = self.batch_ops.normalize_agent_response(dict_response, expected_type="dict")

        assert isinstance(result, dict)
        assert result == dict_response
        assert result["score"] == 7.0

    def test_normalize_list_of_dicts(self):
        """Test normalization of list responses."""
        list_response = [
            {"idea": "Idea 1", "score": 7.5},
            {"idea": "Idea 2", "score": 9.0}
        ]

        # Normalize to list
        result = self.batch_ops.normalize_agent_response(list_response, expected_type="list")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["score"] == 7.5
        assert result[1]["score"] == 9.0

    def test_normalize_list_of_pydantic_models(self):
        """Test normalization of list containing Pydantic models."""
        from madspark.schemas.evaluation import DimensionScore

        # Create list of Pydantic models
        pydantic_list = [
            DimensionScore(score=8.0, reasoning="Good"),
            DimensionScore(score=9.5, reasoning="Excellent")
        ]

        # Normalize to list of dicts
        result = self.batch_ops.normalize_agent_response(pydantic_list, expected_type="list")

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert result[0]["score"] == 8.0
        assert result[1]["score"] == 9.5

    def test_normalize_handles_none_gracefully(self):
        """Test that None responses are handled gracefully."""
        # Test None with different expected types
        assert self.batch_ops.normalize_agent_response(None, expected_type="dict") == {}
        assert self.batch_ops.normalize_agent_response(None, expected_type="list") == []
        assert self.batch_ops.normalize_agent_response(None, expected_type="str") == ""

    def test_normalize_invalid_json_string(self):
        """Test handling of invalid JSON strings."""
        invalid_json = "This is not valid JSON"

        # Expected type dict - should return empty dict with warning
        result = self.batch_ops.normalize_agent_response(invalid_json, expected_type="dict")
        assert result == {}

        # Expected type str - should return as-is
        result = self.batch_ops.normalize_agent_response(invalid_json, expected_type="str")
        assert result == "This is not valid JSON"

    def test_normalize_list_to_dict_takes_first_item(self):
        """Test that list normalized to dict returns first item."""
        list_response = [
            {"score": 8.0, "comment": "First"},
            {"score": 7.0, "comment": "Second"}
        ]

        # Normalize list to dict (should take first item)
        result = self.batch_ops.normalize_agent_response(list_response, expected_type="dict")

        assert isinstance(result, dict)
        assert result["score"] == 8.0
        assert result["comment"] == "First"

    def test_normalize_empty_list_to_dict(self):
        """Test that empty list normalized to dict returns empty dict."""
        empty_list = []

        result = self.batch_ops.normalize_agent_response(empty_list, expected_type="dict")

        assert result == {}

    def test_normalize_dict_to_list_wraps_in_list(self):
        """Test that dict normalized to list is wrapped in list."""
        dict_response = {"score": 8.5, "comment": "Good"}

        result = self.batch_ops.normalize_agent_response(dict_response, expected_type="list")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["score"] == 8.5

    def test_normalize_pydantic_v1_compatibility(self):
        """Test backward compatibility with Pydantic v1 .dict() method."""
        # Create mock Pydantic v1 model (has .dict() but not .model_dump())
        class MockPydanticV1:
            def dict(self):
                return {"field1": "value1", "field2": "value2"}

        mock_v1_response = MockPydanticV1()

        result = self.batch_ops.normalize_agent_response(mock_v1_response, expected_type="dict")

        assert isinstance(result, dict)
        assert result["field1"] == "value1"

    def test_normalize_dict_to_json_string(self):
        """Test normalization of dict to JSON string."""
        import json

        dict_response = {"score": 8.0, "comment": "Good idea"}

        result = self.batch_ops.normalize_agent_response(dict_response, expected_type="str")

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["score"] == 8.0

    def test_normalize_list_to_json_string(self):
        """Test normalization of list to JSON string."""
        import json

        list_response = [{"score": 8.0}, {"score": 9.0}]

        result = self.batch_ops.normalize_agent_response(list_response, expected_type="str")

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["score"] == 8.0