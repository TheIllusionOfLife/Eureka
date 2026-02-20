
import os
# Set MADSPARK_MODE to mock before importing web.backend.main
os.environ["MADSPARK_MODE"] = "mock"

import io
import pytest
from pathlib import Path
from fastapi import UploadFile, HTTPException
from unittest.mock import MagicMock, patch
import shutil

# Import the function to be tested.
# Since it's inside main.py and relies on imports, we use try/except for cross-environment support.

try:
    from web.backend.main import save_upload_file
    from src.madspark.config.execution_constants import MultiModalConfig
except ImportError:
    import sys
    sys.path.append(os.getcwd())
    from web.backend.main import save_upload_file
    from src.madspark.config.execution_constants import MultiModalConfig

class TestUploadSecurity:

    class StreamingFile:
        """A lightweight file-like object for simulating large file reads."""
        def __init__(self, size: int):
            self.total_size = size
            self.bytes_generated = 0

        def read(self, size: int = -1):
            if self.bytes_generated >= self.total_size:
                return b""
            
            chunk_size = size if size > 0 else (self.total_size - self.bytes_generated)
            chunk_size = min(chunk_size, self.total_size - self.bytes_generated)
            self.bytes_generated += chunk_size
            return b"a" * chunk_size

    def setup_method(self):
        self.test_dir = Path("/tmp/madspark_uploads")
        if self.test_dir.exists():
             shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch("madspark.utils.multimodal_input.MultiModalInput.validate_file", return_value=True)
    def test_save_upload_file_chunked(self, mock_validate):
        """Test that save_upload_file works with a valid file."""
        content = b"test content" * 1000
        filename = "test_file.txt"
        file_obj = io.BytesIO(content)

        # Mock UploadFile
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = filename
        upload_file.file = file_obj
        upload_file.size = len(content)

        # Call the function
        saved_path = save_upload_file(upload_file)

        assert saved_path.exists()
        assert saved_path.read_bytes() == content
        mock_validate.assert_called_once()

    def test_save_upload_file_too_large(self):
        """Test that save_upload_file raises HTTPException if file is too large."""
        # Create content slightly larger than limit
        max_size = MultiModalConfig.MAX_FILE_SIZE
        content_size = max_size + 100

        # Initial check using upload_file.size
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "large_file.txt"
        upload_file.size = content_size

        with pytest.raises(HTTPException) as excinfo:
            save_upload_file(upload_file)

        assert excinfo.value.status_code == 413
        assert "File too large" in excinfo.value.detail

    def test_save_upload_file_spoofed_content_length(self):
        """
        Test that save_upload_file detects large file even if size attribute (Content-Length) is small.
        This verifies the incremental size check.
        """
        # Create a "stream" that returns more bytes than reported in .size
        # Limit is 20MB. We create 20MB + 1KB.
        real_size = MultiModalConfig.MAX_FILE_SIZE + 1024
        file_obj = self.StreamingFile(real_size)

        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "spoofed_file.txt"
        upload_file.file = file_obj
        upload_file.size = 1024 # Lie about the size (1KB)

        with pytest.raises(HTTPException) as excinfo:
            save_upload_file(upload_file)

        assert excinfo.value.status_code == 413
        # Ensure it's not the first check
        assert "exceeded" in excinfo.value.detail
        assert "bytes limit during upload" in excinfo.value.detail
