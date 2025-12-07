"""Tests for multi-modal input security and edge cases.

This test suite verifies:
- SSRF protection in URL validation
- File/URL count limits
- Empty file handling
- Permission denied scenarios
- Symbolic link handling
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.madspark.utils.multimodal_input import MultiModalInput
from src.madspark.cli.commands.validation import (
    WorkflowValidator,
    MAX_MULTIMODAL_FILES,
    MAX_MULTIMODAL_URLS
)


class TestSSRFProtection:
    """Test SSRF vulnerability protection."""

    def test_blocks_localhost(self):
        """Test that localhost URLs are blocked."""
        mm_input = MultiModalInput()

        dangerous_urls = [
            "http://localhost/admin",
            "http://localhost:8080/secret",
            "https://localhost/metadata",
        ]

        for url in dangerous_urls:
            with pytest.raises(ValueError, match="Localhost/loopback addresses are not allowed"):
                mm_input.validate_url(url)

    def test_blocks_127_loopback(self):
        """Test that 127.x.x.x loopback addresses are blocked."""
        mm_input = MultiModalInput()

        loopback_urls = [
            "http://127.0.0.1/admin",
            "http://127.1.1.1/secret",
            "https://127.255.255.255/metadata",
        ]

        for url in loopback_urls:
            with pytest.raises(ValueError, match="Localhost/loopback addresses are not allowed"):
                mm_input.validate_url(url)

    def test_blocks_private_ips(self):
        """Test that private IP ranges are blocked."""
        mm_input = MultiModalInput()

        # Mock socket.gethostbyname to return private IPs
        with patch('socket.gethostbyname') as mock_dns:
            # Test 10.x.x.x range
            mock_dns.return_value = "10.0.0.1"
            with pytest.raises(ValueError, match="Private/internal IP addresses are not allowed"):
                mm_input.validate_url("http://internal.company.local/api")

            # Test 192.168.x.x range
            mock_dns.return_value = "192.168.1.1"
            with pytest.raises(ValueError, match="Private/internal IP addresses are not allowed"):
                mm_input.validate_url("http://router.local/admin")

            # Test 172.16-31.x.x range
            mock_dns.return_value = "172.16.0.1"
            with pytest.raises(ValueError, match="Private/internal IP addresses are not allowed"):
                mm_input.validate_url("http://docker.internal/api")

    def test_blocks_aws_metadata(self):
        """Test that AWS metadata endpoint is blocked."""
        mm_input = MultiModalInput()

        with patch('socket.gethostbyname', return_value="169.254.169.254"):
            with pytest.raises(ValueError, match="Private/internal IP addresses are not allowed"):
                mm_input.validate_url("http://169.254.169.254/latest/meta-data/")

    def test_allows_valid_public_urls(self):
        """Test that valid public URLs are allowed."""
        mm_input = MultiModalInput()

        # Mock DNS to return public IP
        with patch('socket.gethostbyname', return_value="1.2.3.4"):
            # Should not raise
            mm_input.validate_url("https://example.com/document.pdf")
            mm_input.validate_url("http://public-api.example.org/data")

    def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        mm_input = MultiModalInput()

        import socket
        with patch('socket.gethostbyname', side_effect=socket.gaierror("DNS lookup failed")):
            with pytest.raises(ValueError, match="Cannot resolve hostname"):
                mm_input.validate_url("http://non-existent-domain-xyz.invalid/file")


class TestFileLimits:
    """Test file and URL count limits."""

    def test_file_count_limit_enforced(self):
        """Test that file count limit is enforced."""
        import argparse

        # Create args with too many files
        args = argparse.Namespace(
            topic="Test",
            context="Test",
            multimodal_files=[f"/path/file{i}.pdf" for i in range(MAX_MULTIMODAL_FILES + 1)],
            multimodal_images=[],
            multimodal_urls=[],
            remix=False
        )

        # Mock logger
        logger = Mock()
        validator = WorkflowValidator(args, logger)

        # Should raise ValidationError due to too many files
        result = validator.execute()
        assert not result.success
        assert "Too many files" in result.message

    def test_url_count_limit_enforced(self):
        """Test that URL count limit is enforced."""
        import argparse

        # Create args with too many URLs
        args = argparse.Namespace(
            topic="Test",
            context="Test",
            multimodal_files=[],
            multimodal_images=[],
            multimodal_urls=[f"http://example.com/doc{i}" for i in range(MAX_MULTIMODAL_URLS + 1)],
            remix=False
        )

        # Mock logger
        logger = Mock()
        validator = WorkflowValidator(args, logger)

        # Should raise ValidationError due to too many URLs
        result = validator.execute()
        assert not result.success
        assert "Too many URLs" in result.message

    def test_within_limits_succeeds(self):
        """Test that validation succeeds when within limits."""
        import argparse

        # Create args within limits (using mocks to avoid actual file validation)
        args = argparse.Namespace(
            topic="Test",
            context="Test",
            multimodal_files=[],
            multimodal_images=[],
            multimodal_urls=[],
            remix=False,
            temperature=0.7,
            creative=None,
            balanced=None,
            focused=None
        )

        # Mock logger
        logger = Mock()
        validator = WorkflowValidator(args, logger)

        # Should succeed
        result = validator.execute()
        assert result.success


class TestFileEdgeCases:
    """Test edge cases in file validation."""

    def test_empty_file_validation(self):
        """Test that empty files (0 bytes) are accepted but documented."""
        mm_input = MultiModalInput()

        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
            temp_file = f.name
            # File is empty (0 bytes)

        try:
            # Empty files should be allowed - the AI model will handle them
            # This test documents the behavior
            mm_input.validate_file(temp_file)  # Should not raise
        finally:
            os.unlink(temp_file)

    @pytest.mark.skipif(os.name == 'nt', reason="Symbolic links work differently on Windows")
    def test_symbolic_link_handling(self):
        """Test that symbolic links are validated based on their extension."""
        mm_input = MultiModalInput()

        # Create a real file with valid extension
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
            f.write("test content")
            real_file = f.name

        # Create a symbolic link with the same extension
        link_file = real_file + ".symlink.txt"

        try:
            os.symlink(real_file, link_file)

            # Should validate based on the symlink's extension
            mm_input.validate_file(link_file)

        finally:
            if os.path.exists(link_file):
                os.unlink(link_file)
            os.unlink(real_file)

    @pytest.mark.skipif(os.name == 'nt', reason="Permission handling works differently on Windows")
    def test_permission_denied(self):
        """Test that files with restricted permissions can still be validated for format."""
        mm_input = MultiModalInput()

        # Create a file and remove read permissions
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_file = f.name

        try:
            # Remove read permissions
            os.chmod(temp_file, 0o000)

            # The validate_file method only checks format and size, not actual readability
            # Actual read permission errors will occur when the file is used
            # This test documents that validation doesn't require read access
            try:
                mm_input.validate_file(temp_file)
            except (FileNotFoundError, PermissionError):
                # If the OS prevents stat() calls, this is expected
                pass

        finally:
            # Restore permissions before cleanup
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_nonexistent_file(self):
        """Test handling of non-existent files."""
        mm_input = MultiModalInput()

        with pytest.raises(FileNotFoundError):
            mm_input.validate_file("/path/to/nonexistent/file.pdf")

    def test_directory_instead_of_file(self):
        """Test that directories are rejected."""
        mm_input = MultiModalInput()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Should raise ValueError because it's a directory, not a file
            with pytest.raises((ValueError, IsADirectoryError)):
                mm_input.validate_file(temp_dir)


class TestURLEdgeCases:
    """Test edge cases in URL validation."""

    def test_empty_url(self):
        """Test that empty URLs are rejected."""
        mm_input = MultiModalInput()

        with pytest.raises(ValueError, match="URL cannot be empty"):
            mm_input.validate_url("")

    def test_none_url(self):
        """Test that None URLs are rejected."""
        mm_input = MultiModalInput()

        with pytest.raises(ValueError, match="URL cannot be empty"):
            mm_input.validate_url(None)

    def test_invalid_scheme(self):
        """Test that invalid URL schemes are rejected."""
        mm_input = MultiModalInput()

        invalid_urls = [
            "ftp://example.com/file.pdf",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Unsupported scheme"):
                mm_input.validate_url(url)

    def test_missing_domain(self):
        """Test that URLs without domains are rejected."""
        mm_input = MultiModalInput()

        invalid_urls = [
            "http://",
            "https://",
            "http:///path",
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError, match="Missing domain"):
                mm_input.validate_url(url)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
