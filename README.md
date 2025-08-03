# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.2%20Complete-success)](#project-status) [![Testing](https://img.shields.io/badge/Testing-85%25%20Coverage-success)](#testing) [![CI/CD](https://img.shields.io/badge/CI%2FCD-Optimized-brightgreen)](#development)

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API. 
Features specialized agents for idea generation, criticism, advocacy, and skepticism with advanced reasoning capabilities.

## 🚀 Key Features

- **🧠 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🎯 Structured Output**: Google Gemini's structured JSON output for clean, consistent formatting (NEW!)
- **🚀 Batch API Optimization**: 50% fewer API calls with 45% cost savings through intelligent batching
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

# Enhanced reasoning with advocate & skeptic agents    
ms "quantum computing" --enhanced

# Add logical inference analysis
ms "renewable energy" --logical

# Cache results with Redis for instant repeated queries                   
ms "how the universe began" --top-ideas 3 --enable-cache

# Set custom timeout (default: 600 seconds / 10 minutes)
ms "complex analysis" --timeout 300     # 5 minute timeout
ms "quick idea" --timeout 60 --async   # 1 minute timeout (async mode enforces timeout)

# Combined options
ms "create a new game concept as a game director" "implementable within a month, solo" --top-ideas 5 --temperature-preset creative --enhanced --logical --enable-cache --detailed

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

### Understanding MadSpark Options

**Core Features (Always Enabled):**
- **Multi-Dimensional Evaluation**: Every idea is automatically scored across 7 dimensions:
  - Feasibility, Innovation, Impact, Cost-Effectiveness, Scalability, Safety Score, Timeline
  - Provides comprehensive assessment without any flags needed

**Optional Enhancement Flags:**

1. **`--enhanced` (Enhanced Reasoning)**
   - Adds two specialized agents to the workflow:
     - 🔷 **Advocate Agent**: Analyzes strengths, opportunities, and addresses potential concerns
     - 🔶 **Skeptic Agent**: Identifies critical flaws, risks, questionable assumptions, and missing considerations
   - Use when: You need balanced perspectives showing both positive potential and realistic challenges

2. **`--logical` (Logical Inference)**
   - Adds formal logical analysis with:
     - 🔍 **Causal Chains**: "If A then B" reasoning paths
     - **Constraint Satisfaction**: Checks if requirements are met
     - **Contradiction Detection**: Identifies conflicting elements
     - **Implications**: Reveals hidden consequences
   - Use when: You need rigorous logical validation and deeper analytical reasoning

**Example Comparison:**
```bash
# Basic (Multi-dimensional evaluation only)
ms "urban farming"
# Output: Ideas with 7-dimension scores

# With Enhanced Reasoning
ms "urban farming" --enhanced  
# Output: Ideas + Advocacy/Skepticism sections

# With Logical Inference
ms "urban farming" --logical
# Output: Ideas + Logical analysis chains

# Combined for maximum insight
ms "urban farming" --enhanced --logical --detailed
# Output: Complete analysis with all agents and reasoning
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

### Structured Output Enhancement (NEW!)

MadSpark now uses Google Gemini's structured output feature for cleaner, more consistent formatting. This eliminates parsing issues and ensures reliable display across all output formats.

**Key Improvements:**
- **No Meta-Commentary**: Clean responses without "Here's my analysis..." or similar prefixes
- **Consistent Formatting**: Structured JSON ensures reliable markdown conversion
- **Eliminated Parsing Errors**: No more truncated output or format inconsistencies
- **Enhanced Display Quality**: Professional formatting for scores, sections, and bullet points

**Format Fixes Implemented:**
- ✅ Removed redundant "Text:" prefix from idea descriptions
- ✅ Fixed score delta display (no more "+-0" formatting issues)
- ✅ Consistent bullet points (• instead of mixed formats)
- ✅ Proper section headers (STRENGTHS, OPPORTUNITIES, etc.)
- ✅ Clean line breaks between sections
- ✅ Reliable logical inference result display

**Technical Details:**
- Uses `response_mime_type="application/json"` with `response_schema`
- Backward compatible with text-based responses for fallback scenarios
- All agents (IdeaGenerator, Critic, Advocate, Skeptic) support structured output
- Applies to both individual and batch processing modes

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

Real-world testing shows significant improvements with comprehensive optimizations:

**🚀 Major Performance Optimizations (August 2025)**:
- **⚡ 60-70% Execution Time Reduction**: Complex queries reduced from 9-10 minutes to 2-3 minutes
- **🔄 Batch Logical Inference**: 80% API call reduction (5 calls → 1 call)
- **⚙️ Parallel Processing**: 50% improvement for advocacy/skepticism operations
- **📈 Combined API Optimization**: 30% fewer total API calls (13 → 9 calls)

**Previous Batch Processing Improvements**:
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
- **[Cost & Time Analysis](docs/COST_TIME_ANALYSIS.md)** - Detailed pricing and performance metrics

## Session Handover

### Last Updated: August 04, 2025 05:41 AM JST

#### Recently Completed

- ✅ **[PR #154](https://github.com/TheIllusionOfLife/Eureka/pull/154)**: Comprehensive Performance Optimization - 60-70% Execution Time Reduction (August 4, 2025)
  - **Major Performance Achievement**: Reduced complex query execution time from 9-10 minutes to 2-3 minutes
  - **Systematic PR Review Success**: Applied 4-phase protocol to address feedback from 5 AI reviewers
  - **Critical Bug Fixes**: Fixed skeptic agent input bug (used evaluation_detail instead of advocacy_output)
  - **API Optimization**: Implemented batch logical inference (80% API call reduction)
  - **Code Quality**: Eliminated DRY violations with reusable helper methods
  - **Error Handling**: Consolidated duplicate error handling patterns across codebase
  
- ✅ **[PR #150](https://github.com/TheIllusionOfLife/Eureka/pull/150)**: Web Interface Logical Inference Display (August 3, 2025)
  - Fixed broken JSON display for Advocacy/Skepticism sections
  - Added missing logical inference display functionality
  - Fixed conditional rendering based on Enhanced Reasoning flag
  - Improved type safety with proper TypeScript interfaces
  - Extracted rendering logic to reusable utilities (~40% code reduction)
  
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

1. **[HIGH] Fix Test Implementation Mismatches**
   - **Source**: Code investigation revealed tests expecting different APIs than implemented
   - **Context**: Tests exist but expect wrong method names or behaviors
   - **Concrete Sub-tasks**:
     - [ ] Fix ContentSafetyFilter tests - change `is_safe()` calls to use `sanitize_content()` API
     - [ ] Update 5 auto-bookmark tests for new CLI structure (currently skipped)
     - [ ] Align test expectations with actual implementations
   
2. **[MEDIUM] Complete Enhanced Error Handling**
   - **Source**: Production readiness requirements
   - **Context**: Retry logic exists, but user-facing error handling incomplete
   - **Concrete Sub-tasks**:
     - [ ] Add React ErrorBoundary to `web/frontend/src/App.tsx`
     - [ ] Create user-friendly error messages enum in `utils/error_messages.py`
     - [ ] Add error tracking/reporting integration (e.g., Sentry)
     - [x] ~~Implement retry logic~~ (Already implemented in `agent_retry_wrappers.py`)

3. **[MEDIUM] Frontend Performance & Testing**
   - **Source**: Web interface optimization needs
   - **Context**: Backend optimized, frontend needs attention
   - **Concrete Sub-tasks**:
     - [ ] Optimize React re-renders in `web/frontend/src/components/IdeaList.tsx`
     - [ ] Add frontend component tests for error states
     - [ ] Add edge case tests for empty/null responses in frontend
     - [ ] Profile and optimize WebSocket message handling

#### Known Issues / Blockers

- **None currently**: All major CI issues resolved, all tests passing

#### Session Learnings

- **Systematic Multi-Step Fix Implementation**: Priority-based approach (Critical → High → Medium → Low) ensures comprehensive issue resolution without missing bugs
- **DRY Violation Elimination**: Extract duplicate patterns into reusable helper methods (e.g., `_handle_agent_output_error`, `_format_logical_inference_fallback`)
- **4-Phase PR Review Protocol Success**: Successfully managed 5 AI reviewers (claude[bot], coderabbitai[bot], github-actions[bot], cursor[bot], gemini-code-assist[bot]) systematically
- **Helper Method Pattern**: Consolidate duplicate error handling across modules reduces maintenance burden and improves consistency
- **Targeted Verification Strategy**: Test specific changed functionality before full CI saves time and catches issues early
- **Sequential vs Parallel Agent Execution**: Fixed critical bug where skeptic agent received wrong input by changing from parallel to sequential advocacy→skepticism flow


##### Historical Context (Previous Sessions)

**Major Infrastructure Completed**:
- ✅ **Performance Optimization Foundation**: Batch API processing, Redis caching, multi-dimensional evaluation
- ✅ **Testing Infrastructure**: Comprehensive test suite with 90%+ coverage across all modules  
- ✅ **Logical Inference Engine**: LLM-powered reasoning with 5 analysis types (FULL, CAUSAL, CONSTRAINTS, CONTRADICTION, IMPLICATIONS)
- ✅ **Web Interface**: React frontend with TypeScript, real-time WebSocket updates, error handling
- ✅ **CI/CD Pipeline**: Optimized 2-4 minute execution with parallel testing and smart caching

**Technical Architecture Established**:
- Standard `src/madspark/` package structure with agents, core, utils, cli modules
- Mock-first development enabling API-free testing and development
- Try/except fallback patterns for multi-environment compatibility  
- Structured output support using Google Gemini API with backward compatibility

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides
