"""Tests for types and logging utilities."""
import pytest
from madspark.core.types_and_logging import normalize_candidate_data
from madspark.utils.errors import ValidationError

class TestNormalizeCandidateData:
    """Tests for normalize_candidate_data function."""

    def test_normalize_candidate_data_populates_text_from_idea(self):
        """Test that 'text' is populated from 'idea'."""
        candidate = {"idea": "test idea", "score": 5, "critique": "good"}
        normalize_candidate_data(candidate, "context")
        assert candidate["text"] == "test idea"
        assert candidate["idea"] == "test idea"

    def test_normalize_candidate_data_populates_idea_from_text(self):
        """Test that 'idea' is populated from 'text'."""
        candidate = {"text": "test idea", "score": 5, "critique": "good"}
        normalize_candidate_data(candidate, "context")
        assert candidate["idea"] == "test idea"
        assert candidate["text"] == "test idea"

    def test_normalize_candidate_data_raises_validation_error_missing_text(self):
        """Test that ValidationError is raised when neither text nor idea is present."""
        candidate = {"score": 5, "critique": "good"}
        with pytest.raises(ValidationError, match="must contain either 'text' or 'idea'"):
            normalize_candidate_data(candidate, "context")

    def test_normalize_candidate_data_populates_initial_score(self):
        """Test that 'initial_score' is populated from 'score'."""
        candidate = {"idea": "test", "score": 8}
        normalize_candidate_data(candidate, "context")
        assert candidate["initial_score"] == 8
        assert candidate["score"] == 8

    def test_normalize_candidate_data_populates_score(self):
        """Test that 'score' is populated from 'initial_score'."""
        candidate = {"idea": "test", "initial_score": 7}
        normalize_candidate_data(candidate, "context")
        assert candidate["score"] == 7
        assert candidate["initial_score"] == 7

    def test_normalize_candidate_data_defaults_score(self):
        """Test that score defaults to 0 if missing."""
        candidate = {"idea": "test"}
        normalize_candidate_data(candidate, "context")
        assert candidate["score"] == 0
        assert candidate["initial_score"] == 0

    def test_normalize_candidate_data_populates_initial_critique(self):
        """Test that 'initial_critique' is populated from 'critique'."""
        candidate = {"idea": "test", "critique": "feedback"}
        normalize_candidate_data(candidate, "context")
        assert candidate["initial_critique"] == "feedback"
        assert candidate["critique"] == "feedback"

    def test_normalize_candidate_data_populates_critique(self):
        """Test that 'critique' is populated from 'initial_critique'."""
        candidate = {"idea": "test", "initial_critique": "feedback"}
        normalize_candidate_data(candidate, "context")
        assert candidate["critique"] == "feedback"
        assert candidate["initial_critique"] == "feedback"

    def test_normalize_candidate_data_defaults_critique(self):
        """Test that critique defaults to empty string if missing."""
        candidate = {"idea": "test"}
        normalize_candidate_data(candidate, "context")
        assert candidate["critique"] == ""
        assert candidate["initial_critique"] == ""

    def test_normalize_candidate_data_preserves_context(self):
        """Test that existing context is not overwritten."""
        candidate = {"idea": "test", "context": "specific context"}
        normalize_candidate_data(candidate, "batch context")
        assert candidate["context"] == "specific context"

    def test_normalize_candidate_data_sets_context_if_missing(self):
        """Test that context is set if missing."""
        candidate = {"idea": "test"}
        normalize_candidate_data(candidate, "batch context")
        assert candidate["context"] == "batch context"
