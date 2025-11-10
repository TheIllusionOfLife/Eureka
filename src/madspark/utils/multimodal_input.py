"""
Multi-Modal Input Processing for MadSpark.

This module handles multi-modal inputs (files, URLs) for the MadSpark system,
converting them into appropriate formats for Gemini API consumption.

Key Features:
- File validation (size, format, existence)
- Part creation from files (images, PDFs, documents)
- URL validation and incorporation
- Mock mode support for testing without API calls
- Comprehensive error handling with clear messages
"""

import logging
import socket
import ipaddress
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

# Import config
from madspark.config.execution_constants import MultiModalConfig

# Import mock Part
from madspark.utils.multimodal_mock import MockPart

# Try to import Google GenAI types
try:
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None  # type: ignore

# Set up logging
logger = logging.getLogger(__name__)


class MultiModalInput:
    """
    Handle multi-modal inputs for MadSpark.

    Processes files (images, PDFs, documents) and URLs, converting them
    into appropriate Part objects for Gemini API or MockPart objects
    for testing.

    Attributes:
        config: MultiModalConfig instance with size/format limits
    """

    # MIME type mappings (class-level constant for efficiency)
    _MIME_MAP = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'webp': 'image/webp',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    def __init__(self):
        """Initialize MultiModalInput with config."""
        self.config = MultiModalConfig

    def validate_file(self, file_path: Union[str, Path]) -> None:
        """
        Validate file exists, has supported format, and is within size limits.

        Args:
            file_path: Path to file to validate

        Raises:
            ValueError: If file path is invalid, format unsupported, or size exceeds limits
            FileNotFoundError: If file does not exist
        """
        if file_path is None:
            raise ValueError("File path cannot be None")

        if isinstance(file_path, str) and file_path == "":
            raise ValueError("File path cannot be empty")

        # Convert to Path object
        path = Path(file_path)

        # Check existence
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Get file size
        file_size = path.stat().st_size

        # Detect format and determine size limit (data-driven approach)
        extension = path.suffix.lower().lstrip('.')

        # Look up file type rules
        if extension in self.config.FILE_TYPE_RULES:
            file_type, max_size = self.config.FILE_TYPE_RULES[extension]
        else:
            supported_all = self.config.SUPPORTED_IMAGE_FORMATS | self.config.SUPPORTED_DOC_FORMATS
            raise ValueError(
                f"Unsupported file format: .{extension}. "
                f"Supported formats: {', '.join(sorted(supported_all))}"
            )

        # Perform single size check
        if file_size > max_size:
            raise ValueError(
                f"File too large: {file_size} bytes "
                f"(max for {file_type}: {max_size} bytes)"
            )

    def validate_url(self, url: Optional[str]) -> None:
        """
        Validate URL format and scheme with SSRF protection.

        Args:
            url: URL string to validate

        Raises:
            ValueError: If URL is invalid, uses unsupported scheme, or targets private/internal resources
        """
        if url is None or url == "":
            raise ValueError("Invalid URL: URL cannot be empty or None")

        # Parse URL (urlparse is robust and doesn't raise exceptions)
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(
                f"Invalid URL: Unsupported scheme '{parsed.scheme}'. "
                f"Only http and https are supported."
            )

        # Check netloc (domain)
        if not parsed.netloc:
            raise ValueError("Invalid URL: Missing domain")

        # SSRF Protection: Block localhost and private IP addresses
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: Cannot extract hostname")

        # Block localhost variants
        localhost_patterns = ['localhost', '127.', '0.0.0.0', '[::]', '[::1]']
        if any(hostname.lower().startswith(pattern) for pattern in localhost_patterns):
            raise ValueError(
                "Invalid URL: Localhost/loopback addresses are not allowed for security reasons"
            )

        # Resolve hostname and check for private IPs
        try:
            # Get IP address from hostname
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)

            # Block private/internal IP ranges
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                raise ValueError(
                    f"Invalid URL: Private/internal IP addresses are not allowed for security reasons "
                    f"(resolved to {ip_str})"
                )
        except socket.gaierror:
            # DNS resolution failed - could be invalid domain or network issue
            raise ValueError(f"Invalid URL: Cannot resolve hostname '{hostname}'")

    def _detect_mime_type(self, file_path: Union[str, Path]) -> str:
        """
        Detect MIME type from file extension.

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        path = Path(file_path)
        extension = path.suffix.lower().lstrip('.')

        return self._MIME_MAP.get(extension, 'application/octet-stream')

    def process_file(self, file_path: Union[str, Path]) -> Union['types.Part', MockPart]:
        """
        Process file and create Part object.

        Args:
            file_path: Path to file to process

        Returns:
            Part object (real or mock depending on mode)

        Raises:
            ValueError: If file validation fails
            FileNotFoundError: If file doesn't exist
        """
        # Validate file first
        self.validate_file(file_path)

        path = Path(file_path)

        # Check file size and log warning if large
        file_size = path.stat().st_size
        if file_size > 5 * 1024 * 1024:  # 5MB threshold
            logger.warning(
                f"Processing large file ({file_size / (1024 * 1024):.1f} MB). "
                f"This may take longer and could approach timeout limits."
            )

        # Read file data
        file_data = path.read_bytes()

        # Detect MIME type
        mime_type = self._detect_mime_type(path)

        # Create Part (real or mock)
        if GENAI_AVAILABLE and types is not None:
            # Real mode: create actual Part
            part = types.Part.from_bytes(
                data=file_data,
                mime_type=mime_type
            )
            return part
        else:
            # Mock mode: create MockPart
            mock_part = MockPart(
                source=str(path),
                mime_type=mime_type,
                data=file_data
            )
            return mock_part

    def build_multimodal_prompt(
        self,
        text_prompt: str,
        files: Optional[List[Union[str, Path]]] = None,
        urls: Optional[List[str]] = None
    ) -> Union[str, List[Union[str, 'types.Part', MockPart]]]:
        """
        Build multi-modal prompt combining text, files, and URLs.

        Args:
            text_prompt: Base text prompt
            files: Optional list of file paths
            urls: Optional list of URLs

        Returns:
            - If no files: returns text prompt (with URLs incorporated)
            - If files provided: returns list of [text, part1, part2, ...]

        Raises:
            ValueError: If file/URL validation fails
        """
        # Start with text prompt
        enhanced_text = text_prompt

        # Add URL context to text (since Gemini can't fetch them)
        if urls:
            for url in urls:
                self.validate_url(url)
            url_list_str = "\n".join(f"- {url}" for url in urls)
            enhanced_text += f"\n\nURL References:\n{url_list_str}\n"

        # If no files, return enhanced text only
        if not files:
            return enhanced_text

        # Process files and build list of Parts
        parts: List[Union[str, 'types.Part', MockPart]] = [enhanced_text]

        for file_path in files:
            part = self.process_file(file_path)
            parts.append(part)

        return parts


# Convenience function to avoid code duplication
def build_prompt_with_multimodal(
    text_prompt: str,
    multimodal_files: Optional[List[Union[str, Path]]] = None,
    multimodal_urls: Optional[List[str]] = None
) -> Union[str, List[Union[str, 'types.Part', MockPart]]]:
    """
    Convenience function to build multi-modal prompt.

    This helper reduces code duplication across idea_generator, improve_idea,
    and structured_idea_generator functions.

    Args:
        text_prompt: Base text prompt
        multimodal_files: Optional list of file paths
        multimodal_urls: Optional list of URLs

    Returns:
        Enhanced prompt (string or list with Parts)
    """
    mm_processor = MultiModalInput()
    return mm_processor.build_multimodal_prompt(
        text_prompt=text_prompt,
        files=multimodal_files,
        urls=multimodal_urls
    )
