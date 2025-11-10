"""Tests for CLI multi-modal argument parsing and integration.

Following TDD principles, these tests are written BEFORE implementation
to define the expected behavior of multi-modal CLI features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import argparse
import tempfile
from pathlib import Path


# Test fixtures
@pytest.fixture
def basic_args():
    """Create basic argument namespace for testing."""
    args = argparse.Namespace()
    args.theme = "Test Theme"
    args.constraints = "Test Constraints"
    args.verbose = False
    args.timeout = 60
    args.similarity_threshold = 0.7
    args.novelty_threshold = 0.7
    args.disable_novelty_filter = False
    args.enhanced_reasoning = False
    args.logical_inference = False
    args.top_ideas = None
    args.no_bookmark = False
    args.bookmark_file = "bookmarks.json"
    args.bookmark_tags = []
    args.export = None
    args.export_dir = "output"
    args.export_filename = None
    args.output_format = "detailed"
    args.output_mode = "detailed"
    args.output_file = None
    args.enable_cache = False
    args.batch = None
    args.batch_concurrent = 5
    args.batch_export_dir = "batch_results"
    args.interactive = False
    args.remix = False
    args.remix_ids = None
    # Multi-modal fields
    args.multimodal_urls = None
    args.multimodal_files = None
    args.multimodal_images = None
    return args


@pytest.fixture
def temp_image(tmp_path):
    """Create a temporary test image file."""
    image_file = tmp_path / "test_image.png"
    # Create a minimal valid PNG file (8-byte PNG signature)
    image_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    return str(image_file)


@pytest.fixture
def temp_pdf(tmp_path):
    """Create a temporary test PDF file."""
    pdf_file = tmp_path / "test_document.pdf"
    # Create a minimal valid PDF file
    pdf_file.write_bytes(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n' + b'\x00' * 100)
    return str(pdf_file)


@pytest.fixture
def temp_text(tmp_path):
    """Create a temporary test text file."""
    text_file = tmp_path / "test_document.txt"
    text_file.write_text("Test document content")
    return str(text_file)


# ==============================================================================
# PHASE 1: CLI Argument Parsing Tests
# ==============================================================================

class TestCLIArgumentParsing:
    """Test CLI argument parsing for multi-modal inputs."""

    def test_single_url_argument(self):
        """Test --url argument parsing with single URL."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--url", "https://example.com"
        ])

        assert args.multimodal_urls == ["https://example.com"]
        assert args.multimodal_files is None
        assert args.multimodal_images is None

    def test_multiple_urls(self):
        """Test --url argument with multiple URLs."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--url", "https://example.com",
            "--url", "https://competitor.com",
            "--url", "https://reference.org"
        ])

        assert args.multimodal_urls == [
            "https://example.com",
            "https://competitor.com",
            "https://reference.org"
        ]
        assert len(args.multimodal_urls) == 3

    def test_url_short_form(self):
        """Test -u short form for --url."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "-u", "https://example.com"
        ])

        assert args.multimodal_urls == ["https://example.com"]

    def test_single_file_argument(self):
        """Test --file argument parsing with single file."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--file", "document.pdf"
        ])

        assert args.multimodal_files == ["document.pdf"]
        assert args.multimodal_urls is None
        assert args.multimodal_images is None

    def test_multiple_files(self):
        """Test --file argument with multiple files."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--file", "doc1.pdf",
            "--file", "doc2.txt",
            "--file", "doc3.md"
        ])

        assert args.multimodal_files == ["doc1.pdf", "doc2.txt", "doc3.md"]
        assert len(args.multimodal_files) == 3

    def test_file_short_form(self):
        """Test -f short form for --file."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "-f", "document.pdf"
        ])

        assert args.multimodal_files == ["document.pdf"]

    def test_single_image_argument(self):
        """Test --image argument parsing with single image."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--image", "mockup.png"
        ])

        assert args.multimodal_images == ["mockup.png"]
        assert args.multimodal_urls is None
        assert args.multimodal_files is None

    def test_multiple_images(self):
        """Test --image argument with multiple images."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--image", "mockup1.png",
            "--image", "mockup2.jpg",
            "--image", "wireframe.jpeg"
        ])

        assert args.multimodal_images == ["mockup1.png", "mockup2.jpg", "wireframe.jpeg"]
        assert len(args.multimodal_images) == 3

    def test_image_short_form(self):
        """Test -img short form for --image."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "-img", "mockup.png"
        ])

        assert args.multimodal_images == ["mockup.png"]

    def test_combined_multimodal_inputs(self):
        """Test combining URLs, files, and images in single command."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--url", "https://example.com",
            "--file", "document.pdf",
            "--image", "mockup.png",
            "--url", "https://another.com",
            "--image", "wireframe.jpg"
        ])

        assert args.multimodal_urls == ["https://example.com", "https://another.com"]
        assert args.multimodal_files == ["document.pdf"]
        assert args.multimodal_images == ["mockup.png", "wireframe.jpg"]

    def test_multimodal_with_other_flags(self):
        """Test multi-modal arguments work alongside other CLI flags."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context",
            "--url", "https://example.com",
            "--verbose",
            "--enhanced-reasoning",
            "--file", "doc.pdf",
            "--output-format", "json"
        ])

        assert args.multimodal_urls == ["https://example.com"]
        assert args.multimodal_files == ["doc.pdf"]
        assert args.verbose is True
        assert args.enhanced_reasoning is True
        assert args.output_format == "json"

    def test_no_multimodal_arguments_backward_compatible(self):
        """Test that omitting multi-modal args maintains backward compatibility."""
        from madspark.cli.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test topic",
            "test context"
        ])

        assert args.multimodal_urls is None
        assert args.multimodal_files is None
        assert args.multimodal_images is None


# ==============================================================================
# PHASE 2: Validation Tests
# ==============================================================================

class TestMultiModalValidation:
    """Test validation of multi-modal inputs."""

    def test_valid_files_pass_validation(self, basic_args, temp_image, temp_pdf):
        """Test that valid files pass validation."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = basic_args
        args.multimodal_files = [temp_pdf]
        args.multimodal_images = [temp_image]
        args.multimodal_urls = None

        validator = WorkflowValidator(args, Mock())

        # Should not raise any exceptions
        validator._validate_multimodal_inputs()

    def test_valid_urls_pass_validation(self, basic_args):
        """Test that valid URLs pass validation."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = basic_args
        args.multimodal_urls = [
            "https://example.com",
            "http://test.org"
        ]
        args.multimodal_files = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        # Should not raise any exceptions
        validator._validate_multimodal_inputs()

    def test_nonexistent_file_fails_validation(self, basic_args):
        """Test that non-existent file raises ValidationError."""
        from madspark.cli.commands.validation import WorkflowValidator, ValidationError

        args = basic_args
        args.multimodal_files = ["/nonexistent/path/to/file.pdf"]
        args.multimodal_urls = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        with pytest.raises(ValidationError, match="File not found"):
            validator._validate_multimodal_inputs()

    def test_oversized_file_fails_validation(self, basic_args, tmp_path):
        """Test that oversized file raises ValidationError."""
        from madspark.cli.commands.validation import WorkflowValidator, ValidationError

        # Create a file larger than MAX_IMAGE_SIZE (8MB)
        large_file = tmp_path / "large_image.png"
        large_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * (9 * 1024 * 1024))

        args = basic_args
        args.multimodal_images = [str(large_file)]
        args.multimodal_files = None
        args.multimodal_urls = None

        validator = WorkflowValidator(args, Mock())

        with pytest.raises(ValidationError, match="File too large"):
            validator._validate_multimodal_inputs()

    def test_unsupported_format_fails_validation(self, basic_args, tmp_path):
        """Test that unsupported file format raises ValidationError."""
        from madspark.cli.commands.validation import WorkflowValidator, ValidationError

        # Create a file with unsupported extension
        unsupported = tmp_path / "test.xyz"
        unsupported.write_bytes(b"test content")

        args = basic_args
        args.multimodal_files = [str(unsupported)]
        args.multimodal_urls = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        with pytest.raises(ValidationError, match="Unsupported file format"):
            validator._validate_multimodal_inputs()

    def test_invalid_url_scheme_fails_validation(self, basic_args):
        """Test that invalid URL scheme raises ValidationError."""
        from madspark.cli.commands.validation import WorkflowValidator, ValidationError

        args = basic_args
        args.multimodal_urls = ["ftp://invalid.com"]
        args.multimodal_files = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        with pytest.raises(ValidationError, match="Invalid URL"):
            validator._validate_multimodal_inputs()

    def test_malformed_url_fails_validation(self, basic_args):
        """Test that malformed URL raises ValidationError."""
        from madspark.cli.commands.validation import WorkflowValidator, ValidationError

        args = basic_args
        args.multimodal_urls = ["not-a-valid-url"]
        args.multimodal_files = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        with pytest.raises(ValidationError, match="Invalid URL"):
            validator._validate_multimodal_inputs()

    def test_empty_multimodal_inputs_pass_validation(self, basic_args):
        """Test that empty/None multi-modal inputs pass validation (backward compatibility)."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = basic_args
        args.multimodal_urls = None
        args.multimodal_files = None
        args.multimodal_images = None

        validator = WorkflowValidator(args, Mock())

        # Should not raise any exceptions
        validator._validate_multimodal_inputs()

    def test_combined_valid_inputs_pass_validation(self, basic_args, temp_image, temp_pdf):
        """Test that combination of valid URLs and files pass validation."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = basic_args
        args.multimodal_urls = ["https://example.com", "http://test.org"]
        args.multimodal_files = [temp_pdf]
        args.multimodal_images = [temp_image]

        validator = WorkflowValidator(args, Mock())

        # Should not raise any exceptions
        validator._validate_multimodal_inputs()


# ==============================================================================
# PHASE 3: Integration Tests
# ==============================================================================

class TestMultiModalWorkflowIntegration:
    """Test integration of multi-modal inputs with workflow execution."""

    def test_workflow_receives_multimodal_files(self, basic_args, temp_pdf, temp_image):
        """Test that workflow receives multi-modal files correctly."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        args = basic_args
        args.multimodal_files = [temp_pdf]
        args.multimodal_images = [temp_image]
        args.multimodal_urls = None
        args.top_ideas = None  # Single idea (sync mode)

        mock_temp_manager = Mock()
        mock_results = []

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results) as mock_workflow:
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(args, Mock(), mock_temp_manager)
                executor.execute()

                # Verify workflow was called with multi-modal files
                assert mock_workflow.called
                call_kwargs = mock_workflow.call_args.kwargs

                assert 'multimodal_files' in call_kwargs
                assert call_kwargs['multimodal_files'] == [temp_pdf, temp_image]

    def test_workflow_receives_multimodal_urls(self, basic_args):
        """Test that workflow receives multi-modal URLs correctly."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        args = basic_args
        args.multimodal_urls = ["https://example.com", "https://test.org"]
        args.multimodal_files = None
        args.multimodal_images = None
        args.top_ideas = None  # Single idea (sync mode)

        mock_temp_manager = Mock()
        mock_results = []

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results) as mock_workflow:
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(args, Mock(), mock_temp_manager)
                executor.execute()

                # Verify workflow was called with multi-modal URLs
                assert mock_workflow.called
                call_kwargs = mock_workflow.call_args.kwargs

                assert 'multimodal_urls' in call_kwargs
                assert call_kwargs['multimodal_urls'] == ["https://example.com", "https://test.org"]

    def test_workflow_receives_combined_multimodal_inputs(self, basic_args, temp_pdf, temp_image):
        """Test that workflow receives combined multi-modal inputs correctly."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        args = basic_args
        args.multimodal_urls = ["https://example.com"]
        args.multimodal_files = [temp_pdf]
        args.multimodal_images = [temp_image]
        args.top_ideas = None  # Single idea (sync mode)

        mock_temp_manager = Mock()
        mock_results = []

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results) as mock_workflow:
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(args, Mock(), mock_temp_manager)
                executor.execute()

                # Verify workflow was called with all multi-modal inputs
                assert mock_workflow.called
                call_kwargs = mock_workflow.call_args.kwargs

                assert 'multimodal_files' in call_kwargs
                assert 'multimodal_urls' in call_kwargs
                # Files and images should be combined
                assert call_kwargs['multimodal_files'] == [temp_pdf, temp_image]
                assert call_kwargs['multimodal_urls'] == ["https://example.com"]

    def test_workflow_receives_none_when_no_multimodal_inputs(self, basic_args):
        """Test backward compatibility: workflow receives None when no multi-modal args."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        args = basic_args
        args.multimodal_urls = None
        args.multimodal_files = None
        args.multimodal_images = None
        args.top_ideas = None  # Single idea (sync mode)

        mock_temp_manager = Mock()
        mock_results = []

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results) as mock_workflow:
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(args, Mock(), mock_temp_manager)
                executor.execute()

                # Verify workflow was called with None for multi-modal inputs
                assert mock_workflow.called
                call_kwargs = mock_workflow.call_args.kwargs

                assert call_kwargs.get('multimodal_files') is None
                assert call_kwargs.get('multimodal_urls') is None

    def test_async_workflow_receives_multimodal_inputs(self, basic_args, temp_image):
        """Test that async workflow receives multi-modal inputs correctly."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        args = basic_args
        args.multimodal_urls = ["https://example.com"]
        args.multimodal_images = [temp_image]
        args.multimodal_files = None
        args.top_ideas = 3  # Trigger async mode

        mock_temp_manager = Mock()
        mock_results = []

        with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=3):
            with patch('madspark.cli.commands.workflow_executor.asyncio.run') as mock_async_run:
                mock_async_run.return_value = mock_results

                executor = WorkflowExecutor(args, Mock(), mock_temp_manager)
                executor.execute()

                # Verify async was called (which means async path was taken)
                mock_async_run.assert_called_once()


# ==============================================================================
# Mock Mode Compatibility Tests
# ==============================================================================

class TestMultiModalMockMode:
    """Test that multi-modal features work in mock mode (no API key)."""

    @patch('madspark.agents.idea_generator.GENAI_AVAILABLE', False)
    def test_multimodal_works_in_mock_mode(self, basic_args, temp_image):
        """Test that multi-modal inputs work when GENAI_AVAILABLE is False."""
        from madspark.agents.idea_generator import generate_ideas

        # Should not raise exceptions in mock mode
        result = generate_ideas(
            topic="test topic",
            context="test context",
            multimodal_files=[temp_image],
            multimodal_urls=["https://example.com"]
        )

        # Should return mock result
        assert isinstance(result, str)
        assert len(result) > 0
