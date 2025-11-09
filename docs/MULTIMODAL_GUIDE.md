# Multi-Modal Input Guide

## Overview

MadSpark now supports multi-modal inputs, allowing you to provide rich context through:
- **Files**: Images (PNG, JPG, WebP, GIF, BMP), PDFs, and documents (TXT, MD)
- **URLs**: Web pages for additional context

This enables more informed and contextual idea generation by leveraging visual, document, and web-based information.

## Quick Start

### Python API

```python
from madspark.agents.idea_generator import generate_ideas, improve_idea

# Generate ideas with an image
ideas = generate_ideas(
    topic="UI/UX improvements",
    context="Mobile app redesign",
    multimodal_files=["mockup.png"],
    temperature=0.8
)

# Generate ideas with a PDF
ideas = generate_ideas(
    topic="Product strategy",
    context="Market analysis",
    multimodal_files=["report.pdf"],
    temperature=0.8
)

# Generate ideas with URLs
ideas = generate_ideas(
    topic="Feature ideas",
    context="Competitive analysis",
    multimodal_urls=["https://competitor1.com", "https://competitor2.com"],
    temperature=0.8
)

# Mix files and URLs
ideas = generate_ideas(
    topic="Comprehensive design review",
    context="Best practices from multiple sources",
    multimodal_files=["current_design.png"],
    multimodal_urls=["https://dribbble.com/shots/..."],
    temperature=0.8
)

# Improve ideas with visual context
improved = improve_idea(
    original_idea="A responsive card-based layout",
    critique="Needs more specific features",
    advocacy_points="Clean visual hierarchy",
    skeptic_points="Lacks interactivity details",
    topic="UI Component Design",
    context="Web application",
    multimodal_files=["reference_design.png"]
)
```

## Supported File Formats

### Images
- **Formats**: PNG, JPG, JPEG, WebP, GIF, BMP
- **Max Size**: 8 MB per image
- **Use Cases**: Mockups, screenshots, diagrams, design references

### Documents
- **PDF**: Max 40 MB, up to 100 pages
- **Text**: TXT, MD files, max 20 MB
- **Use Cases**: Reports, documentation, research papers

### URLs
- **Protocols**: HTTP, HTTPS
- **Use Cases**: Competitor websites, reference articles, design examples

## Configuration Limits

All limits are defined in `src/madspark/config/execution_constants.py`:

```python
class MultiModalConfig:
    # File size limits (bytes)
    MAX_FILE_SIZE = 20_000_000      # 20MB (general)
    MAX_IMAGE_SIZE = 8_000_000      # 8MB (images)
    MAX_PDF_SIZE = 40_000_000       # 40MB (PDFs)

    # Processing limits
    MAX_PDF_PAGES = 100
    IMAGE_MAX_DIMENSION = 4096
    MAX_URL_CONTENT_LENGTH = 5_000_000  # 5MB
```

## Examples

### Example 1: UI Design with Visual Context

```python
from madspark.agents.idea_generator import generate_ideas

# Analyze a design mockup and generate improvement ideas
ideas = generate_ideas(
    topic="Mobile app navigation improvements",
    context="iOS design patterns, accessibility focus",
    multimodal_files=["current_nav.png", "competitor_nav.png"],
    temperature=0.9  # Higher creativity
)
```

### Example 2: Market Research with Documents

```python
# Analyze market research PDFs and generate strategy ideas
ideas = generate_ideas(
    topic="Go-to-market strategy",
    context="SaaS B2B product, competitive landscape",
    multimodal_files=["market_analysis.pdf", "user_research.pdf"],
    temperature=0.7  # More focused
)
```

### Example 3: Competitive Analysis with URLs

```python
# Analyze competitor websites for feature ideas
ideas = generate_ideas(
    topic="Product feature roadmap",
    context="E-commerce platform enhancements",
    multimodal_urls=[
        "https://www.shopify.com",
        "https://www.bigcommerce.com",
        "https://www.woocommerce.com"
    ],
    temperature=0.8
)
```

### Example 4: Comprehensive Multi-Modal Analysis

```python
# Combine diagrams, documents, and web references
ideas = generate_ideas(
    topic="System architecture redesign",
    context="Cloud-native, microservices, scalability",
    multimodal_files=[
        "current_architecture.png",
        "performance_report.pdf",
        "requirements.txt"
    ],
    multimodal_urls=[
        "https://aws.amazon.com/architecture/well-architected/",
        "https://12factor.net/"
    ],
    temperature=0.85
)
```

## Error Handling

The multi-modal system provides clear error messages for common issues:

### File Not Found
```python
try:
    ideas = generate_ideas(
        topic="Test",
        context="Test",
        multimodal_files=["/nonexistent/file.png"]
    )
except FileNotFoundError as e:
    print(f"Error: {e}")  # "File not found: /nonexistent/file.png"
```

### File Too Large
```python
try:
    ideas = generate_ideas(
        topic="Test",
        context="Test",
        multimodal_files=["huge_image.png"]  # >8MB
    )
except ValueError as e:
    print(f"Error: {e}")  # "File too large: X bytes (max for images: 8000000 bytes)"
```

### Unsupported Format
```python
try:
    ideas = generate_ideas(
        topic="Test",
        context="Test",
        multimodal_files=["document.exe"]
    )
except ValueError as e:
    print(f"Error: {e}")  # "Unsupported file format: .exe"
```

### Invalid URL
```python
try:
    ideas = generate_ideas(
        topic="Test",
        context="Test",
        multimodal_urls=["not-a-valid-url"]
    )
except ValueError as e:
    print(f"Error: {e}")  # "Invalid URL: ..."
```

## Performance Considerations

### File Size Warnings
Files larger than 5 MB will trigger a warning log:
```
WARNING: Processing large file (6.5 MB). This may take longer and could approach timeout limits.
```

### Timeout Recommendations
- **Small files** (<1 MB): Normal processing time
- **Medium files** (1-5 MB): Slight delay expected
- **Large files** (5-40 MB): May approach timeout limits, consider:
  - Reducing file size
  - Optimizing images
  - Splitting large PDFs

### URL Fetching
- URLs are incorporated into text prompts (Gemini doesn't fetch them directly)
- Include URLs for context and reference, not for content extraction

## Best Practices

### 1. Choose Relevant Files
- Use files that directly relate to your topic
- Avoid generic or unrelated images
- PDFs should be well-formatted and text-searchable

### 2. Optimize File Sizes
- Compress images before upload
- Use appropriate image formats (WebP for smaller sizes)
- Extract relevant pages from large PDFs

### 3. Provide Clear Context
- Even with files, provide descriptive `context` parameter
- Explain what the files represent
- Guide the AI on how to interpret the visual/document content

### 4. Mix Modalities Strategically
- Combine files and URLs when you need multiple perspectives
- Use images for visual concepts
- Use PDFs for detailed data/research
- Use URLs for live examples and references

### 5. Use Appropriate Temperature
- **Lower (0.5-0.7)**: When files contain specific data you want followed closely
- **Medium (0.7-0.9)**: Balanced creativity with file context
- **Higher (0.9-1.0)**: Creative interpretation of visual/document context

## Backward Compatibility

All multi-modal parameters are **optional**. Existing code continues to work:

```python
# Still works exactly as before
ideas = generate_ideas(
    topic="Innovation ideas",
    context="Cost-effective solutions"
)
```

## Technical Architecture

### How It Works

1. **Validation**: Files are validated for existence, size, and format
2. **Processing**: Files are read as bytes and converted to Gemini `Part` objects
3. **Prompt Building**: Multi-modal prompts combine text with file Parts
4. **API Call**: Gemini receives both text and file content
5. **Response**: Standard idea generation continues with enhanced context

### Mock Mode
In mock/test mode (no API key):
- File validation still occurs
- `MockPart` objects are created instead of real Parts
- Tests can run without API calls
- Full functionality verified in CI/CD

## Limitations

### Current Limitations
- Video files not supported (Gemini 2.0 feature, planned for future)
- Audio files not supported
- URLs are text references only (Gemini doesn't fetch content)
- Maximum of reasonable file count per request (API limits apply)

### Gemini API Limitations
- File upload consumes API quota
- Large files may increase processing time
- Rate limits apply to file uploads

## Troubleshooting

### Issue: "File too large" error
**Solution**: Compress the file or extract relevant portions

### Issue: Timeout with large files
**Solution**:
- Reduce file size
- Split into multiple smaller requests
- Use higher timeout configuration

### Issue: Poor results with images
**Solution**:
- Ensure images are clear and high-resolution
- Add descriptive context about what the image shows
- Use multiple angles/examples if available

### Issue: PDF not being analyzed properly
**Solution**:
- Ensure PDF is text-searchable (not scanned image)
- Check PDF isn't password-protected
- Verify PDF is within page limit (100 pages)

## Future Enhancements

Planned improvements include:
- Video support (Gemini 2.0)
- Audio input for voice memos
- Batch multi-modal processing
- Context caching for repeated file usage
- Automatic image optimization
- PDF page range selection

## Support

For issues or questions:
1. Check error messages - they provide specific guidance
2. Review file sizes and formats
3. Verify API key is configured
4. Check logs for detailed error information
5. Report issues at: [GitHub Issues](https://github.com/TheIllusion OfLife/Eureka/issues)

---

**Last Updated**: November 10, 2025
**Version**: 1.0.0 (Initial Release)
