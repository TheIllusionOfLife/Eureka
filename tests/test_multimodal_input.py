"""
Test suite for MultiModal Input Processing.

This module tests the core multi-modal input handling functionality,
including file validation, Part creation, and multi-modal prompt building.

Following TDD approach:
1. Write comprehensive tests first
2. Verify tests fail (red)
3. Implement functionality (green)
4. Refactor while keeping tests passing

Test coverage goals: 90%+ for critical paths
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Optional
import tempfile
import os


class TestMultiModalInputValidation:
    """Test file validation logic."""

    def test_validate_file_exists(self):
        """Test that validation checks file existence."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Non-existent file should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="File not found"):
            mm_input.validate_file("/nonexistent/file.png")

    def test_validate_file_size_within_limit(self):
        """Test file size validation - file within limit should pass."""
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig

        mm_input = MultiModalInput()

        # Create a small test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"x" * 100)  # 100 bytes - well under 8MB limit
            tmp_path = tmp.name

        try:
            # Should not raise any exception
            mm_input.validate_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_size_exceeds_image_limit(self):
        """Test file size validation - oversized image should fail."""
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig

        mm_input = MultiModalInput()

        # Create a file larger than MAX_IMAGE_SIZE (8MB)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            # Write 9MB of data
            tmp.write(b"x" * (9 * 1024 * 1024))
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="File too large"):
                mm_input.validate_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_size_exceeds_pdf_limit(self):
        """Test file size validation - oversized PDF should fail."""
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig

        mm_input = MultiModalInput()

        # Create a file larger than MAX_PDF_SIZE (40MB)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            # Write 41MB of data
            tmp.write(b"x" * (41 * 1024 * 1024))
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="File too large"):
                mm_input.validate_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_unsupported_format(self):
        """Test format validation - unsupported file type should fail."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create a file with unsupported extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                mm_input.validate_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_validate_file_supported_image_formats(self):
        """Test that all supported image formats are accepted."""
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig

        mm_input = MultiModalInput()
        supported_formats = MultiModalConfig.SUPPORTED_IMAGE_FORMATS

        for ext in supported_formats:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(b"test image data")
                tmp_path = tmp.name

            try:
                # Should not raise exception
                mm_input.validate_file(tmp_path)
            finally:
                os.unlink(tmp_path)

    def test_validate_file_supported_doc_formats(self):
        """Test that all supported document formats are accepted."""
        from madspark.utils.multimodal_input import MultiModalInput
        from madspark.config.execution_constants import MultiModalConfig

        mm_input = MultiModalInput()
        supported_formats = MultiModalConfig.SUPPORTED_DOC_FORMATS

        for ext in supported_formats:
            if ext in ['doc', 'docx']:  # Skip MS Office formats for now
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(b"test document data")
                tmp_path = tmp.name

            try:
                # Should not raise exception
                mm_input.validate_file(tmp_path)
            finally:
                os.unlink(tmp_path)


class TestMultiModalInputPartCreation:
    """Test Part object creation from files."""

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_process_file_mock_mode(self):
        """Test file processing in mock mode returns MockPart."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test image")
            tmp_path = tmp.name

        try:
            part = mm_input.process_file(tmp_path)

            # In mock mode, should return MockPart
            assert hasattr(part, 'source')
            assert hasattr(part, 'mime_type')
            assert tmp_path in str(part.source)
        finally:
            os.unlink(tmp_path)

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', True)
    @patch('madspark.utils.multimodal_input.types')
    def test_process_file_real_mode(self, mock_types):
        """Test file processing in real mode creates actual Part."""
        from madspark.utils.multimodal_input import MultiModalInput

        # Mock types.Part.from_bytes to return a fake Part
        mock_part = Mock()
        mock_types.Part.from_bytes.return_value = mock_part

        mm_input = MultiModalInput()

        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test image")
            tmp_path = tmp.name

        try:
            part = mm_input.process_file(tmp_path)

            # Should call Part.from_bytes with correct args
            mock_types.Part.from_bytes.assert_called_once()
            call_kwargs = mock_types.Part.from_bytes.call_args.kwargs
            assert 'data' in call_kwargs
            assert 'mime_type' in call_kwargs
            assert call_kwargs['mime_type'] == 'image/png'

            # Should return the mocked Part
            assert part == mock_part
        finally:
            os.unlink(tmp_path)

    def test_detect_mime_type_images(self):
        """Test MIME type detection for various image formats."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        test_cases = [
            ('test.png', 'image/png'),
            ('test.jpg', 'image/jpeg'),
            ('test.jpeg', 'image/jpeg'),
            ('test.webp', 'image/webp'),
            ('test.gif', 'image/gif'),
            ('test.bmp', 'image/bmp'),
        ]

        for filename, expected_mime in test_cases:
            mime_type = mm_input._detect_mime_type(filename)
            assert mime_type == expected_mime, f"Failed for {filename}"

    def test_detect_mime_type_documents(self):
        """Test MIME type detection for various document formats."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        test_cases = [
            ('test.pdf', 'application/pdf'),
            ('test.txt', 'text/plain'),
            ('test.md', 'text/markdown'),
        ]

        for filename, expected_mime in test_cases:
            mime_type = mm_input._detect_mime_type(filename)
            assert mime_type == expected_mime, f"Failed for {filename}"


class TestMultiModalInputPromptBuilding:
    """Test multi-modal prompt construction."""

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_build_prompt_text_only(self):
        """Test building prompt with text only (no files/URLs)."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Text-only prompt
        result = mm_input.build_multimodal_prompt(
            text_prompt="Generate innovative ideas",
            files=None,
            urls=None
        )

        # Should return the text as-is
        assert isinstance(result, str)
        assert result == "Generate innovative ideas"

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_build_prompt_with_single_file(self):
        """Test building prompt with one file."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        try:
            result = mm_input.build_multimodal_prompt(
                text_prompt="Analyze this image",
                files=[tmp_path],
                urls=None
            )

            # Should return a list with text and Part
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0] == "Analyze this image"
            # Second element should be a Part (or MockPart in mock mode)
            assert hasattr(result[1], 'mime_type')
        finally:
            os.unlink(tmp_path)

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_build_prompt_with_multiple_files(self):
        """Test building prompt with multiple files."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create test files
        files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(f"test{i}".encode())
            tmp.close()
            files.append(tmp.name)

        try:
            result = mm_input.build_multimodal_prompt(
                text_prompt="Compare these images",
                files=files,
                urls=None
            )

            # Should return list: [text, part1, part2, part3]
            assert isinstance(result, list)
            assert len(result) == 4  # 1 text + 3 files
            assert result[0] == "Compare these images"
            for i in range(1, 4):
                assert hasattr(result[i], 'mime_type')
        finally:
            for f in files:
                os.unlink(f)

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_build_prompt_with_urls(self):
        """Test building prompt with URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        urls = ["https://example.com", "https://test.org"]

        result = mm_input.build_multimodal_prompt(
            text_prompt="Analyze these websites",
            files=None,
            urls=urls
        )

        # URLs should be incorporated into the text prompt
        # (since Gemini can't fetch URLs, we add them as context)
        assert isinstance(result, str)
        assert "https://example.com" in result
        assert "https://test.org" in result
        assert "Analyze these websites" in result

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_build_prompt_mixed_files_and_urls(self):
        """Test building prompt with both files and URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        try:
            urls = ["https://example.com"]

            result = mm_input.build_multimodal_prompt(
                text_prompt="Comprehensive analysis",
                files=[tmp_path],
                urls=urls
            )

            # Should return list with enhanced text and file Part
            assert isinstance(result, list)
            assert len(result) == 2
            # First element should be text with URL context
            assert "https://example.com" in result[0]
            assert "Comprehensive analysis" in result[0]
            # Second element should be file Part
            assert hasattr(result[1], 'mime_type')
        finally:
            os.unlink(tmp_path)


class TestMultiModalInputErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_file_path(self):
        """Test handling of empty file path."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        with pytest.raises(ValueError, match="File path cannot be empty"):
            mm_input.process_file("")

    def test_none_file_path(self):
        """Test handling of None file path."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        with pytest.raises(ValueError, match="File path cannot be None"):
            mm_input.process_file(None)

    def test_invalid_url_format(self):
        """Test validation of URL format."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Unsupported scheme
            "javascript:alert(1)",  # Security risk
            "",
            None
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Invalid URL"):
                mm_input.validate_url(url)

    def test_valid_url_formats(self):
        """Test acceptance of valid URL formats."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        valid_urls = [
            "https://example.com",
            "http://test.org",
            "https://sub.domain.com/path?query=value",
            "https://example.com:8080/path"
        ]

        for url in valid_urls:
            # Should not raise exception
            mm_input.validate_url(url)

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_large_file_warning(self, caplog):
        """Test that large files trigger warning logs."""
        import logging
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create a file larger than 5MB (warning threshold)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(b"x" * (6 * 1024 * 1024))  # 6MB
            tmp_path = tmp.name

        try:
            with caplog.at_level(logging.WARNING):
                mm_input.process_file(tmp_path)

            # Should have logged a warning about processing time
            assert any("large file" in record.message.lower() or "processing time" in record.message.lower()
                      for record in caplog.records)
        finally:
            os.unlink(tmp_path)


class TestMultiModalInputIntegration:
    """Integration tests for complete workflows."""

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_end_to_end_single_image(self):
        """Test complete flow: validate → process → build prompt."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create test image
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(b"fake jpeg data")
            tmp_path = tmp.name

        try:
            # Step 1: Validate
            mm_input.validate_file(tmp_path)

            # Step 2: Process
            part = mm_input.process_file(tmp_path)
            assert part is not None

            # Step 3: Build prompt
            result = mm_input.build_multimodal_prompt(
                text_prompt="Describe this",
                files=[tmp_path],
                urls=None
            )

            assert isinstance(result, list)
            assert len(result) == 2
        finally:
            os.unlink(tmp_path)

    @patch('madspark.utils.multimodal_input.GENAI_AVAILABLE', False)
    def test_end_to_end_mixed_inputs(self):
        """Test complete flow with mixed inputs (file + URL)."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Create test PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"fake pdf content")
            tmp_path = tmp.name

        try:
            # Validate URL
            mm_input.validate_url("https://example.com")

            # Validate file
            mm_input.validate_file(tmp_path)

            # Build prompt with both
            result = mm_input.build_multimodal_prompt(
                text_prompt="Analyze document and website",
                files=[tmp_path],
                urls=["https://example.com"]
            )

            assert isinstance(result, list)
            assert len(result) == 2
            # Text should include URL
            assert "https://example.com" in result[0]
            # Should have PDF Part
            assert hasattr(result[1], 'mime_type')
        finally:
            os.unlink(tmp_path)


# Run tests with: PYTHONPATH=src pytest tests/test_multimodal_input.py -v
