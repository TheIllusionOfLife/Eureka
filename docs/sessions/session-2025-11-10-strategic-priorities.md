# Strategic Priorities: Multi-Modal Capabilities vs. Refactoring

## Date: November 10, 2025 01:35 AM JST

## Context

**New Feature Proposal**: Add multi-modal input capabilities (URLs, PDFs, images) to MadSpark
**Current State**: Refactoring plan at 85% (Phase 3), 20% (Phase 4)
**Key Question**: What should be our overall priorities?

---

## Multi-Modal Feature Analysis

### Value Proposition

**Problem**: Text-only input limits context understanding
**Solution**: Leverage Gemini's native multi-modal capabilities

**Supported Inputs:**
1. **URLs** - Fetch and analyze web content for context
2. **PDFs** - Extract and understand document content
3. **Images** - Visual context (diagrams, mockups, screenshots)
4. **Videos** (future) - Gemini 2.0 supports video understanding

**User Impact**: 🔥 **VERY HIGH**
- Richer context leads to better ideas
- Natural workflow (share links/files instead of copy-paste)
- Competitive advantage (most AI tools don't do this well)
- Unlocks new use cases (analyze competitor sites, understand design mockups)

### Technical Feasibility

**Gemini Advantages:**
```python
# Gemini already supports this natively!
import google.generativeai as genai

# URL context (built-in)
response = genai.GenerativeModel('gemini-2.0-flash').generate_content([
    "Analyze this website for innovative ideas",
    "https://example.com"
])

# PDF upload
pdf_file = genai.upload_file('document.pdf')
response = model.generate_content([
    "Extract key insights from this document",
    pdf_file
])

# Image understanding
image_file = genai.upload_file('mockup.png')
response = model.generate_content([
    "Suggest improvements for this UI design",
    image_file
])
```

**Implementation Complexity**: 🟡 **MODERATE**
- Gemini handles the heavy lifting
- Need CLI argument parsing for file paths/URLs
- Need web API endpoint changes
- Need frontend upload UI
- Need error handling for invalid inputs

**Estimated Effort**: **12-16 hours** (including tests and documentation)

---

## Priority Framework Analysis

### Option A: Features First (Multi-Modal Now)
```
1. Merge PR #189 (30 min)
2. Implement Multi-Modal Capabilities (12-16 hours)
3. Centralize Configuration (3-4 hours) - later
4. Improve Error Handling (4-5 hours) - later
```

**Pros:**
- ✅ High user value delivered quickly
- ✅ Exciting feature to showcase
- ✅ Leverages Gemini's strengths
- ✅ Competitive differentiation

**Cons:**
- ❌ Build on potentially shaky foundation (hardcoded configs, inconsistent errors)
- ❌ May need to refactor multi-modal code later
- ❌ Harder to handle file upload errors without consistent error framework
- ❌ Technical debt continues to accumulate

**Risk Level**: 🟡 **MEDIUM**
- May encounter config/error handling issues during implementation
- Harder to maintain without centralized configuration

---

### Option B: Foundation First (Refactoring, Then Multi-Modal)
```
1. Merge PR #189 (30 min)
2. Centralize Configuration (3-4 hours)
3. Improve Error Handling (4-5 hours)
4. Implement Multi-Modal Capabilities (12-16 hours)
```

**Pros:**
- ✅ Build multi-modal on solid foundation
- ✅ Better error messages for file upload failures
- ✅ Centralized config for file size limits, supported formats
- ✅ Easier to maintain and extend
- ✅ Complete refactoring plan (95%+)

**Cons:**
- ❌ Delays user-facing value by ~8 hours
- ❌ Less exciting initial work

**Risk Level**: 🟢 **LOW**
- Foundation work is straightforward
- Multi-modal benefits from better error handling

---

### Option C: Hybrid Approach (Critical Foundation + Multi-Modal)
```
1. Merge PR #189 (30 min)
2. Centralize Configuration (3-4 hours) ⭐ CRITICAL for multi-modal
3. Implement Multi-Modal Capabilities (12-16 hours)
4. Improve Error Handling (4-5 hours) - leverage multi-modal learnings
```

**Pros:**
- ✅ **Best of both worlds**
- ✅ Config centralization directly benefits multi-modal (file limits, format configs)
- ✅ User value delivered reasonably quickly
- ✅ Error handling can incorporate multi-modal use cases
- ✅ Balanced approach (foundation + features)

**Cons:**
- ❌ Slightly longer path to multi-modal (3-4 hours delay)

**Risk Level**: 🟢 **LOW**
- Small foundation work de-risks multi-modal implementation

---

## Recommended Priority: **Option C - Hybrid Approach**

### Rationale

1. **Configuration Centralization is Critical for Multi-Modal**
   ```python
   # You'll need these for multi-modal:
   MAX_FILE_SIZE = 10_000_000  # 10MB
   SUPPORTED_IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'gif']
   SUPPORTED_DOC_FORMATS = ['pdf', 'txt', 'md']
   URL_FETCH_TIMEOUT = 30.0
   MAX_PDF_PAGES = 100
   IMAGE_MAX_DIMENSION = 4096
   ```
   Better to have these centralized **before** implementing multi-modal

2. **Error Handling Can Wait**
   - Multi-modal will reveal error patterns we need to handle
   - Better to implement error handling **after** seeing real failure modes
   - Can incorporate multi-modal error cases into unified error hierarchy

3. **Quick Foundation Work = Less Technical Debt**
   - 3-4 hours of config work saves refactoring multi-modal code later
   - Clean implementation from the start

---

## Detailed Implementation Plan

### Phase 1: Foundation (3.5-4.5 hours)

#### Step 1.1: Merge PR #189 (30 min)
- Review and merge documentation PR
- Clean slate for new work

#### Step 1.2: Centralize Configuration Constants (3-4 hours)
Create `src/madspark/config/execution_constants.py`:

```python
"""Centralized execution configuration for MadSpark."""

# ========================================
# API & Networking
# ========================================
class APIConfig:
    """API-related configuration."""
    DEFAULT_TIMEOUT = 60.0
    LONG_TIMEOUT = 120.0
    WORKFLOW_TIMEOUT = 1200.0  # 20 minutes
    URL_FETCH_TIMEOUT = 30.0
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

# ========================================
# Multi-Modal Input Limits
# ========================================
class MultiModalConfig:
    """Multi-modal input configuration."""
    # File size limits (bytes)
    MAX_FILE_SIZE = 10_000_000  # 10MB
    MAX_IMAGE_SIZE = 4_000_000  # 4MB
    MAX_PDF_SIZE = 20_000_000   # 20MB

    # Format support
    SUPPORTED_IMAGE_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'}
    SUPPORTED_DOC_FORMATS = {'pdf', 'txt', 'md', 'doc', 'docx'}

    # Processing limits
    MAX_PDF_PAGES = 100
    IMAGE_MAX_DIMENSION = 4096
    MAX_URL_CONTENT_LENGTH = 5_000_000  # 5MB

# ========================================
# Execution & Processing
# ========================================
class ExecutionConfig:
    """Execution-related configuration."""
    THREAD_POOL_SIZE = 4
    MAX_PARALLEL_EVALUATIONS = 10
    OUTPUT_LINE_LIMIT = 5000
    REGEX_COMPLEXITY_LIMIT = 500

# ========================================
# Caching & Performance
# ========================================
class CacheConfig:
    """Cache-related configuration."""
    REDIS_TTL = 3600  # 1 hour
    ENABLE_CACHE_BY_DEFAULT = False
```

**Migration:**
- Search and replace hardcoded values
- Update all imports
- Add tests verifying constants are used

---

### Phase 2: Multi-Modal Implementation (12-16 hours)

#### Step 2.1: Core Multi-Modal Module (4-5 hours)

Create `src/madspark/utils/multimodal_input.py`:

```python
"""Multi-modal input handling for MadSpark."""
from pathlib import Path
from typing import Union, List, Optional
import google.generativeai as genai
from ..config.execution_constants import MultiModalConfig

class MultiModalInput:
    """Handle multi-modal inputs (URLs, PDFs, images)."""

    def __init__(self):
        self.config = MultiModalConfig()

    def process_url(self, url: str) -> genai.types.Part:
        """Process URL input."""
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {url}")

        # Gemini handles URL fetching natively
        return genai.types.Part.from_uri(url)

    def process_file(self, file_path: str) -> genai.types.Part:
        """Process file input (PDF, image, etc.)."""
        path = Path(file_path)

        # Validate existence
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate size
        file_size = path.stat().st_size
        if file_size > self.config.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {file_size} bytes "
                f"(max: {self.config.MAX_FILE_SIZE})"
            )

        # Validate format
        extension = path.suffix.lower().lstrip('.')
        if extension in self.config.SUPPORTED_IMAGE_FORMATS:
            if file_size > self.config.MAX_IMAGE_SIZE:
                raise ValueError(f"Image too large: {file_size} bytes")
        elif extension in self.config.SUPPORTED_DOC_FORMATS:
            if file_size > self.config.MAX_PDF_SIZE:
                raise ValueError(f"Document too large: {file_size} bytes")
        else:
            raise ValueError(
                f"Unsupported format: {extension}. "
                f"Supported: {self.config.SUPPORTED_IMAGE_FORMATS | self.config.SUPPORTED_DOC_FORMATS}"
            )

        # Upload to Gemini
        uploaded_file = genai.upload_file(str(path))
        return uploaded_file

    def build_multimodal_prompt(
        self,
        text_prompt: str,
        urls: Optional[List[str]] = None,
        files: Optional[List[str]] = None
    ) -> List[Union[str, genai.types.Part]]:
        """Build multi-modal prompt for Gemini."""
        parts = [text_prompt]

        if urls:
            for url in urls:
                parts.append(self.process_url(url))

        if files:
            for file_path in files:
                parts.append(self.process_file(file_path))

        return parts
```

**Tests** (`tests/test_multimodal_input.py`):
- Test URL validation
- Test file size validation
- Test format validation
- Test successful file upload (mock)
- Test error cases

---

#### Step 2.2: CLI Integration (3-4 hours)

Update `src/madspark/cli/cli.py`:

```python
# Add new arguments
parser.add_argument(
    '--url', '-u',
    action='append',
    help='Add URL for context (can specify multiple times)'
)
parser.add_argument(
    '--file', '-f',
    action='append',
    help='Add file for context: PDF, image, etc. (can specify multiple times)'
)
parser.add_argument(
    '--image', '-i',
    action='append',
    help='Add image for visual context (can specify multiple times)'
)

# Usage example:
# ms "design improvements" --url https://competitor.com --image mockup.png
# ms "document insights" --file report.pdf --file data.pdf
```

Update workflow execution:

```python
def execute_workflow_with_multimodal(args):
    """Execute workflow with multi-modal inputs."""
    from madspark.utils.multimodal_input import MultiModalInput

    # Build multi-modal prompt
    mm_input = MultiModalInput()

    # Combine URLs and files
    urls = args.url or []
    files = (args.file or []) + (args.image or [])

    # Add context hint for multi-modal
    if urls or files:
        context_hint = "Context provided via:\n"
        if urls:
            context_hint += f"- {len(urls)} URL(s)\n"
        if files:
            context_hint += f"- {len(files)} file(s)\n"

        # Prepend to context
        args.context = (args.context or "") + "\n\n" + context_hint

    # Execute workflow (agents will receive multi-modal parts)
    # ... existing workflow code
```

---

#### Step 2.3: Agent Updates (2-3 hours)

Update `src/madspark/agents/idea_generator.py`:

```python
def generate_idea_with_multimodal(
    topic: str,
    context: str,
    temperature: float,
    multimodal_parts: Optional[List] = None
) -> str:
    """Generate ideas with optional multi-modal context."""

    # Build prompt
    prompt_parts = [
        f"Generate innovative ideas for: {topic}",
        f"Context: {context}"
    ]

    # Add multi-modal parts if provided
    if multimodal_parts:
        prompt_parts.extend(multimodal_parts)

    # Call Gemini with multi-modal prompt
    response = genai_client.models.generate_content(
        model=model_name,
        contents=prompt_parts,  # List of text + files + URLs
        config=config
    )

    return response.text
```

**Similar updates for:**
- `critic.py` - Analyze ideas considering multi-modal context
- `advocate.py` - Find strengths using visual/document context
- `skeptic.py` - Identify flaws using comprehensive context
- `improver.py` - Suggest improvements based on multi-modal insights

---

#### Step 2.4: Web API Integration (2-3 hours)

Update `web/backend/main.py`:

```python
from fastapi import UploadFile, File
from typing import List, Optional

@app.post("/api/generate-multimodal")
async def generate_ideas_multimodal(
    topic: str,
    context: Optional[str] = None,
    urls: Optional[List[str]] = None,
    files: List[UploadFile] = File(None)
):
    """Generate ideas with multi-modal inputs."""

    # Save uploaded files temporarily
    temp_files = []
    if files:
        for file in files:
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            temp_files.append(temp_path)

    try:
        # Process multi-modal inputs
        mm_input = MultiModalInput()
        parts = mm_input.build_multimodal_prompt(
            text_prompt=f"Topic: {topic}\nContext: {context}",
            urls=urls,
            files=temp_files
        )

        # Execute workflow with multi-modal context
        results = await execute_workflow(topic, context, multimodal_parts=parts)

        return {"results": results}

    finally:
        # Cleanup temp files
        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)
```

---

#### Step 2.5: Frontend UI (1-2 hours)

Update `web/frontend/src/components/IdeaForm.tsx`:

```typescript
const [urls, setUrls] = useState<string[]>([]);
const [files, setFiles] = useState<File[]>([]);

// URL input
<div className="multimodal-inputs">
  <label>Add URLs for context:</label>
  <input
    type="url"
    placeholder="https://example.com"
    onKeyPress={(e) => {
      if (e.key === 'Enter') {
        setUrls([...urls, e.currentTarget.value]);
        e.currentTarget.value = '';
      }
    }}
  />
  {urls.map((url, i) => (
    <div key={i} className="url-tag">
      {url}
      <button onClick={() => setUrls(urls.filter((_, idx) => idx !== i))}>×</button>
    </div>
  ))}
</div>

// File upload
<div className="file-upload">
  <label>Upload files (PDF, images):</label>
  <input
    type="file"
    multiple
    accept=".pdf,.png,.jpg,.jpeg"
    onChange={(e) => setFiles(Array.from(e.target.files || []))}
  />
  {files.map((file, i) => (
    <div key={i} className="file-tag">
      📎 {file.name} ({(file.size / 1024).toFixed(1)}KB)
    </div>
  ))}
</div>
```

---

### Phase 3: Error Handling Enhancement (4-5 hours)

**After** multi-modal implementation, update error handling to incorporate:

```python
# src/madspark/utils/error_handling.py

class MultiModalError(MadSparkError):
    """Multi-modal input errors."""
    pass

class FileSizeError(MultiModalError):
    """File too large."""
    pass

class UnsupportedFormatError(MultiModalError):
    """Unsupported file format."""
    pass

class URLFetchError(MultiModalError):
    """Failed to fetch URL."""
    pass
```

---

## Complete Priority Roadmap

### Session 1: Foundation + Multi-Modal Core (16-20 hours)
1. ✅ Merge PR #189 (30 min)
2. ✅ Centralize Configuration Constants (3-4 hours)
   - Create execution_constants.py
   - Add MultiModalConfig
   - Migrate existing hardcoded values
3. ✅ Implement Multi-Modal Core (12-16 hours)
   - MultiModalInput module (4-5 hours)
   - CLI integration (3-4 hours)
   - Agent updates (2-3 hours)
   - Web API integration (2-3 hours)
   - Frontend UI (1-2 hours)
   - Tests and documentation

### Session 2: Polish & Enhancement (8-10 hours)
4. ✅ Improve Error Handling (4-5 hours)
   - Incorporate multi-modal error cases
   - Unified error hierarchy
   - Consistent error messages
5. ✅ Documentation & Examples (2-3 hours)
   - Update README with multi-modal examples
   - Create MULTIMODAL_GUIDE.md
   - Add example use cases
6. ✅ Performance Testing (2 hours)
   - Test with large files
   - Test with multiple URLs
   - Optimize file handling

### Future Enhancements (Optional)
- Video support (Gemini 2.0 feature)
- Audio input (voice memos as context)
- Batch multi-modal processing
- Context caching for repeated file usage

---

## Expected Outcomes

### User Experience Improvements
- **Rich Context**: Users can share links instead of copy-pasting
- **Visual Context**: Upload mockups, diagrams, screenshots
- **Document Analysis**: Extract insights from PDFs
- **Natural Workflow**: More intuitive than text-only input

### Example Use Cases

**Use Case 1: Competitor Analysis**
```bash
ms "innovative features" \
  --url https://competitor1.com \
  --url https://competitor2.com \
  --context "e-commerce platform"
```

**Use Case 2: Design Improvements**
```bash
ms "UI/UX enhancements" \
  --image current-mockup.png \
  --image competitor-design.png \
  --context "mobile app redesign"
```

**Use Case 3: Document Insights**
```bash
ms "actionable recommendations" \
  --file quarterly-report.pdf \
  --file market-research.pdf \
  --context "strategic planning"
```

---

## Risk Mitigation

### Technical Risks

**Risk 1: File Upload Size**
- Mitigation: Centralized size limits in config
- Validation before upload
- Clear error messages

**Risk 2: Gemini API Rate Limits**
- Mitigation: Track file uploads separately
- Implement retry logic
- Document rate limit considerations

**Risk 3: File Storage**
- Mitigation: Temporary file cleanup
- Consider cloud storage for web interface
- Document storage requirements

### Testing Strategy

**Unit Tests:**
- Multi-modal input validation
- File format detection
- Size limit enforcement
- URL validation

**Integration Tests:**
- End-to-end workflow with URLs
- End-to-end workflow with files
- Mixed multi-modal inputs
- Error cases

**Manual Testing:**
- Real URLs (various sites)
- Real PDFs (various sizes)
- Real images (various formats)
- Web interface file upload

---

## Success Criteria

### Phase 1 (Foundation):
- ✅ All configuration centralized
- ✅ No hardcoded timeouts/limits
- ✅ All existing tests pass

### Phase 2 (Multi-Modal):
- ✅ CLI accepts --url, --file, --image flags
- ✅ Web interface has file upload UI
- ✅ Agents use multi-modal context
- ✅ URLs fetched successfully
- ✅ Files uploaded successfully
- ✅ Clear error messages for invalid inputs
- ✅ 90%+ test coverage for multi-modal code

### Phase 3 (Polish):
- ✅ Consistent error handling
- ✅ Comprehensive documentation
- ✅ Performance benchmarks established

---

## Recommendation Summary

**Priority Order:**
1. 🟢 **Merge PR #189** (30 min) - Quick cleanup
2. 🟢 **Centralize Configuration** (3-4 hours) - Critical foundation
3. 🔥 **Multi-Modal Capabilities** (12-16 hours) - High user value
4. 🟡 **Error Handling Polish** (4-5 hours) - Incorporate learnings

**Total Effort**: 20-26 hours across 2 sessions

**Rationale**:
- Small foundation work (3-4 hours) de-risks multi-modal implementation
- Multi-modal delivers immediate user value
- Error handling benefits from real multi-modal use cases
- Balanced approach: quality + features

**Alternative**: If time is very constrained, could skip config centralization and go straight to multi-modal, but this creates technical debt that must be addressed later.

---

## Document Metadata

**Created**: November 10, 2025 01:35 AM JST
**Analysis Type**: Strategic Priority Assessment
**Decision**: Foundation + Multi-Modal (Hybrid Approach)
**Next Action**: Execute Phase 1 (Foundation + Multi-Modal Core)
