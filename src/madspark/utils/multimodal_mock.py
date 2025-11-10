"""
Mock Part objects for multi-modal testing.

This module provides mock implementations of Gemini Part objects
for use in mock mode and testing without API calls.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class MockPart:
    """
    Mock Gemini Part object for testing.

    Simulates the structure of google.genai.types.Part for use
    in mock mode and tests.

    Attributes:
        source: Source identifier (file path or URL)
        mime_type: MIME type of the content
        data: Optional bytes data (for inline content)
    """

    source: str
    mime_type: str
    data: Optional[bytes] = None

    # Attributes to match real Part structure
    function_call: Optional[object] = None
    code_execution_result: Optional[object] = None
    executable_code: Optional[object] = None
    file_data: Optional[object] = None
    function_response: Optional[object] = None
    inline_data: Optional[object] = None
    text: Optional[str] = None
    thought: Optional[object] = None
    thought_signature: Optional[object] = None
    video_metadata: Optional[object] = None

    def __post_init__(self):
        """Set inline_data if data is provided."""
        if self.data is not None:
            # Simulate inline_data structure
            self.inline_data = {
                'mime_type': self.mime_type,
                'data': self.data
            }

    def __repr__(self) -> str:
        """String representation of MockPart."""
        return f"MockPart(source={self.source!r}, mime_type={self.mime_type!r})"
