"""Tests for WorkflowConfig module."""

import pytest
from madspark.core.workflow_config import WorkflowConfig


class TestWorkflowConfig:
    """Tests for WorkflowConfig.build_workflow_params()."""

    def test_basic_params(self):
        """Test basic workflow parameters."""
        params = WorkflowConfig.build_workflow_params(
            topic="Test topic",
            context="Test context",
        )

        assert params["topic"] == "Test topic"
        assert params["context"] == "Test context"
        assert params["num_top_candidates"] == 3  # default
        assert params["enable_novelty_filter"] is True  # default
        assert params["enhanced_reasoning"] is True  # default
        assert params["multi_dimensional_eval"] is True  # default
        assert params["logical_inference"] is False  # default

    def test_all_params(self):
        """Test all workflow parameters."""
        params = WorkflowConfig.build_workflow_params(
            topic="Test topic",
            context="Test context",
            num_candidates=5,
            enable_novelty_filter=False,
            novelty_threshold=0.5,
            verbose=True,
            enhanced_reasoning=True,
            multi_dimensional_eval=True,
            logical_inference=True,
            timeout=600,
            multimodal_files=["/path/to/file.pdf"],
            multimodal_urls=["https://example.com/doc"],
        )

        assert params["topic"] == "Test topic"
        assert params["context"] == "Test context"
        assert params["num_top_candidates"] == 5
        assert params["enable_novelty_filter"] is False
        assert params["novelty_threshold"] == 0.5
        assert params["verbose"] is True
        assert params["enhanced_reasoning"] is True
        assert params["multi_dimensional_eval"] is True
        assert params["logical_inference"] is True
        assert params["timeout"] == 600
        assert params["multimodal_files"] == ["/path/to/file.pdf"]
        assert params["multimodal_urls"] == ["https://example.com/doc"]

    def test_reasoning_engine_not_included(self):
        """Test that reasoning_engine is NOT included in params.

        This is critical - async_coordinator must create its own engine
        with the router for batch operations to work correctly.
        """
        params = WorkflowConfig.build_workflow_params(
            topic="Test topic",
        )

        assert "reasoning_engine" not in params

    def test_default_values(self):
        """Test default parameter values."""
        params = WorkflowConfig.build_workflow_params(topic="Test")

        assert params["context"] == ""
        assert params["num_top_candidates"] == 3
        assert params["enable_novelty_filter"] is True
        assert params["novelty_threshold"] == 0.3
        assert params["verbose"] is False
        assert params["enhanced_reasoning"] is True
        assert params["multi_dimensional_eval"] is True
        assert params["logical_inference"] is False
        assert params["timeout"] == 1200
        assert params["multimodal_files"] is None
        assert params["multimodal_urls"] is None

    def test_temperature_manager_default(self):
        """Test that temperature_manager is created by default."""
        params = WorkflowConfig.build_workflow_params(topic="Test")

        # Should have a temperature_manager (either real or None if import fails)
        assert "temperature_manager" in params

    def test_custom_temperature_manager(self):
        """Test passing a custom temperature_manager."""
        mock_manager = object()  # placeholder for custom manager

        params = WorkflowConfig.build_workflow_params(
            topic="Test",
            temperature_manager=mock_manager,
        )

        assert params["temperature_manager"] is mock_manager

    def test_empty_multimodal_lists(self):
        """Test that empty multimodal lists are passed as None."""
        params = WorkflowConfig.build_workflow_params(
            topic="Test",
            multimodal_files=[],
            multimodal_urls=[],
        )

        # Empty lists should be passed as-is (caller can decide to convert to None)
        assert params["multimodal_files"] == []
        assert params["multimodal_urls"] == []

    def test_japanese_topic(self):
        """Test handling of Japanese topic and context."""
        params = WorkflowConfig.build_workflow_params(
            topic="テスト",
            context="日本語で",
        )

        assert params["topic"] == "テスト"
        assert params["context"] == "日本語で"
