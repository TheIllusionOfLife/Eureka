# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Eureka is a mature Python project featuring the MadSpark Multi-Agent System, a sophisticated AI-powered experimental platform. The project is licensed under GPL-3.0 and implements a hybrid architecture supporting multiple operational modes.

## Project Architecture

### Main Project: MadSpark Multi-Agent System (`mad_spark_multiagent/`)

**Core Architecture**: Multi-agent coordination system with three operational modes:
- **Mock Mode**: Cost-free development and testing (always available)
- **Direct API Mode**: Production Google Gemini integration (recommended)
- **ADK Framework Mode**: Advanced agent management (currently has integration issues)

**Key Components**:
- **Agents**: IdeaGenerator, Critic, Advocate, Skeptic (in `agent_defs/`)
- **Coordinator**: Main orchestration engine (`coordinator.py`)
- **CLI Interface**: Full-featured command-line interface (`cli.py`)
- **Temperature Control**: Creativity levels with presets (conservative, balanced, creative, wild)
- **Bookmark System**: File-based idea storage with tagging (`bookmark_system.py`)
- **Novelty Filter**: Lightweight duplicate detection (`novelty_filter.py`)

## Development Commands

**Working Directory**: All commands must be run from within the `mad_spark_multiagent/` directory unless otherwise specified.

### Environment Setup
```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd mad_spark_multiagent
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env to add your GOOGLE_API_KEY, GOOGLE_GENAI_MODEL, and GOOGLE_CLOUD_PROJECT
```

### Running the Application
```bash
# Direct workflow execution
python coordinator.py

# Full CLI interface with new Phase 1 features
python cli.py --help
python cli.py "AI in healthcare" "Budget-friendly" --temperature 0.8
python cli.py "Smart cities" "Scalable solutions" --temperature-preset creative
python cli.py "Green energy" "Residential" --bookmark-results --bookmark-tags renewable energy
python cli.py "Innovation" --remix --bookmark-tags technology

# Bookmark management
python cli.py --list-bookmarks
python cli.py --search-bookmarks "solar"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run single test method
pytest tests/test_coordinator.py::TestCoordinator::test_run_workflow_mock_mode

# Quick CI-safe test (no API calls)
python -c "
import agent_defs.idea_generator as ig
import agent_defs.critic as critic
prompt = ig.build_generation_prompt('test', {'mode': '逆転'})
print('✅ Basic functionality tests passed')
"
```

### Code Quality
```bash
# Linting (optional, continues on error)
ruff check .

# Type checking (optional, continues on error)  
mypy .

# Security scanning
bandit -r . -x tests/
```

## Development Patterns

### Hybrid Implementation Strategy
The project uses a sophisticated fallback system:
1. Graceful import fallbacks for optional dependencies
2. Multiple operational modes with automatic fallback to mock mode
3. API-free testing to avoid costs and external dependencies

### Error Handling
- Comprehensive retry logic with exponential backoff
- Structured error responses: `{"status": "error", "message": "...", "details": {...}}`
- Graceful degradation when APIs unavailable

### Configuration Management
- Environment variables via `.env` file (GOOGLE_API_KEY, GOOGLE_GENAI_MODEL, GOOGLE_CLOUD_PROJECT)
- Temperature presets in `constants.py` (conservative, balanced, creative, wild)
- Agent configurations in `agent_defs/`
- Pytest configuration in `pytest.ini` with test API keys

## Testing Strategy

**Framework**: pytest with comprehensive mocking
- All tests run without external API calls
- Extensive use of `unittest.mock` for API interactions
- Test coverage includes unit tests, integration tests, and CI-safe tests
- Configure via `pytest.ini` in the `mad_spark_multiagent/` directory

**Test Structure**:
- `test_agents.py` - Agent functionality
- `test_coordinator.py` - Workflow orchestration  
- `test_bookmark_system.py` - Bookmark management
- `test_temperature_control.py` - Temperature configuration
- `test_novelty_filter.py` - Duplicate detection
- `test_utils.py` - Utility functions
- `test_constants.py` - Constants validation

**CI/CD Integration**:
- GitHub Actions workflow testing Python 3.10-3.13
- Automatic dependency caching and security scanning
- CI-safe tests that skip ADK Tool imports when unavailable

## Development Philosophy

### Test-Driven Development (TDD)

* As an overall principle, do test-driven development.
* First, write tests based on expected input/output pairs. Avoid creating mock implementations, even for functionality that doesn't exist yet in the codebase.
* Second, run the tests and confirm they fail. Do not write any implementation code at this stage.
* Third, commit the test when you're satisfied with them.
* Then, write code that passes the tests. Do not modify the tests. Keep going until all tests pass.
* Finally, commit the code once only when you're satisfied with the changes.

## Project Status & Roadmap

### ✅ **Phase 1 "Quick Wins" - COMPLETED** (PR #50 - Merged)
All Phase 1 features have been successfully implemented and merged:

- **Temperature Control**: Full temperature management with CLI support and presets
- **Tier0 Novelty Filter**: Lightweight duplicate detection and similarity filtering
- **Bookmark & Remix System**: File-based idea storage with tagging and remix functionality
- **Enhanced CLI Interface**: Comprehensive command-line interface with all features

**Technical Achievements**:
- Comprehensive code review fixes (21 comments addressed)
- Production-ready error handling and performance optimization
- Complete test coverage with CI/CD validation
- Constants-based architecture eliminating magic numbers

### ✅ **Phase 2 "Complete Enhancement Suite" - COMPLETED** (PR #60, #71 - Merged)
All Phase 2 features have been successfully implemented, tested, and merged to main:

**Phase 2.1 - Enhanced Reasoning Integration**:
- **Context-Aware Agents**: Agents reference conversation history for informed decisions
- **Multi-Dimensional Evaluation**: 7-dimension assessment framework (feasibility, innovation, impact, cost-effectiveness, scalability, risk, timeline) - NOW A CORE FEATURE, ALWAYS ACTIVE
- **Logical Inference Engine**: Formal reasoning chains with confidence scoring and consistency analysis
- **Agent Memory System**: Persistent context storage with intelligent similarity search
- **CLI Integration**: New flags `--enhanced-reasoning`, `--logical-inference` (multi-dimensional eval is now always enabled)

**Phase 2.2-2.3 - Performance & User Experience**:
- **Redis Caching**: LRU eviction with production-safe SCAN operations
- **Batch Processing**: Parallel execution from CSV/JSON input files
- **Interactive CLI**: Real-time conversation mode with guided refinement
- **Web Interface**: React TypeScript frontend with WebSocket progress updates
- **Export Formats**: JSON, CSV, Markdown, and PDF export capabilities
- **Async Execution**: Concurrent agent processing with semaphore control

**Technical Achievements**:
- 95% test coverage across all components
- Comprehensive security fixes (no os.system, sanitized filenames)
- Production-ready error handling and performance optimization
- Full CI/CD validation on Python 3.10-3.13
- Complete documentation and examples

### 🚀 **Phase 3: Enterprise & Integration** (Priority: Future - 6-9 weeks)
- **Enterprise Features**: RBAC, audit logging, SSO integration
- **External Integrations**: Slack/Teams, webhooks, REST APIs
- **Advanced AI Features**: Custom agents, knowledge bases, multi-language support
- **Scalability**: Database backend, multi-user support, horizontal scaling
- **Analytics**: Usage metrics, performance monitoring, cost tracking

## Important Notes

- **Python 3.10+ Required**: Project uses modern Python features
- **API Keys**: Never commit API keys; use `.env.example` as template
- **Mock-First Development**: All functionality must work in mock mode
- **TypedDict Usage**: Use type hints for better code clarity
- **Constants Module**: Eliminate magic strings by using `constants.py`
- **Production Ready**: All core features are stable and CI-validated

## Key Architectural Decisions

### Multi-Mode Operation
The system implements three distinct operational modes to handle different development and deployment scenarios:
- **Mock Mode** (`mock`): Returns predictable test responses, ideal for development and CI/CD
- **Direct API Mode** (`direct`): Direct Google Gemini API calls, recommended for production
- **ADK Framework Mode** (`adk`): Uses Google ADK framework, currently has integration challenges

### Japanese Language Support
The system includes comprehensive Japanese language support:
- Agent prompts and responses in Japanese (`agent_defs/`)
- Japanese idea generation patterns (逆転, 組み合わせ, etc.)
- Unicode handling in all text processing components

### Fallback Architecture
Implements graceful degradation patterns:
- Optional dependency imports with try/catch blocks
- API failure handling with meaningful error messages
- Automatic fallback to mock mode when APIs unavailable

## Pull Request Review Management

### Critical Guidelines for Accessing PR Reviews

**IMPORTANT**: When asked to address PR review comments, you MUST follow this systematic approach to ensure you get complete review content. Previous issues occurred due to incomplete review retrieval.

#### 1. Mandatory Two-Phase Review Check Protocol

**CRITICAL**: You MUST follow this exact protocol to prevent missing reviews. The two-phase approach ensures complete discovery before any filtering.

**Phase 1: Complete Discovery (NO FILTERING)**
```bash
# Step 1: Get PR context and auto-detect variables
PR_NUM=$(gh pr view --json number | jq -r '.number')
REPO=$(gh repo view --json owner,name | jq -r '.owner.login + "/" + .name')

echo "📊 Analyzing PR #${PR_NUM} in ${REPO}"
echo ""

# Step 2: Check ALL three review sources systematically
echo "=== 📝 PR COMMENTS (General Discussion) ==="
gh api "/repos/${REPO}/issues/${PR_NUM}/comments" | jq -r '.[] | .body'

echo ""
echo "=== 📋 PR REVIEWS (Formal Reviews) ==="
gh api "/repos/${REPO}/pulls/${PR_NUM}/reviews" | jq -r '.[] | .body // "No summary"'

echo ""
echo "=== 💬 LINE COMMENTS (Code-Specific) ==="
gh api "/repos/${REPO}/pulls/${PR_NUM}/comments" | jq -r '.[] | .body'

echo ""
echo "✅ Phase 1 Complete: All review sources checked"
```

**Phase 2: Timestamp Filtering (Only After Complete Discovery)**
```bash
# Only apply timestamp filtering AFTER Phase 1 is complete
TIMESTAMP="$(git log -1 --format="%cd" --date=iso)"
echo "🕒 Checking for new feedback since: ${TIMESTAMP}"

# Apply same checks with timestamp filter
gh api "/repos/${REPO}/issues/${PR_NUM}/comments" | jq -r '.[] | select(.created_at > "'$TIMESTAMP'") | .body'
gh api "/repos/${REPO}/pulls/${PR_NUM}/comments" | jq -r '.[] | select(.created_at > "'$TIMESTAMP'") | .body'
gh api "/repos/${REPO}/pulls/${PR_NUM}/reviews" | jq -r '.[] | select(.submitted_at > "'$TIMESTAMP'") | .body // "No summary"'
```

**Fallback Methods** (if API fails):
```bash
# Method A: Use gh pr view commands
gh pr view {PR_NUMBER} --json comments | jq '.comments | reverse | .[]'
gh pr view {PR_NUMBER} --json reviews | jq '.reviews | reverse | .[]'

# Method B: Manual text parsing (last resort)
gh pr view {PR_NUMBER} --comments
```

#### 2. Handling Truncation Issues

**Always verify complete content**:
- If output ends with `... [X lines truncated] ...`, the content is incomplete
- Use JSON output format instead of text format
- Extract review bodies individually using jq
- For very long reviews, save to temporary files:

```bash
# Save full review to file for analysis
gh pr view {PR_NUMBER} --json reviews | jq -r '.reviews[0].body' > /tmp/review.txt
cat /tmp/review.txt
```

#### 3. Mandatory Verification Checklist

**CRITICAL**: Complete this checklist before proceeding with ANY fixes:

**Review Completeness:**
- [ ] Phase 1 complete discovery executed (all 3 sources checked)
- [ ] Complete review text retrieved (no truncation warnings)
- [ ] All reviewer names identified with attribution
- [ ] Total count verified: X comments, Y reviews, Z line comments

**Content Analysis:**
- [ ] Critical vs. medium vs. minor issues classified
- [ ] Specific file/line references documented
- [ ] Clear understanding of what needs to be fixed
- [ ] Dependencies between issues identified

**Quality Gates:**
- [ ] No filtering applied until complete discovery finished
- [ ] No "... [X lines truncated] ..." warnings in output
- [ ] All three review sources returned content or explicit "no content" message

#### 4. Error Handling Protocol

**If you get 404 errors**:
1. Verify you're in the correct repository directory
2. Check if PR number is correct: `gh pr list`
3. Verify GitHub CLI authentication: `gh auth status`
4. Try alternative endpoints or ask user for direct issue description

**If reviews are incomplete**:
1. DO NOT proceed with partial information
2. Ask user to provide specific review content
3. Explain what information you were unable to retrieve
4. Request clarification on critical issues to address

#### 5. Required Response Pattern

When addressing PR reviews, always start with:
```
## Issues Identified from Reviews

**Critical Issues:**
- [List critical issues with reviewer attribution]

**Minor Issues:**
- [List minor issues with reviewer attribution]

**Verification:** ✅ Complete review content retrieved
```

### Examples of Working Commands

```bash
# Get latest review from Gemini Code Assist
gh pr view 56 --json reviews | jq -r '.reviews[-1].body'

# Get review from specific reviewer
gh pr view 56 --json reviews | jq -r '.reviews[] | select(.author.login=="cursor") | .body'

# Get all reviews with metadata
gh pr view 56 --json reviews | jq '.reviews[] | {author: .author.login, state: .state, body: .body}'
```

#### 6. Systematic Preventive Measures

**Root Cause Prevention**: Based on analysis of systematic review failures, implement these safeguards:

**A. Two-Phase Discovery Protocol**
- NEVER apply timestamp filtering until Phase 1 complete discovery is finished
- Always use auto-detection patterns instead of manual PR number entry
- Verify all three review sources return content or explicit "no content" message

**B. Content Verification Standards**
- Use JSON extraction over text parsing to prevent truncation
- Save large reviews to temp files: `/tmp/review_$REVIEWER.txt`
- Implement reviewer attribution tracking: "Fixed Copilot ✅ Gemini ✅ Claude ✅"

**C. Quality Gates**
```bash
# Verification command to run before proceeding
verify_review_completeness() {
    local comments_count=$(gh api "/repos/${REPO}/issues/${PR_NUM}/comments" | jq '. | length')
    local reviews_count=$(gh api "/repos/${REPO}/pulls/${PR_NUM}/reviews" | jq '. | length')  
    local line_comments_count=$(gh api "/repos/${REPO}/pulls/${PR_NUM}/comments" | jq '. | length')
    
    echo "📊 Review Discovery Summary:"
    echo "   PR Comments: ${comments_count}"
    echo "   PR Reviews: ${reviews_count}"
    echo "   Line Comments: ${line_comments_count}"
    echo "   Total Issues: $((comments_count + reviews_count + line_comments_count))"
    
    if [[ $((comments_count + reviews_count + line_comments_count)) -eq 0 ]]; then
        echo "⚠️  WARNING: No reviews found - verify this is correct"
        return 1
    fi
    
    echo "✅ Review completeness verified"
    return 0
}
```

**D. Implementation Quality Standards**
- Use clear, testable validation logic over complex one-liners
- Include comprehensive edge case handling (zero, negative, non-numeric values)
- Add logging for debugging and verification
- Test with various input scenarios before committing

**Note**: This guidance was added after experiencing systematic review failures where incomplete review retrieval led to missing critical problems. The two-phase protocol prevents premature filtering and ensures comprehensive issue discovery.


## Web Interface & Export Features (Phase 2.2)

### Architecture Patterns
- **Full-Stack Structure**: FastAPI backend + React TypeScript frontend
- **Real-time Communication**: WebSocket for progress updates using asyncio
  - Events: progress updates, workflow completion, error notifications
  - Message format: `{"type": "progress", "message": "...", "progress": 0.0-1.0, "timestamp": "..."}`
  - Client connection: `/ws/progress` endpoint with auto-reconnection
- **Export Strategy**: Centralized ExportManager with format-specific methods
- **Integration**: Web interface calls same `coordinator.py` workflow as CLI, shared state via FastAPI global variables

### File Organization
```
web/
├── backend/main.py          - FastAPI server with WebSocket support
├── frontend/src/App.tsx     - React TypeScript application
├── frontend/package.json    - Frontend dependencies  
└── docker-compose.yml       - Container orchestration (backend:8000, frontend:3000, redis:6379)
```

### Common Tasks
- **Run Web Interface**: `cd web && docker-compose up` (starts all services)
- **Test Export**: `python cli.py 'theme' 'constraints' --export all`
  - Supported formats: JSON, CSV, Markdown, PDF
  - Files saved to: `exports/` directory with timestamps
  - Exports: Complete workflow results including all agent responses
- **WebSocket Debugging**: Check `/ws/progress` endpoint and browser console
- **API Documentation**: Available at `http://localhost:8000/docs` (FastAPI auto-generated)

### Testing Approach
- **Export Tests**: Comprehensive test suite in `test_export_utils.py`
- **WebSocket Tests**: Manual testing required - automated tests pending (plan: pytest-asyncio)
- **Frontend Tests**: React Testing Library setup pending
- **Integration Tests**: Need tests for frontend/backend API communication
- **Web UI Testing**: Use Playwright MCP server for comprehensive end-to-end testing

#### Web Interface Testing with Playwright MCP

**IMPORTANT**: For testing the web interface functionality, use the Playwright MCP server instead of manual browser testing. This provides automated, repeatable testing of the React frontend.

**Prerequisites**:
- Web interface running: `cd web && docker-compose up`
- Backend healthy: `curl http://localhost:8000/api/health`
- Frontend accessible: `http://localhost:3000`

**Testing Commands**:
```bash
# Navigate to web interface
mcp__playwright__playwright_navigate(url="http://localhost:3000")

# Fill form fields
mcp__playwright__playwright_fill(selector="input[name='theme']", value="Your test theme")
mcp__playwright__playwright_fill(selector="textarea[name='constraints']", value="Your constraints")
mcp__playwright__playwright_select(selector="select[name='temperature_preset']", value="balanced")

# Enable enhanced features
mcp__playwright__playwright_click(selector="input[name='enhanced_reasoning']")
mcp__playwright__playwright_click(selector="input[name='multi_dimensional_eval']")

# Submit and capture results
mcp__playwright__playwright_click(selector="button[type='submit']")
mcp__playwright__playwright_screenshot(name="test_results", fullPage=true, savePng=true)

# Test expandable sections
mcp__playwright__playwright_click(selector="button:has-text('Toggle multi-dimensional evaluation section')")
```

**Key Test Scenarios**:
1. **Form Submission**: Verify all form fields accept input correctly
2. **Feature Toggles**: Test enhanced reasoning, multi-dimensional eval, logical inference
3. **Real-time Progress**: Monitor WebSocket progress updates during generation
4. **Results Display**: Verify idea generation, scoring, and feedback loop enhancements
5. **Expandable Content**: Test toggle buttons for critiques, advocacy, skeptical analysis
6. **Score Comparison**: Validate feedback loop showing original vs improved scores
7. **Multi-dimensional Charts**: Confirm radar chart visualization displays correctly

**Error Handling**:
- Check browser console logs: `mcp__playwright__playwright_console_logs(type="error")`
- Monitor WebSocket errors and 500 responses
- Verify backend processing warnings don't break functionality
- Test graceful degradation when API calls fail

**Benefits of Playwright MCP Testing**:
- Automated screenshots for visual regression testing
- Programmatic interaction with complex React components
- Real browser environment testing (not just unit tests)
- Consistent, repeatable test execution
- Integration with Claude Code workflow

### Dependencies
- **Frontend**: React 18.2.0, TypeScript ^4.8, Tailwind CSS 3.x, axios ^1.0
- **Backend**: FastAPI ^0.104, uvicorn ^0.24, python-multipart ^0.0.6
- **Optional**: reportlab ^4.0 (for PDF export - fallback message if unavailable)
- **Infrastructure**: Docker, Redis 7-alpine (for future caching)

### Known Gotchas
- **WebSocket Broadcasting**: Must handle exceptions in async functions for consistent returns
- **Docker Environment**: React needs explicit `REACT_APP_*` environment variables
- **Export Memory**: PDF generation can be memory-intensive for large datasets
- **CORS Configuration**: Currently allows specific origins (e.g., `localhost:3000`) in development. In production, it is strongly recommended to whitelist specific domains to prevent unauthorized cross-origin requests and enhance security.
- **Volume Mounts**: Frontend hot-reload requires `node_modules` volume exclusion in docker-compose
