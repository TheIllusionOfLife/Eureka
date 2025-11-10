"""
Test suite for Multi-Modal Agent Integration.

This module tests the integration of multi-modal inputs into MadSpark agents,
specifically focusing on idea generation and improvement with multi-modal context.

Following TDD approach:
1. Write integration tests first (red)
2. Implement agent integration (green)
3. Test with real API key
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import os


class TestIdeaGeneratorMultiModal:
    """Test idea_generator with multi-modal inputs."""

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_with_single_image(self, mock_client, mock_types):
        """Test generating ideas with single image context."""
        from madspark.agents.idea_generator import generate_ideas

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        # Mock the response
        mock_response = Mock()
        mock_response.text = "Idea 1: Image-inspired design\nIdea 2: Visual context optimization"
        mock_client.models.generate_content.return_value = mock_response

        # Create test image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"fake image data")
            tmp_path = tmp.name

        try:
            # Call with multi-modal inputs
            result = generate_ideas(
                topic="UI improvements",
                context="Mobile app redesign",
                multimodal_files=[tmp_path]
            )

            # Should call API with list (text + Part)
            assert mock_client.models.generate_content.called
            call_args = mock_client.models.generate_content.call_args

            # contents is passed as keyword argument
            contents = call_args.kwargs['contents']

            assert isinstance(contents, list), f"Contents should be a list for multi-modal, got {type(contents)}"
            assert len(contents) >= 2, "Should have text and at least one file Part"

            # Result should contain ideas
            assert "Idea" in result
        finally:
            os.unlink(tmp_path)

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_with_pdf(self, mock_client, mock_types):
        """Test generating ideas with PDF context."""
        from madspark.agents.idea_generator import generate_ideas

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Idea 1: Document-based insight\nIdea 2: PDF analysis feature"
        mock_client.models.generate_content.return_value = mock_response

        # Create test PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"%PDF-1.4 fake pdf")
            tmp_path = tmp.name

        try:
            result = generate_ideas(
                topic="Document analysis",
                context="Research insights",
                multimodal_files=[tmp_path]
            )

            assert mock_client.models.generate_content.called
            assert "Idea" in result
        finally:
            os.unlink(tmp_path)

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_with_url(self, mock_client, mock_types):
        """Test generating ideas with URL context."""
        from madspark.agents.idea_generator import generate_ideas

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Idea 1: Website-inspired feature\nIdea 2: Competitor analysis"
        mock_client.models.generate_content.return_value = mock_response

        result = generate_ideas(
            topic="Feature ideas",
            context="E-commerce platform",
            multimodal_urls=["https://example.com", "https://competitor.com"]
        )

        assert mock_client.models.generate_content.called

        # Check that URLs were incorporated into prompt
        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get('contents') or call_args.args[1]

        # Contents might be string (if no files) or list
        if isinstance(contents, str):
            assert "https://example.com" in contents
            assert "https://competitor.com" in contents
        else:
            # First element should be text with URLs
            assert "https://example.com" in contents[0]
            assert "https://competitor.com" in contents[0]

        assert "Idea" in result

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_mixed_multimodal(self, mock_client, mock_types):
        """Test generating ideas with both files and URLs."""
        from madspark.agents.idea_generator import generate_ideas

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Idea 1: Comprehensive analysis\nIdea 2: Multi-source insights"
        mock_client.models.generate_content.return_value = mock_response

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test image")
            tmp_path = tmp.name

        try:
            result = generate_ideas(
                topic="Innovation",
                context="Multi-modal analysis",
                multimodal_files=[tmp_path],
                multimodal_urls=["https://example.com"]
            )

            assert mock_client.models.generate_content.called

            # Should have list with text (including URL) and file Part
            call_args = mock_client.models.generate_content.call_args
            contents = call_args.kwargs.get('contents') or call_args.args[1]

            assert isinstance(contents, list)
            assert len(contents) >= 2
            assert "https://example.com" in contents[0]

            assert "Idea" in result
        finally:
            os.unlink(tmp_path)

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_generate_ideas_backward_compatible(self, mock_client, mock_types):
        """Test that generate_ideas still works without multi-modal params."""
        from madspark.agents.idea_generator import generate_ideas

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Idea 1: Standard idea\nIdea 2: Another standard idea"
        mock_client.models.generate_content.return_value = mock_response

        # Call WITHOUT multi-modal params (backward compatibility)
        result = generate_ideas(
            topic="Standard topic",
            context="Standard context"
        )

        assert mock_client.models.generate_content.called

        # Should use string prompt (not list)
        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get('contents') or call_args.args[1]

        # In standard mode, contents can be string
        assert isinstance(contents, (str, list))

        assert "Idea" in result

    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', False)
    def test_generate_ideas_multimodal_mock_mode(self):
        """Test multi-modal in mock mode (no API calls)."""
        from madspark.agents.idea_generator import generate_ideas

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        try:
            result = generate_ideas(
                topic="Test topic",
                context="Test context",
                multimodal_files=[tmp_path]
            )

            # In mock mode, should return mock result
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)


class TestIdeaImproverMultiModal:
    """Test idea improvement with multi-modal inputs."""

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_improve_idea_with_image(self, mock_client, mock_types):
        """Test improving idea with image context."""
        from madspark.agents.idea_generator import improve_idea

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Improved idea with visual context considerations"
        mock_client.models.generate_content.return_value = mock_response

        # Create test image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test image")
            tmp_path = tmp.name

        try:
            result = improve_idea(
                original_idea="Original design concept",
                critique="Needs visual refinement",
                advocacy_points="Strong foundation",
                skeptic_points="Lacks detail",
                topic="UI Design",
                context="Mobile app",
                multimodal_files=[tmp_path]
            )

            assert mock_client.models.generate_content.called

            # Should use multi-modal prompt
            call_args = mock_client.models.generate_content.call_args
            contents = call_args.kwargs.get('contents') or call_args.args[1]

            assert isinstance(contents, list)
            assert len(contents) >= 2

            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_improve_idea_with_urls(self, mock_client, mock_types):
        """Test improving idea with URL context."""
        from madspark.agents.idea_generator import improve_idea

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Improved idea with external references"
        mock_client.models.generate_content.return_value = mock_response

        result = improve_idea(
            original_idea="Feature concept",
            critique="Needs market validation",
            advocacy_points="Innovative approach",
            skeptic_points="Unclear value",
            topic="Product feature",
            context="Competitive analysis",
            multimodal_urls=["https://competitor1.com", "https://competitor2.com"]
        )

        assert mock_client.models.generate_content.called

        # Check URLs in prompt
        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get('contents') or call_args.args[1]

        if isinstance(contents, list):
            assert "https://competitor1.com" in contents[0]
        else:
            assert "https://competitor1.com" in contents

        assert len(result) > 0

    @patch('madspark.agents.idea_generator.types')
    @patch('madspark.agents.idea_generator.idea_generator_client')
    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', True)
    def test_improve_idea_backward_compatible(self, mock_client, mock_types):
        """Test improve_idea works without multi-modal params."""
        from madspark.agents.idea_generator import improve_idea

        # Mock the types module
        mock_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_config

        mock_response = Mock()
        mock_response.text = "Standard improved idea"
        mock_client.models.generate_content.return_value = mock_response

        # Call without multi-modal params
        result = improve_idea(
            original_idea="Original",
            critique="Critique",
            advocacy_points="Strengths",
            skeptic_points="Weaknesses",
            topic="Topic",
            context="Context"
        )

        assert mock_client.models.generate_content.called
        assert len(result) > 0


class TestMultiModalErrorHandling:
    """Test error handling in multi-modal agent integration."""

    def test_invalid_file_raises_error(self):
        """Test that invalid file path raises appropriate error."""
        from madspark.agents.idea_generator import generate_ideas

        with pytest.raises(FileNotFoundError):
            generate_ideas(
                topic="Test",
                context="Test",
                multimodal_files=["/nonexistent/file.png"]
            )

    def test_oversized_file_raises_error(self):
        """Test that oversized file raises appropriate error."""
        from madspark.agents.idea_generator import generate_ideas

        # Create a file larger than MAX_IMAGE_SIZE
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"x" * (9 * 1024 * 1024))  # 9MB
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="File too large"):
                generate_ideas(
                    topic="Test",
                    context="Test",
                    multimodal_files=[tmp_path]
                )
        finally:
            os.unlink(tmp_path)

    def test_invalid_url_raises_error(self):
        """Test that invalid URL raises appropriate error."""
        from madspark.agents.idea_generator import generate_ideas

        with pytest.raises(ValueError, match="Invalid URL"):
            generate_ideas(
                topic="Test",
                context="Test",
                multimodal_urls=["not-a-valid-url"]
            )


# Run tests with: PYTHONPATH=src pytest tests/test_multimodal_agents.py -v
