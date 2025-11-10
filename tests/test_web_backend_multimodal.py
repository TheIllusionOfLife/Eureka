"""
Test suite for web backend multi-modal file upload functionality.

This module tests the FastAPI endpoints for handling multi-modal inputs
including file uploads (PDFs, images, documents) and URL validation.
"""
import pytest
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

# Mock FastAPI UploadFile if not available
try:
    from fastapi import UploadFile
    from fastapi.datastructures import UploadFile as FastAPIUploadFile
except ImportError:
    # Create mock UploadFile for testing when FastAPI not available
    class UploadFile:
        def __init__(self, filename, file=None):
            self.filename = filename
            self.file = file
            self.size = 0

    FastAPIUploadFile = UploadFile


class TestFileUploadValidation:
    """Test cases for file upload validation."""

    def test_validate_file_size_within_limit(self):
        """Test file size validation for files within limit."""
        # Create a mock file within size limit (10 MB)
        file_content = b"x" * (5 * 1024 * 1024)  # 5 MB
        mock_file = Mock()
        mock_file.size = len(file_content)
        mock_file.filename = "test.pdf"

        # Should not raise exception
        from madspark.config.execution_constants import MultiModalConfig
        assert mock_file.size <= MultiModalConfig.MAX_FILE_SIZE

    def test_validate_file_size_exceeds_limit(self):
        """Test file size validation for files exceeding limit."""
        # Create a mock file exceeding size limit
        file_size = 25 * 1024 * 1024  # 25 MB (exceeds 20 MB limit)
        mock_file = Mock()
        mock_file.size = file_size
        mock_file.filename = "large_file.pdf"

        from madspark.config.execution_constants import MultiModalConfig
        assert mock_file.size > MultiModalConfig.MAX_FILE_SIZE

    def test_validate_pdf_format(self):
        """Test validation of PDF file format."""
        from madspark.utils.multimodal_input import MultiModalInput

        # Create a temporary PDF file
        temp_dir = Path("/tmp/madspark_test")
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / f"test_{uuid.uuid4()}.pdf"

        try:
            # Write minimal PDF header
            test_file.write_bytes(b"%PDF-1.4\n")

            # Validate file
            mm_input = MultiModalInput()
            mm_input.validate_file(test_file)  # Should not raise

        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_validate_unsupported_format(self):
        """Test validation rejects unsupported file formats."""
        from madspark.utils.multimodal_input import MultiModalInput

        # Create a temporary file with unsupported extension
        temp_dir = Path("/tmp/madspark_test")
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir / f"test_{uuid.uuid4()}.exe"

        try:
            test_file.write_bytes(b"fake executable")

            # Validate file - should raise ValueError
            mm_input = MultiModalInput()
            with pytest.raises(ValueError, match="Unsupported file format"):
                mm_input.validate_file(test_file)

        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
            temp_dir.rmdir()

    def test_validate_image_format(self):
        """Test validation of image file formats."""
        from madspark.utils.multimodal_input import MultiModalInput

        # Test various image formats
        temp_dir = Path("/tmp/madspark_test")
        temp_dir.mkdir(exist_ok=True)

        image_formats = [
            ("test.png", b"\x89PNG\r\n\x1a\n"),  # PNG magic bytes
            ("test.jpg", b"\xff\xd8\xff"),       # JPEG magic bytes
            ("test.webp", b"RIFF"),               # WebP magic bytes
        ]

        for filename, magic_bytes in image_formats:
            test_file = temp_dir / f"{uuid.uuid4()}_{filename}"
            try:
                test_file.write_bytes(magic_bytes)

                # Validate file
                mm_input = MultiModalInput()
                mm_input.validate_file(test_file)  # Should not raise

            finally:
                test_file.unlink(missing_ok=True)

        temp_dir.rmdir()


class TestURLValidation:
    """Test cases for URL validation including SSRF protection."""

    def test_validate_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        url = "http://example.com/document.pdf"
        mm_input.validate_url(url)  # Should not raise

    def test_validate_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        url = "https://example.com/document.pdf"
        mm_input.validate_url(url)  # Should not raise

    def test_reject_localhost_url(self):
        """Test SSRF protection - reject localhost URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        urls = [
            ("http://localhost/secret", "(?i)localhost|loopback|internal"),
            ("http://127.0.0.1/internal", "(?i)localhost|loopback|internal|127\\.0\\.0\\.1"),
            ("http://[::1]/loopback", "(?i)Cannot resolve hostname|localhost|loopback"),
        ]

        for url, pattern in urls:
            with pytest.raises(ValueError, match=pattern):
                mm_input.validate_url(url)

    def test_reject_private_network_url(self):
        """Test SSRF protection - reject private network URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        urls = [
            "http://192.168.1.1/admin",
            "http://10.0.0.1/internal",
            "http://172.16.0.1/private",
        ]

        for url in urls:
            with pytest.raises(ValueError, match="(?i)private|internal"):
                mm_input.validate_url(url)

    def test_reject_file_protocol_url(self):
        """Test rejection of file:// protocol URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        url = "file:///etc/passwd"

        with pytest.raises(ValueError, match="(?i)unsupported|file protocol"):
            mm_input.validate_url(url)

    def test_reject_ftp_protocol_url(self):
        """Test rejection of FTP protocol URLs."""
        from madspark.utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()
        url = "ftp://example.com/file"

        with pytest.raises(ValueError, match="(?i)unsupported|ftp"):
            mm_input.validate_url(url)


class TestSaveUploadFile:
    """Test cases for save_upload_file helper function."""

    def test_save_valid_pdf(self, mock_upload_file, temp_upload_dir):
        """Test saving a valid PDF file."""
        # Import the helper function
        import sys
        from pathlib import Path
        # Add web/backend directory dynamically
        backend_path = Path(__file__).parent.parent / 'web' / 'backend'
        sys.path.insert(0, str(backend_path))
        from main import save_upload_file

        # Save the file
        saved_path = save_upload_file(mock_upload_file)

        # Verify file exists
        assert saved_path.exists()
        assert saved_path.parent == Path("/tmp/madspark_uploads")
        assert "test.pdf" in saved_path.name

        # Cleanup
        saved_path.unlink(missing_ok=True)

    def test_save_rejects_oversized_file(self, temp_upload_dir):
        """Test that save_upload_file rejects files exceeding size limit."""
        from madspark.config.execution_constants import MultiModalConfig
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent.parent / 'web' / 'backend'
        sys.path.insert(0, str(backend_path))
        from main import save_upload_file

        # Create oversized file
        file_content = b"x" * (MultiModalConfig.MAX_FILE_SIZE + 1000)
        file = BytesIO(file_content)

        upload_file = UploadFile(filename="large.pdf", file=file)
        upload_file.size = len(file_content)

        # Should raise HTTPException(413)
        try:
            from fastapi import HTTPException
        except ImportError:
            pytest.skip("FastAPI not available")

        with pytest.raises(HTTPException) as exc_info:
            save_upload_file(upload_file)

        assert exc_info.value.status_code == 413

    def test_save_creates_unique_filename(self, mock_upload_file, temp_upload_dir):
        """Test that save_upload_file creates unique filenames."""
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent.parent / 'web' / 'backend'
        sys.path.insert(0, str(backend_path))
        from main import save_upload_file

        # Reset file pointer
        mock_upload_file.file.seek(0)
        path1 = save_upload_file(mock_upload_file)

        # Create second upload with same filename
        file2 = BytesIO(b"%PDF-1.4\nTest PDF content 2")
        upload_file2 = UploadFile(filename="test.pdf", file=file2)
        upload_file2.size = len(file2.getvalue())

        path2 = save_upload_file(upload_file2)

        # Verify different paths
        assert path1 != path2
        assert path1.name != path2.name

        # Cleanup
        path1.unlink(missing_ok=True)
        path2.unlink(missing_ok=True)

    def test_save_validates_file_format(self, temp_upload_dir):
        """Test that save_upload_file validates file format."""
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent.parent / 'web' / 'backend'
        sys.path.insert(0, str(backend_path))
        from main import save_upload_file

        # Create file with invalid extension
        file_content = b"fake executable"
        file = BytesIO(file_content)

        upload_file = UploadFile(filename="malware.exe", file=file)
        upload_file.size = len(file_content)

        # Should raise HTTPException(400) for invalid format
        try:
            from fastapi import HTTPException
        except ImportError:
            pytest.skip("FastAPI not available")

        with pytest.raises(HTTPException) as exc_info:
            save_upload_file(upload_file)

        assert exc_info.value.status_code == 400
        assert "validation failed" in str(exc_info.value.detail).lower()

    def test_cleanup_temp_file_on_error(self, temp_upload_dir):
        """Test that temp files are cleaned up on error."""
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent.parent / 'web' / 'backend'
        sys.path.insert(0, str(backend_path))
        from main import save_upload_file

        # Create file with invalid extension that will fail validation
        file_content = b"fake executable"
        file = BytesIO(file_content)

        upload_file = UploadFile(filename="malware.exe", file=file)
        upload_file.size = len(file_content)

        # Try to save (should fail)
        try:
            from fastapi import HTTPException
        except ImportError:
            pytest.skip("FastAPI not available")

        try:
            save_upload_file(upload_file)
        except HTTPException:
            pass  # Expected

        # Verify no temp files left behind
        temp_dir = Path("/tmp/madspark_uploads")
        exe_files = list(temp_dir.glob("*malware.exe"))
        assert len(exe_files) == 0, "Temp file not cleaned up after validation error"


class TestMultiModalEndpoint:
    """Integration tests for multi-modal file upload endpoint."""

    @pytest.mark.integration
    def test_generate_ideas_with_pdf_upload(self):
        """Test idea generation with PDF file upload."""
        # This test will be implemented after endpoint modification
        # It will test end-to-end file upload flow
        pass

    @pytest.mark.integration
    def test_generate_ideas_with_image_upload(self):
        """Test idea generation with image file upload."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_generate_ideas_with_url_input(self):
        """Test idea generation with URL input."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_generate_ideas_with_multiple_files(self):
        """Test idea generation with multiple file uploads."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_generate_ideas_rejects_invalid_file(self):
        """Test that endpoint rejects invalid file formats."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_generate_ideas_rejects_oversized_file(self):
        """Test that endpoint rejects oversized files."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_temp_file_cleanup_after_success(self):
        """Test that temp files are cleaned up after successful processing."""
        # This test will be implemented after endpoint modification
        pass

    @pytest.mark.integration
    def test_temp_file_cleanup_after_failure(self):
        """Test that temp files are cleaned up after processing failure."""
        # This test will be implemented after endpoint modification
        pass


class TestMultiModalURLs:
    """Test cases for multi-modal URL handling in requests."""

    def test_request_with_valid_urls(self):
        """Test IdeaGenerationRequest with valid URLs."""
        # This test will validate the extended Pydantic model
        pass

    def test_request_with_too_many_urls(self):
        """Test that request validation limits number of URLs."""
        # This test will check max_items constraint
        pass

    def test_request_urls_optional(self):
        """Test that multimodal_urls field is optional."""
        # This test will verify backward compatibility
        pass


class TestErrorTracking:
    """Test cases for file-specific error tracking."""

    def test_track_file_validation_error(self):
        """Test error tracking for file validation failures."""
        # This test will verify error_tracker integration
        pass

    def test_track_file_size_error(self):
        """Test error tracking for file size limit errors."""
        # This test will verify specific error categorization
        pass

    def test_track_unsupported_format_error(self):
        """Test error tracking for unsupported file format errors."""
        # This test will verify error message clarity
        pass


# Test fixtures
@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    file_content = b"%PDF-1.4\nTest PDF content"
    file = BytesIO(file_content)

    upload_file = UploadFile(
        filename="test.pdf",
        file=file
    )
    upload_file.size = len(file_content)

    return upload_file


@pytest.fixture
def mock_image_upload():
    """Create a mock image UploadFile for testing."""
    # PNG magic bytes + minimal valid PNG data
    file_content = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    file = BytesIO(file_content)

    upload_file = UploadFile(
        filename="test.png",
        file=file
    )
    upload_file.size = len(file_content)

    return upload_file


@pytest.fixture
def temp_upload_dir():
    """Create temporary upload directory for testing."""
    temp_dir = Path("/tmp/madspark_test_uploads")
    temp_dir.mkdir(exist_ok=True)

    yield temp_dir

    # Cleanup
    for file in temp_dir.glob("*"):
        file.unlink()
    temp_dir.rmdir()
