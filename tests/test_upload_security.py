
import io
import pytest
from pathlib import Path
from fastapi import UploadFile, HTTPException
from unittest.mock import MagicMock, patch
import os
import shutil

# Import the function to be tested.
# Since it's inside main.py and relies on imports, we might need to mock imports or import carefully.
# We will try to import it from web.backend.main

import sys
sys.path.append(os.getcwd())

from web.backend.main import save_upload_file
from src.madspark.config.execution_constants import MultiModalConfig

class TestUploadSecurity:

    def setup_method(self):
        self.test_dir = Path("/tmp/madspark_uploads")
        if self.test_dir.exists():
             shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)

    def teardown_method(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_save_upload_file_chunked(self):
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

    def test_save_upload_file_too_large(self):
        """Test that save_upload_file raises HTTPException if file is too large."""
        # Create content slightly larger than limit
        max_size = MultiModalConfig.MAX_FILE_SIZE
        content_size = max_size + 100

        # We don't want to actually create a 20MB+ string in memory if we can avoid it,
        # but for this test we need to simulate a large file.
        # However, checking `upload_file.size` is the first check.

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
        This verifies the incremental size check we plan to add.
        """
        # Create a "stream" that returns more bytes than reported in .size
        # Limit is 20MB. We create 20MB + 1KB.
        real_content = b"a" * (MultiModalConfig.MAX_FILE_SIZE + 1024)
        file_obj = io.BytesIO(real_content)

        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = "spoofed_file.txt"
        upload_file.file = file_obj
        upload_file.size = 1024 # Lie about the size (1KB)

        with pytest.raises(HTTPException) as excinfo:
            save_upload_file(upload_file)

        assert excinfo.value.status_code == 413
        # Ensure it's not the first check (which uses parentheses in detail message)
        # The first check: f"File too large: {upload_file.filename} ({file_size} bytes). Maximum size: {MultiModalConfig.MAX_FILE_SIZE} bytes"
        # The incremental check: f"File too large: exceeded {MultiModalConfig.MAX_FILE_SIZE} bytes limit during upload"
        assert "exceeded" in excinfo.value.detail
        assert "bytes limit during upload" in excinfo.value.detail
