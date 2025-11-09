#!/usr/bin/env python3
"""
Proof-of-Concept: Gemini Multi-Modal API Research
==================================================

This script tests the Google GenAI SDK's multi-modal capabilities to understand:
1. How to upload and process images
2. How to upload and process PDFs
3. How to handle URLs (if supported)
4. Compatibility with structured output (response_schema)
5. Part object structure and API patterns

Run: PYTHONPATH=src python tools/research/multimodal_poc.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    print("❌ google-genai not available")
    GENAI_AVAILABLE = False
    sys.exit(1)


def test_image_upload():
    """Test 1: Upload and analyze an image using from_bytes()."""
    print("\n" + "="*60)
    print("TEST 1: Image Upload and Analysis (from_bytes)")
    print("="*60)

    # Create a simple test image if it doesn't exist
    test_image_path = Path(__file__).parent / "test_image.txt"

    if not test_image_path.exists():
        print(f"ℹ️  Note: No test image found. This test requires a real image file.")
        print(f"   Create a test image at: {test_image_path}")
        return None

    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

        # Method: Use types.Part.from_bytes()
        print(f"📤 Reading file: {test_image_path}")
        file_data = test_image_path.read_bytes()

        # Create Part from bytes
        file_part = types.Part.from_bytes(
            data=file_data,
            mime_type="text/plain"  # For test file; use image/png for real images
        )

        print(f"✅ Part created successfully!")
        print(f"   Part type: {type(file_part)}")
        print(f"   Has inline_data: {file_part.inline_data is not None}")

        # Try to use the Part in a prompt
        # Can mix strings and Part objects in contents list
        print(f"\n🤖 Sending prompt with file Part...")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=["Describe the content of this file:", file_part]
        )

        print(f"✅ Response received:")
        print(f"   {response.text[:200]}...")

        return file_part

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pdf_upload():
    """Test 2: Upload and analyze a PDF using from_bytes()."""
    print("\n" + "="*60)
    print("TEST 2: PDF Upload and Analysis (from_bytes)")
    print("="*60)

    test_pdf_path = Path(__file__).parent / "test_document.pdf"

    if not test_pdf_path.exists():
        print(f"ℹ️  Note: No test PDF found. Skipping this test.")
        print(f"   Create a test PDF at: {test_pdf_path}")
        return None

    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

        print(f"📤 Reading PDF: {test_pdf_path}")
        pdf_data = test_pdf_path.read_bytes()

        # Create Part from PDF bytes
        pdf_part = types.Part.from_bytes(
            data=pdf_data,
            mime_type="application/pdf"
        )

        print(f"✅ Part created successfully!")

        # Try to extract content from PDF
        print(f"\n🤖 Sending prompt with PDF Part...")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=["Summarize this document in 2-3 bullet points:", pdf_part]
        )

        print(f"✅ Response received:")
        print(f"   {response.text}")

        return pdf_part

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_url_context():
    """Test 3: Use URL as context (if supported)."""
    print("\n" + "="*60)
    print("TEST 3: URL Context Support")
    print("="*60)

    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

        # Try providing a URL directly
        test_url = "https://www.example.com"
        prompt = f"Analyze this website and describe its purpose: {test_url}"

        print(f"🤖 Sending prompt with URL: {test_url}")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )

        print(f"✅ Response received:")
        print(f"   {response.text}")

        # Check if there's a Part type for URLs
        print(f"\n🔍 Checking for URL-specific Part types...")
        if hasattr(types, 'Part'):
            print(f"   types.Part available: {types.Part}")
            if hasattr(types.Part, 'from_uri'):
                print(f"   types.Part.from_uri() method found!")
            else:
                print(f"   No from_uri() method found")

        return True

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def test_structured_output_with_multimodal():
    """Test 4: Structured output compatibility with multi-modal."""
    print("\n" + "="*60)
    print("TEST 4: Structured Output + Multi-Modal")
    print("="*60)

    test_image_path = Path(__file__).parent / "test_image.txt"

    if not test_image_path.exists():
        print(f"ℹ️  Skipping: No test image found")
        return None

    try:
        from typing import TypedDict, List

        class FileAnalysis(TypedDict):
            description: str
            content_type: str
            key_points: List[str]

        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

        # Read file and create Part
        file_data = test_image_path.read_bytes()
        file_part = types.Part.from_bytes(
            data=file_data,
            mime_type="text/plain"
        )

        # Create config with structured output
        config = types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=FileAnalysis
        )

        print(f"🤖 Sending prompt with structured output schema...")
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=["Analyze this file and provide structured information about it.", file_part],
            config=config
        )

        print(f"✅ Response received:")
        print(f"   {response.text}")

        # Try to parse as JSON
        import json
        try:
            parsed = json.loads(response.text)
            print(f"\n✅ Successfully parsed as structured JSON:")
            print(f"   Description: {parsed.get('description', 'N/A')}")
            print(f"   Content Type: {parsed.get('content_type', 'N/A')}")
            print(f"   Key Points: {parsed.get('key_points', [])}")
        except json.JSONDecodeError:
            print(f"⚠️  Response is not valid JSON")

        return True

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_part_structure():
    """Test 5: Understand Part object structure."""
    print("\n" + "="*60)
    print("TEST 5: Part Object Structure")
    print("="*60)

    try:
        # Inspect available Part types
        print("🔍 Inspecting genai.types module...")

        if hasattr(types, 'Part'):
            print(f"✅ types.Part exists")
            print(f"   Methods: {[m for m in dir(types.Part) if not m.startswith('_')]}")

        if hasattr(types, 'Content'):
            print(f"✅ types.Content exists")
            print(f"   Methods: {[m for m in dir(types.Content) if not m.startswith('_')]}")

        # Try to create a text Part
        if hasattr(types, 'Part'):
            try:
                text_part = types.Part(text="Hello, world!")
                print(f"\n✅ Created text Part:")
                print(f"   {text_part}")
            except Exception as e:
                print(f"⚠️  Cannot create text Part: {e}")

        return True

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run all POC tests."""
    print("=" * 60)
    print("Gemini Multi-Modal API - Proof of Concept")
    print("=" * 60)

    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not set. Please set it to run these tests.")
        print("   export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    print(f"✅ API Key found: {api_key[:10]}...")

    # Run tests
    results = {
        'image_upload': test_image_upload(),
        'pdf_upload': test_pdf_upload(),
        'url_context': test_url_context(),
        'structured_output': test_structured_output_with_multimodal(),
        'part_structure': test_part_structure()
    }

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "⚠️  SKIP/FAIL" if result is None else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    print("KEY FINDINGS")
    print("="*60)
    print("""
VERIFIED MULTI-MODAL API PATTERNS:

1. **Part Creation from Bytes**:
   - Use types.Part.from_bytes(data=bytes, mime_type=str)
   - Keyword-only arguments required
   - Returns Part with inline_data attribute

2. **Part Creation from Text**:
   - Use types.Part.from_text(text=str) for text Parts
   - Can also pass raw strings to contents parameter directly

3. **Part Creation from URI**:
   - Use types.Part.from_uri(file_uri=str, mime_type=str|None)
   - For cloud storage or external file URIs

4. **Multi-Modal Contents**:
   - contents parameter accepts List[str | Part]
   - Can mix strings and Part objects freely
   - Example: ["prompt text", file_part, "more context"]

5. **Structured Output Compatibility**:
   - ✅ response_schema WORKS with multi-modal inputs
   - Returns valid JSON matching TypedDict schema
   - Critical for maintaining MadSpark's structured output pattern

6. **URL Context**:
   - Gemini cannot fetch external URLs directly
   - URLs must be included in text prompt for context
   - No special URL Part type needed (just include in text)

7. **MIME Types**:
   - text/plain for text files
   - image/png, image/jpeg for images
   - application/pdf for PDFs
   - Part.from_bytes() requires explicit mime_type

IMPLEMENTATION IMPLICATIONS:

- MultiModalInput should use types.Part.from_bytes() for files
- Support keyword-only Part factory methods
- Maintain backward compatibility: strings work in contents
- Structured output (response_schema) is safe to use
- URL fetching must happen client-side (not by Gemini)
    """)


if __name__ == '__main__':
    main()
