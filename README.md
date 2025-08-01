# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.2%20Complete-success)](#project-status) [![Testing](https://img.shields.io/badge/Testing-85%25%20Coverage-success)](#testing) [![CI/CD](https://img.shields.io/badge/CI%2FCD-Optimized-brightgreen)](#development)

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API. 
Features specialized agents for idea generation, criticism, advocacy, and skepticism with advanced reasoning capabilities.

## 🚀 Key Features

- **🧠 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🔗 Feedback Loop**: Ideas are improved based on agent insights with score comparison
- **📚 OpenAPI Documentation**: Interactive API docs at `/docs` and `/redoc`
- **🌐 Web Interface**: React frontend with WebSocket progress updates
- **⌨️ Keyboard Shortcuts**: ? for help, Ctrl+Enter to submit, Ctrl+G to focus form
- **🔍 Duplicate Detection**: Intelligent similarity-based bookmark filtering
- **📤 Export Formats**: JSON, CSV, Markdown, and PDF export support

## Quick Start

### Prerequisites
- Python 3.10+ (required for TypedDict and modern features)
- Google Gemini API key (optional - mock mode available)

### Installation

```bash
# Clone the repo
git clone https://github.com/TheIllusionOfLife/Eureka.git
cd Eureka

# Initial setup with interactive configuration
./setup.sh  

# Configure your API key (for real AI responses)
mad_spark config  # Interactive configuration
```

### Non-Interactive Setup (CI/CD, Automation)

For automated environments where interactive prompts aren't available:

```bash
# Create .env file with your API key (root directory)
echo 'GOOGLE_API_KEY="YOUR_API_KEY_HERE"' > .env
echo 'GOOGLE_GENAI_MODEL="gemini-2.5-flash"' >> .env

# Verify configuration
mad_spark config --status

# Run ideas generation (all commands below are equivalent)
mad_spark "your topic here" "your context here"
madspark "your topic here" "your context here"  
ms "your topic here" "your context here"         # Short alias
```

### Command Aliases

MadSpark provides three equivalent commands for your convenience:
- `mad_spark` - Full command name
- `madspark` - Alternative without underscore  
- `ms` - Short alias for quick access

All commands have identical functionality. Choose based on your preference.

See [Command Aliases Documentation](docs/COMMAND_ALIASES.md) for detailed information about installation, troubleshooting, and advanced usage.

### Usage

```bash
# Get help and see all available options
ms --help

# Basic usage with any alias
# command "question/topic/theme" "constraints/context"
mad_spark "how to reduce carbon footprint?" "small business"          
madspark "innovative teaching methods" "high school science"
ms "Come up with innovative ways to teach math" "elementary school"

# Second argument is optional.   
ms "I want to learn AI. Guide me."

# Single argument works too - constraints will default                                    
ms "future technology"                                                 

# Output modes for different needs
ms "healthcare AI" --brief              # Quick summary (default)
ms "education innovation" --detailed     # Full agent analysis
ms "climate solutions" --simple         # Clean

# Advanced options
# Generate 3 ideas with high creativity. Default value is 1.
ms "space exploration" --top-ideas 3 --temperature-preset creative

# Enhanced reasoning with logical inference    
ms "quantum computing" --enhanced --logical

# Cache results with Redis for instant repeated queries                   
ms "how the universe began" --top-ideas 3 --enable-cache

# Set custom timeout (default: 600 seconds / 10 minutes)
ms "complex analysis" --timeout 300     # 5 minute timeout
ms "quick idea" --timeout 60 --async   # 1 minute timeout (async mode enforces timeout)

# Combined options
ms "main prompt" "context" --top-ideas 5 --temperature-preset creative --enhanced --logical --enable-cache --timeout 120

# Run the coordinator - full multi-agent analysis system
# Orchestrates IdeaGenerator, Critic, Advocate, and Skeptic agents
ms coordinator

# Run test suite to verify functionality
ms test

# Web interface (after setting up aliases - see below)
madspark-web                    # Start web interface at http://localhost:3000
madspark-web-logs              # View logs from all services
madspark-web-stop              # Stop web interface

# Manual web interface commands (without aliases)
cd web && docker compose up -d  # Start in detached mode
docker compose logs -f          # View logs
docker compose down            # Stop services
```

### Bookmark Management

MadSpark automatically saves all generated ideas as bookmarks for future reference and remixing. 
Each bookmark includes the improved idea text, score, theme, and timestamp.

#### Key Features:
- **Automatic Deduplication**: Uses Jaccard similarity (default threshold: 0.8) to prevent saving duplicate ideas
- **Smart Display**: Bookmarks are truncated to 300 characters in list view for better readability
- **Full Text Storage**: Complete idea text is preserved in the bookmarks file
- **Flexible Management**: Add tags, search, remove, and remix bookmarks easily

```bash
# Generate ideas - automatically saved as bookmarks
ms "renewable energy" "urban applications"
ms "smart cities" --bookmark-tags urban-innovation smart tech  # Add custom tags

# Generate without saving (use --no-bookmark to disable)
ms "test idea" --no-bookmark

# List all saved bookmarks (shows truncated text for readability)
ms --list-bookmarks

# Search bookmarks by content
ms --search-bookmarks "energy"

# Remove bookmarks by ID (single or multiple)
ms --remove-bookmark bookmark_20250714_141829_c2f64f14
ms --remove-bookmark bookmark_123,bookmark_456,bookmark_789

# Generate new ideas based on saved bookmarks (remix mode)
ms "future technology" --remix --bookmark-tags smart
ms "future technology" --remix --remix-ids bookmark_123,bookmark_456  # Use specific bookmark IDs
```

### Web Interface Setup

The MadSpark web interface provides a modern React-based UI for generating ideas with real-time progress updates.

**Quick Setup with Aliases (Recommended):**
```bash
# Add to your ~/.zshrc or ~/.bashrc:
alias madspark-web="cd ~/Eureka && source .env && cd web && MADSPARK_MODE=api GOOGLE_API_KEY=\$GOOGLE_API_KEY GOOGLE_GENAI_MODEL=\$GOOGLE_GENAI_MODEL docker compose up -d"
alias madspark-web-stop="cd ~/Eureka/web && docker compose down"
alias madspark-web-logs="cd ~/Eureka/web && docker compose logs -f"

# Reload shell configuration
source ~/.zshrc  # or ~/.bashrc

# Use the aliases
madspark-web       # Start at http://localhost:3000
madspark-web-logs  # View logs
madspark-web-stop  # Stop services
```

**Features:**
- Real-time progress updates via WebSocket
- Interactive bookmark management
- Duplicate detection with visual warnings
- Export results in multiple formats
- Keyboard shortcuts for power users

**Notes:** 
- The web interface uses your API key from the root `.env` file. No need to duplicate it in the web directory.
- You may see webpack deprecation warnings about `onAfterSetupMiddleware` and `onBeforeSetupMiddleware`. These are harmless warnings from react-scripts 5.0.1 and don't affect functionality.

### Performance Optimization with Redis Caching

If you have Redis installed, you can enable caching to dramatically speed up repeated queries:

```bash
# Install Redis (if not already installed)
brew install redis          # macOS
sudo apt install redis      # Ubuntu/Debian

# Start Redis
redis-server               # Or: brew services start redis (macOS)

# Use --enable-cache flag
ms "renewable energy" --enable-cache       # First run: 3-5 seconds
ms "renewable energy" --enable-cache       # Subsequent runs: <0.1 seconds (from cache)
```

**Benefits:**
- **10-100x faster** for repeated identical queries
- **Cost savings** by avoiding redundant API calls
- **Ideal for development** when iterating on the same topic
- **Automatic cache management** - no manual intervention needed

<details>
<summary>Manual Setup (Advanced)</summary>

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r config/requirements.txt

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Configure API (use root .env file)
echo 'GOOGLE_API_KEY="YOUR_API_KEY_HERE"' > .env
echo 'GOOGLE_GENAI_MODEL="gemini-2.5-flash"' >> .env

# Run commands
ms "sustainable transportation" "low-cost solutions"
ms coordinator
```

</details>

## Project Structure

```
eureka/
├── src/madspark/           # Core application
│   ├── agents/             # Agent definitions
│   ├── core/               # Coordinators & logic
│   ├── utils/              # Utilities
│   ├── cli/                # CLI interface
│   └── web_api/            # Web backend
├── tests/                  # Test suite (85%+ coverage)
├── web/frontend/           # React TypeScript app
├── docs/                   # Documentation
└── config/                 # Configuration files
```

## Development

### Quick Setup
```bash
# Install pre-commit hooks
pip install pre-commit && pre-commit install

# Verify environment
./scripts/check_dependencies.sh

# Create feature branch
git checkout -b feature/your-feature-name
```

### Testing
```bash
# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run all tests
pytest tests/ -v --cov=src --cov-report=html

# Run specific suites
pytest tests/test_agents.py -v           # Agent tests
pytest tests/test_integration.py -v     # Integration tests

# Frontend tests
cd web/frontend && npm test -- --coverage --watchAll=false
```

### CI/CD Pipeline

Optimized pipeline with **2-4 minute execution time**:
- **Quick Checks**: Python syntax, deprecated patterns (30s)
- **Parallel Testing**: Backend and frontend tests with coverage
- **Quality Checks**: Ruff linting, Bandit security scans
- **Docker Validation**: Syntax verification for web services

Key optimizations:
- Parallel test execution with pytest-xdist
- Conditional Python matrix (3.10 for PRs, full matrix for main)
- Performance test exclusion for PR CI
- Aggressive dependency caching

See [`docs/ci-policy.md`](docs/ci-policy.md) for complete CI management guidelines.

## Documentation

- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Common usage patterns
- **[Batch Processing Guide](docs/BATCH_PROCESSING_GUIDE.md)** - Process multiple themes
- **[Interactive Mode Guide](docs/INTERACTIVE_MODE_GUIDE.md)** - Conversational interface
- **[Web Interface Guide](docs/WEB_INTERFACE_GUIDE.md)** - Modern web UI

## Session Handover

**Last Updated**: August 1, 2025 07:17 AM JST

### Recently Completed

- ✅ **[PR #135](https://github.com/TheIllusionOfLife/Eureka/pull/135)**: Test expectations fix and mad_spark command tests (August 1, 2025)
  - **Test Expectations Fix**: Updated mock response validation to use pattern-based checks (Issue #119)
  - **Command Tests Implementation**: Replaced all 8 placeholder tests with real subprocess execution tests
  - **CI Compatibility**: Enhanced run.py to work in CI environments without virtual environment
  - **Code Quality**: Fixed linting issues, DRY violations, and test data pollution in bookmarks.json
  - **Argument Parsing Fix**: Corrected CLI simplified syntax handling to prevent context duplication
  - **Systematic PR Review**: Applied 4-phase protocol to address feedback from 5 automated reviewers
- ✅ **[PR #133](https://github.com/TheIllusionOfLife/Eureka/pull/133)**: Performance test markers for faster CI (August 1, 2025)
  - **Performance Optimization**: Achieved 30-50% CI speedup using pytest markers (@pytest.mark.slow, @pytest.mark.integration)
  - **Test Categorization**: Applied 47 markers across 6 test files for smart conditional execution (fast tests for PRs, full coverage on main)  
  - **Comprehensive Documentation**: Added TESTING_GUIDE.md with marker usage guidelines and best practices
  - **Systematic PR Review**: Successfully addressed feedback from 6 reviewers using 4-phase protocol (discover → extract → prioritize → fix)
  - **Mock Mode Compatibility**: Preserved skipif decorators for timeout tests - mock operations are instantaneous

- ✅ **[PR #132](https://github.com/TheIllusionOfLife/Eureka/pull/132)**: Enhanced JSON parsing for partial evaluations (August 1, 2025)  
  - **Enhanced Parsing**: Implemented multiple fallback strategies with bracket matching for incomplete responses
  - **ReDoS Prevention**: Limited regex repetition to 500 characters to prevent denial of service attacks
  - **Array Extraction**: Added `_extract_json_arrays` helper with proper bracket matching algorithm
  - **Issue Resolution**: Fixed coordinator evaluation parsing mismatch (Issue #118)

- ✅ **[PR #130](https://github.com/TheIllusionOfLife/Eureka/pull/130)**: AI-powered MultiDimensionalEvaluator implementation (July 31, 2025)
  - **Language-Agnostic**: Replaced keyword-based evaluation with AI-powered system supporting all languages
  - **Mock-Mode Compatible**: Maintained mock-first development with try/except SimpleNamespace pattern
  - **Explicit Failures**: No graceful degradation - clear error messages when API key not configured
  - **Human-Readable Prompts**: Context formatted as natural language instead of raw dictionaries
  - **Multi-Bot Review**: Successfully addressed feedback from claude[bot], coderabbitai[bot], cursor[bot], and gemini-code-assist[bot]

- ✅ **[PR #128](https://github.com/TheIllusionOfLife/Eureka/pull/128)**: UI improvements - collapsed sections by default (July 31, 2025)
  - Made improved idea and multi-dimensional evaluation sections collapsed for cleaner UI

- ✅ **[PR #127](https://github.com/TheIllusionOfLife/Eureka/pull/127)**: Web interface aliases and keyboard shortcuts (July 31, 2025)
  - Added convenient aliases for web interface management
  - Removed conflicting keyboard shortcuts for better UX

- ✅ **[PR #125](https://github.com/TheIllusionOfLife/Eureka/pull/125)**: Temperature range fix and CLI option consolidation (July 29, 2025)
  - **Temperature Range**: Expanded validation from 0.0-1.0 to 0.0-2.0 to support "wild" preset
  - **Option Cleanup**: Removed duplicate `--creativity` option in favor of `--temperature-preset`
  - **Test Coverage**: Added comprehensive test suite following TDD principles
  - **Documentation**: Updated all help text and README examples

- ✅ **[PR #123](https://github.com/TheIllusionOfLife/Eureka/pull/123)**: CLI improvements - automatic bookmarking, optional context, and flag passing (July 29, 2025)
  - **Automatic Bookmarking**: Changed from opt-in (`--bookmark-results`) to opt-out (`--no-bookmark`) approach
  - **Optional Context**: Made second parameter optional - users can now run `ms "topic"` without context
  - **Fixed Flag Passing**: The `ms` command alias now properly passes flags like `--enable-cache`
  - **Enhanced CLI Features**: Added `--remove-bookmark` command, improved help formatting, intelligent text truncation
  - **Redis Documentation**: Added comprehensive Redis caching setup guide (10-100x speedup benefits)
  - **Code Quality**: Removed duplicated code, added file locking, fixed cross-platform compatibility
  - **Bug Fixes**: Fixed overly aggressive lowercase idea filtering, undefined variable in exception handling

#### Next Priority Tasks

**Updated: August 1, 2025** - Based on recent completions and code analysis

All critical and high priority issues have been resolved! The following are medium/low priority improvements:

##### Medium Priority (Improve Quality)

1. **[MEDIUM] Document Command Aliases Strategy**
   - **Source**: PR #117 added mad_spark/madspark/ms aliases
   - **Context**: Need clear guidance on which is primary command
   - **Approach**: Add documentation section about command aliases
   - **Estimated Effort**: 1 hour

##### Low Priority/Future Improvements

2. **[LOW] Improve or Remove Logical Inference Feature**
   - **Problem**: `--logical` flag enables overly simplistic hardcoded templates
   - **Current State**: Methods return fixed strings like "Therefore, the consequent follows"
   - **Recommendation**: Either implement real logical inference or remove to avoid misleading users
   - **Estimated Effort**: 4-5 hours for proper implementation

3. **[LOW] Optimize MultiDimensional Evaluator Performance**
   - **Source**: PR #130 review feedback
   - **Current**: 7 sequential API calls per idea evaluation
   - **Improvement**: Parallel API calls could provide 7x speedup
   - **Approach**: Use asyncio for parallel calls, implement caching
   - **Estimated Effort**: 4-5 hours

4. **[LOW] Batch Processing Enhancement**
   - **Context**: CLI improvements from PR #123 showed UX gains
   - **Potential**: Implement `--batch` for processing multiple topics
   - **Approach**: Extend CLI infrastructure for batch operations
   - **Estimated Effort**: 4-6 hours

5. **[LOW] CI Performance Monitoring**
   - **Source**: PR #107 optimization gains
   - **Context**: Prevent CI time regression
   - **Approach**: GitHub Actions workflow to track duration trends
   - **Estimated Effort**: 3-4 hours

##### Feature Quality Assessment

Based on code analysis (July 31, 2025):
- ✅ **Multi-dimensional evaluation**: Sophisticated AI-powered system providing real value
- ⚠️ **Enhanced reasoning (--enhanced)**: Moderate value through context awareness
- ❌ **Logical inference (--logical)**: Too simplistic with hardcoded templates - needs rework

#### Previous Milestones

- ✅ **PR #115**: User-friendly setup and bookmark fixes (July 24, 2025)
  - Created `run.py` and `setup.sh` for 2-step installation (was 8+ steps)
  - Consolidated API key management to single `.env` file
  - Fixed bookmark API field mismatch (theme→topic, constraints→context)

- ✅ **PR #111**: Restored comprehensive integration tests
  - System, Docker, Web API, error handling, and performance tests
  - 759 lines of test coverage improvements

- ✅ **PR #107**: CI/CD performance optimization (20min → 2-4min, 85-90% improvement)
  - Conditional Python matrix, parallel execution, workflow separation

#### Known Issues & Follow-up Items

**Note**: All user-facing functionality works correctly.

#### Multi-Dimensional Evaluation System

**AI-Powered Language-Agnostic Evaluation (Implemented July 31, 2025):**
- **Previous Issue**: The system used English keyword matching, causing non-English text to receive meaningless default scores of 5.0
- **Solution**: Replaced keyword-based evaluation with AI-powered evaluation using Gemini API
- **Benefits**: 
  - All languages now receive accurate, meaningful evaluation scores
  - Clear error messages when API key is not configured
  - No misleading fallback to keyword matching

**Requirements:**
- Multi-dimensional evaluation now requires `GOOGLE_API_KEY` to be configured
- Without API key, the system will display clear error messages instead of providing misleading scores

#### Session Learnings

- **Multi-Reviewer PR Management**: Address ALL automated bot feedback systematically (cursor[bot], coderabbitai[bot], gemini-code-assist[bot])
- **Overly Aggressive Validation**: Avoid filtering valid inputs - lowercase idea filtering discarded legitimate results
- **Exception Handling Safety**: Initialize variables before try blocks to prevent NameError in cleanup code
- **Cross-Platform Compatibility**: Use platform detection and graceful fallbacks for OS-specific features like file locking
- **Code Duplication Elimination**: Extract duplicated logic into helper functions (e.g., text truncation utility)
- **Strategic Test Skipping**: Skip overly complex mocking tests in CI while preserving functional coverage
- **CLI Flag Preservation**: Ensure simplified command aliases properly pass all user flags to underlying implementations
- **Automatic Feature Adoption**: Opt-out approaches (auto-bookmark with --no-bookmark) increase feature adoption vs opt-in
- **Temperature Range Flexibility**: LLM temperature validation should match model capabilities (e.g., 0.0-2.0 for Gemini)
- **CLI Option Consolidation**: Remove duplicate options that confuse users (--creativity vs --temperature-preset)
- **Test-Driven CI Fixes**: Write failing tests first when fixing CI issues to ensure correct behavior
- **Systematic PR Review**: Always check all three GitHub API sources (PR comments, reviews, line comments)
- **Mock-Mode Compatibility**: Use try/except with SimpleNamespace for optional packages while maintaining mock-first development
- **Human-Readable AI Prompts**: Format context as natural language (e.g., "Theme: X. Constraints: Y") not raw dictionaries
- **Multi-Bot PR Review**: Successfully addressed feedback from 4+ review bots by fixing issues systematically
- **Test Implementation Best Practices**: See CLAUDE.md for detailed PR #135 technical learnings

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides
