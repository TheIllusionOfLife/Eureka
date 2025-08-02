# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.2%20Complete-success)](#project-status) [![Testing](https://img.shields.io/badge/Testing-85%25%20Coverage-success)](#testing) [![CI/CD](https://img.shields.io/badge/CI%2FCD-Optimized-brightgreen)](#development)

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API. 
Features specialized agents for idea generation, criticism, advocacy, and skepticism with advanced reasoning capabilities.

## 🚀 Key Features

- **🧠 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🚀 Batch API Optimization**: 50% fewer API calls with 45% cost savings through intelligent batching (NEW!)
- **📊 Real-time Monitoring**: Comprehensive token usage and cost tracking with detailed analytics
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

### Logical Inference (NEW!)

MadSpark now features LLM-powered logical inference that provides deep analytical reasoning for generated ideas. This replaces the previous hardcoded templates with genuine logical analysis.

**Key Features:**
- **Multiple Analysis Types**: Full reasoning, causal chains, constraint satisfaction, contradiction detection, and implications analysis
- **Confidence Scoring**: Each inference includes a confidence score (0-1) indicating the strength of the logical reasoning
- **Structured Output**: Clear inference chains showing step-by-step logical progression
- **Contextual Integration**: Inference considers theme, constraints, and evaluation scores

**Usage Examples:**
```bash
# Enable logical inference for comprehensive analysis
ms "renewable energy" "urban environment" --logical

# Combine with enhanced reasoning for maximum insight
ms "sustainable farming" "limited space" --enhanced --logical

# Use with multiple ideas for comparative logical analysis
ms "education innovation" --top-ideas 3 --logical --detailed
```

**Output Example:**
When logical inference is enabled, you'll see analysis like this in the critique:

```
🧠 Logical Inference Analysis:

Inference Chain:
  → Urban areas have limited horizontal space
  → Vertical solutions maximize space efficiency  
  → Rooftop gardens provide local food production
  → Community involvement ensures long-term sustainability

Conclusion: Vertical rooftop gardens are an optimal solution for urban food security

Confidence: 85%

Suggested Improvements: Consider hydroponic systems for higher yields in limited space
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

## 📊 Batch API Monitoring & Cost Analysis

MadSpark includes comprehensive monitoring for API usage and cost optimization. The system automatically tracks token usage, API call efficiency, and cost savings.

### Real-time Monitoring

All batch operations are monitored automatically with detailed metrics:

```bash
# View recent batch operations
python -m madspark.cli.batch_metrics --recent

# View comprehensive cost analysis  
python -m madspark.cli.batch_metrics

# Clear metrics history
python -m madspark.cli.batch_metrics --clear
```

### Performance Results

Real-world testing shows significant improvements with batch processing:

- **🚀 50% API Call Reduction**: 3 batch calls vs 6 individual calls for 2 candidates
- **💰 45% Cost Savings**: Skeptic and improve operations show excellent savings
- **📈 Token Efficiency**: ~1,298 tokens per item with detailed per-operation tracking
- **💵 Cost Transparency**: $0.0036 average cost per item with full breakdown

### Monitoring Features

- **📊 Real-time Metrics**: Token usage, duration, and cost tracking per batch operation
- **💡 Cost Effectiveness Analysis**: Automatic comparison vs individual API calls
- **📈 Session Summaries**: Detailed breakdowns by batch type and efficiency metrics
- **🔍 Performance Insights**: Items per second, tokens per item, and cost per operation
- **📋 Historical Tracking**: Persistent metrics logged to `~/.madspark/batch_metrics.jsonl`

### Example Monitoring Output

```
📊 Batch Type Analysis:
  advocate: 1 batch calls vs 2 individual calls (2.0 items/call)
  skeptic: 1 batch calls vs 2 individual calls (2.0 items/call) - 45% savings
  improve: 1 batch calls vs 2 individual calls (2.0 items/call) - 45% savings

📞 API Call Efficiency: 50.0% reduction
💵 Estimated cost: $0.0214 ($0.0036 per item)
```

The monitoring system ensures you get maximum value from your API usage while maintaining full transparency on costs and performance.

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

### Last Updated: August 02, 2025 06:39 PM JST

### Recently Completed

- ✅ **[PR #146](https://github.com/TheIllusionOfLife/Eureka/pull/146)**: LLM-powered logical inference engine (August 2, 2025)
  - **Feature Implementation**: Replaced hardcoded templates with genuine LLM-based logical reasoning
  - **5 Analysis Types**: FULL, CAUSAL, CONSTRAINTS, CONTRADICTION, IMPLICATIONS
  - **Integration**: Seamlessly integrated with enhanced reasoning system and async coordinator
  - **CLI Support**: `--logical` flag enables inference with confidence threshold filtering
  - **Comprehensive Testing**: Full test coverage including error handling and integration tests
  - **API Pattern Discovery**: Documented correct Google GenAI SDK usage pattern
- ✅ **[PR #145](https://github.com/TheIllusionOfLife/Eureka/pull/145)**: Updated session handover with accurate task status (August 2, 2025)
- ✅ **[PR #144](https://github.com/TheIllusionOfLife/Eureka/pull/144)**: Documentation update - session handover and learnings (August 2, 2025)
  - Updated Session Handover section with PR #143 completion details
  - Documented timeout functionality and command aliases implementation
  - Added technical learnings about test module patching and system configuration

- ✅ **[PR #143](https://github.com/TheIllusionOfLife/Eureka/pull/143)**: TDD Implementation - Timeout Functionality & Command Aliases (August 2, 2025)
  - **Timeout Implementation**: ThreadPoolExecutor-based timeout enforcement with proper cancellation
  - **Command Aliases**: Fully implemented mad_spark/madspark/ms commands with comprehensive tests
  - **Critical Fixes**: Temperature handling regression, reasoning engine initialization
  - **Test Infrastructure**: Enhanced timeout tests with proper module patching

- ✅ **[PR #141](https://github.com/TheIllusionOfLife/Eureka/pull/141)**: Batch API Optimization - 50% Fewer API Calls & Cost Savings (August 1, 2025)
  - **Performance**: Reduced API calls from O(N) to O(1) through intelligent batching
  - **Cost Savings**: 45% reduction in token usage for advocate/skeptic operations
  - **Comprehensive Testing**: Added extensive test suite for batch operations
  - **Error Handling**: Custom exception hierarchy (BatchAPIError, BatchParsingError) for robust error management
  - **Mock Support**: Full mock response generation with language detection
  - **CI Fixes**: Resolved all test failures including None response handling

- ✅ **[PR #139](https://github.com/TheIllusionOfLife/Eureka/pull/139)**: Refactored structured output code quality - DRY improvements (August 1, 2025)
  - **DRY Compliance**: Extracted duplicate response creation into `_create_success_response()` helper
  - **Test Quality**: Replaced redundant `pytest.skip()` calls with decorator-only approach
  - **Documentation**: Enhanced helper function docstrings with detailed parameter descriptions
  - **Code Safety**: Improved attribute checking with `getattr()` pattern

- ✅ **[PR #138](https://github.com/TheIllusionOfLife/Eureka/pull/138)**: Implemented frontend structured JSON support with backend integration (August 1, 2025)
  - **Feature**: Structured output detection prevents AI meta-commentary in responses
  - **Fix**: Mock mode cache bug preventing structured output detection
  - **Frontend Integration**: Added structured output flag to API responses
  - **Cleaning Logic**: Skip idea cleaning when structured output is detected

#### Next Priority Tasks

**Updated: August 02, 2025 06:39 PM JST**

Current priorities based on completion of logical inference feature:

##### High Priority

1. **[HIGH] Implement Shell Autocomplete**
   - **Source**: test_mad_spark_command.py line 277 (only skipped test in file)
   - **Context**: Tab completion for commands (coordinator, test, --help, --version) and options
   - **Approach**: Add bash/zsh completion scripts to src/madspark/bin/
   - **Estimated Effort**: 2-3 hours

2. **[HIGH] Web Interface Integration for Logical Inference**
   - **Source**: PR #146 Future Enhancements
   - **Context**: Backend logical inference is complete, needs frontend display
   - **Approach**: Add logical inference toggle and results display to React UI
   - **Estimated Effort**: 3-4 hours

3. **[HIGH] Add Colored Output to setup.sh**
   - **Source**: test_setup_enhancements.py line 162 (only skipped test in file)
   - **Context**: Enhance setup.sh with ANSI color codes for better UX
   - **Approach**: Add green for success messages, red for errors
   - **Estimated Effort**: 1-2 hours

#### Known Issues / Blockers

- **None currently**: All major CI issues resolved, all tests passing

##### Medium Priority (Enhancements)

4. **[MEDIUM] Expand Structured Output Logging**
   - **Source**: Currently only implemented in App.tsx (lines 313-317)
   - **Status**: Basic implementation exists, could be expanded
   - **Approach**: Add similar logging to ResultsDisplay.tsx and other components
   - **Estimated Effort**: 1-2 hours

##### Already Completed (Investigation Findings)

- ✅ **Error Handling in structured_output_check.py**: Already uses specific exception types (ImportError, AttributeError)
- ✅ **Command Aliases Documentation**: Fully documented in docs/COMMAND_ALIASES.md (212 lines)
- ✅ **Structured Output Logging**: Basic implementation exists in App.tsx

##### Low Priority/Future Improvements

5. **[LOW] Optimize MultiDimensional Evaluator Performance**
   - **Source**: PR #130 review feedback
   - **Current**: 7 sequential API calls per idea evaluation
   - **Improvement**: Parallel API calls could provide 7x speedup
   - **Approach**: Use asyncio for parallel calls, implement caching
   - **Estimated Effort**: 4-5 hours

6. **[LOW] Batch Processing Enhancement**
   - **Context**: CLI improvements from PR #123 showed UX gains
   - **Potential**: Implement `--batch` for processing multiple topics
   - **Approach**: Extend CLI infrastructure for batch operations
   - **Estimated Effort**: 4-6 hours

##### Summary of Investigation

**Total Skipped Tests Found**: 2 (not 6 as previously stated)
- `test_mad_spark_autocomplete` in test_mad_spark_command.py
- `test_setup_shows_colored_output` in test_setup_enhancements.py

**Tasks Already Completed**:
- Command aliases documentation (docs/COMMAND_ALIASES.md)
- Structured output logging (implemented in App.tsx)
- Error handling improvements (structured_output_check.py)

##### Feature Quality Assessment

Based on code analysis (August 2, 2025):
- ✅ **Multi-dimensional evaluation**: Sophisticated AI-powered system providing real value
- ✅ **Logical inference (--logical)**: LLM-powered reasoning engine with 5 analysis types (PR #146)
- ⚠️ **Enhanced reasoning (--enhanced)**: Moderate value through context awareness

#### Technical Learnings from PR #143 (August 2, 2025)

Key technical insights from PR #143 implementation:

1. **Test Module Patching Pattern**: Mock functions where they're imported/used, not where they're defined
   - Example: Patch `coordinator_batch.improve_ideas_batch`, not `agents.idea_generator.improve_ideas_batch`

2. **System Configuration Regression Prevention**: Always verify class defaults vs constants match
   - TemperatureManager defaults: (0.91, 0.28, 0.7, 0.7) ≠ Constants: (0.9, 0.3, 0.5, 0.5)
   - Impact: Different AI behavior when replacing constants with class instances

3. **Automated Bot Feedback Value**: Cursor bot caught 3 critical issues that CI missed
   - Temperature handling regression, reasoning engine initialization, file placement violations
   - Pattern: Take bot feedback seriously, investigate thoroughly before dismissing

4. **Environment Management in Tests**: Use autouse fixtures for clean setup/teardown
   - Eliminates manual env variable management in individual tests
   - Prevents test pollution and ensures consistent isolation

#### Session Learnings from PR #146 (August 2, 2025)

- **Google GenAI API Pattern**: Always use `genai_client.models.generate_content()` with `genai.types.GenerateContentConfig`
- **Nested API Mock Testing**: Mock the complete structure (`mock_genai_client.models = mock_models`)
- **Balanced Exception Handling**: Include RuntimeError for API errors while satisfying reviewer requests for specific exceptions
- **4-Phase PR Review Success**: Systematic approach (Discover → Extract → Verify → Fix) handled 5 reviewers efficiently
- **TDD in Complex Features**: Comprehensive test suite written first ensured smooth implementation
- **DRY Principle in Systems**: Share instances (LogicalInferenceEngine) between components to avoid duplication

#### Previous Session Learnings

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
- **Cache Bug Pattern**: Never cache None/mock results that block real client checks (PR #138)
- **DRY Helper Functions**: Extract duplicate response creation into reusable helpers (PR #139)
- **Test Skip Best Practice**: Use @pytest.mark.skip only, avoid redundant pytest.skip() calls (PR #139)
- **Structured Output**: Successfully eliminates AI meta-commentary from responses (PR #138-139)
- **Batch API Optimization**: Reduced API calls by 50% through intelligent batching with proper error handling (PR #141)
- **None Response Handling**: Always check for None before json.loads() in batch processing functions (PR #141)
- **Test Expectations**: Mock mode tests should match actual mock behavior, not assume single-item processing (PR #141)
- **CI Iteration Strategy**: Use `/fix_ci` with repeat-until-pass directive for efficient CI debugging (PR #141)

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides
