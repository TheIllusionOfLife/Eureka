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

### 🔄 **Next Development Phases**
Future development should focus on:

1. **Phase 2 Features**: Advanced agent behaviors and improved evaluation metrics
2. **Performance Optimization**: Caching strategies and batch processing
3. **Integration Enhancements**: External service integrations and webhook support
4. **User Experience**: Web interface and visualization tools

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

#### 1. Systematic PR Review Fetching Process

**Primary Method** (use this first):
```bash
# Step 1: Get PR number and verify context
gh pr view --json number,headRepository

# Step 2: Get all reviews in reverse order (latest first)
gh pr view {PR_NUMBER} --json reviews | jq '.reviews | reverse | .[]'

# Step 3: Extract specific review content (replace {INDEX} with 0, 1, 2...)
gh pr view {PR_NUMBER} --json reviews | jq -r '.reviews[{INDEX}].body'
```

**Fallback Methods** (if primary fails):
```bash
# Method A: Use comments endpoint
gh pr view {PR_NUMBER} --json comments | jq '.comments | reverse | .[]'

# Method B: Try direct API access
gh api /repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/reviews

# Method C: Use text output with manual parsing
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

#### 3. Verification Checklist

Before proceeding with fixes, ensure you have:
- [ ] Complete review text (no truncation)
- [ ] All reviewer names and their specific issues
- [ ] Specific file/line references if mentioned
- [ ] Critical vs. minor issue classification
- [ ] Clear understanding of what needs to be fixed

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

**Note**: This guidance was added after experiencing issues where incomplete review retrieval led to missing critical problems. Always ensure complete information before proceeding with fixes.
