# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.2%20Complete-success)](#project-status) [![Testing](https://img.shields.io/badge/Testing-85%25%20Coverage-success)](#testing) [![CI/CD](https://img.shields.io/badge/CI%2FCD-Optimized-brightgreen)](#development)

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API. 
Features specialized agents for idea generation, criticism, advocacy, and skepticism with advanced reasoning capabilities.

## 🚀 Key Features

- **🧠 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🎯 Structured Output**: Google Gemini's structured JSON output for clean, consistent formatting
- **🦙 Multi-LLM Support**: Ollama (local, free) with Gemini fallback - automatic provider selection (NEW!)
- **🖼️ Multi-Modal Input**: CLI and API support for images, PDFs, documents, and URLs as context
- **💾 Response Caching**: Disk-based caching with 30-50% reduction in API calls
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

# Set custom timeout (default: 1200 seconds / 20 minutes)
ms "complex analysis" --timeout 300     # 5 minute timeout
ms "quick idea" --timeout 60 --async   # 1 minute timeout (async mode enforces timeout)

# Combined options
ms "create a new game concept as a game director" "implementable within a month, solo" --top-ideas 5 --temperature-preset creative --enhanced --logical --enable-cache --detailed
```

### Multi-Modal Input (NEW!)

Enhance your idea generation with visual and document context! Multi-modal inputs allow you to provide images, PDFs, documents, and URLs alongside your text prompts for richer, more contextual idea generation.

#### CLI Usage (Recommended)

```bash
# Single URL for context
ms "Improve our landing page" "Increase conversions" --url https://competitor.com

# Multiple images for visual inspiration
ms "Modern app redesign" "Clean, minimal" --image mockup.png --image wireframe.jpg

# Analyze documents (PDFs, text files, etc.)
ms "Summarize research findings" "Key insights" --file research.pdf --file data.csv

# Combined multi-modal inputs
ms "Product improvement ideas" "User-focused" \
  --url https://reviews.com \
  --file feedback.pdf \
  --image current-ui.png
```

#### Python API Usage

```python
from madspark.agents.idea_generator import generate_ideas

# Generate ideas with image context
ideas = generate_ideas(
    topic="UI/UX improvements",
    context="Mobile app redesign",
    multimodal_files=["mockup.png"]
)

# Analyze PDFs for insights
ideas = generate_ideas(
    topic="Market strategy",
    context="Competitive analysis",
    multimodal_files=["report.pdf"]
)

# Reference competitor websites
ideas = generate_ideas(
    topic="Feature roadmap",
    context="E-commerce platform",
    multimodal_urls=["https://competitor.com"]
)

# Mix files and URLs
ideas = generate_ideas(
    topic="Design system",
    context="Best practices",
    multimodal_files=["current_design.png"],
    multimodal_urls=["https://dribbble.com/shots/..."]
)
```

#### Supported Formats

- **Images**: PNG, JPG, JPEG, WebP, GIF, BMP (max 8MB each)
- **Documents**: PDF (max 40MB), TXT, MD, DOC, DOCX (max 20MB each)
- **URLs**: HTTP/HTTPS (competitor sites, references, documentation)

**📖 See [Multi-Modal Guide](docs/MULTIMODAL_GUIDE.md) for comprehensive documentation, examples, and best practices.**

### LLM Provider Selection (Ollama-First by Default!)

MadSpark uses a multi-LLM provider system with **Ollama as the default** for cost-free local inference, automatically falling back to Gemini when needed:

```bash
# Default: Auto-select provider (Ollama primary, Gemini fallback)
# Runs on Ollama for FREE when available!
ms "urban farming" --show-llm-stats

# Force specific provider
ms "AI healthcare" --provider ollama        # Local inference (FREE)
ms "quantum computing" --provider gemini    # Cloud API (paid)

# Control model quality tier
ms "space exploration" --model-tier fast      # gemma3:4b (quick)
ms "climate solutions" --model-tier balanced  # gemma3:12b (better)
ms "renewable energy" --model-tier quality    # gemini-2.5-flash (best)

# Cache management (enabled by default)
ms "education innovation" --no-cache       # Disable caching
ms --clear-cache "healthcare AI"           # Clear cache first

# Disable fallback (fail if primary provider unavailable)
ms "future transportation" --no-fallback

# Disable router entirely (use direct Gemini API like before)
ms "legacy workflow" --no-router
```

**Provider Features:**
- **Ollama (Primary)**: Local inference with gemma3 models, $0 cost, image support
- **Gemini (Fallback)**: Cloud inference, PDF/URL support, higher quality
- **Response Caching**: Disk-based cache with 24h TTL, 30-50% fewer API calls
- **Automatic Fallback**: Seamlessly switches providers on failure
- **Usage Statistics**: Track tokens, cost, cache hits with `--show-llm-stats`

**Web Interface LLM Controls:**
The web interface includes advanced LLM settings:
- AI Provider selector (Auto/Ollama/Gemini)
- Model Quality Tier (Fast/Balanced/Quality)
- Response Caching toggle
- LLM usage metrics display (tokens, cost, cache hit rate)

### Standard CLI Usage

```bash
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
- Uses `response_mime_type="application/json"` with `response_schema` for all LLM interactions
- **Enhanced JSON Parsing**: Dedicated `json_parsing` package with 5 progressive fallback strategies
- **Pre-compiled Patterns**: 15-20% faster parsing using pre-compiled regex patterns
- **Telemetry Tracking**: Monitors parsing strategy usage for optimization
- Backward compatible with text-based responses for fallback scenarios
- All agents (IdeaGenerator, Critic, Advocate, Skeptic) support structured output
- Applies to both individual and batch processing modes
- **Logical Inference**: 5 specialized schemas for reasoning analysis (full, causal, constraints, contradiction, implications)

**Example: Using JsonParser Directly**

For developers integrating with MadSpark's parsing infrastructure:

```python
from madspark.utils.json_parsing import JsonParser

# Create parser instance
parser = JsonParser()

# Parse AI response with automatic fallback
response_text = '{"idea": "Smart energy grid", "score": 8.5}'
result = parser.parse(response_text)
# Returns: {"idea": "Smart energy grid", "score": 8.5}

# Works with messy/mixed content
messy_text = '''
Here are some ideas:
[{"id": 1, "text": "Solar panels"}, {"id": 2, "text": "Wind power"}]
Hope this helps!
'''
result = parser.parse(messy_text, expected_count=2)
# Returns: [{"id": 1, "text": "Solar panels"}, {"id": 2, "text": "Wind power"}]

# View parsing statistics (which strategies succeeded)
stats = parser.telemetry.get_stats()
# Example: {'DirectJson': 1, 'JsonArrayExtraction': 1, 'total': 2}
```

**Migration from Legacy Parsing**:

```python
# Old way (deprecated)
from madspark.utils.utils import parse_json_with_fallback
result = parse_json_with_fallback(text)  # Triggers DeprecationWarning

# New way (recommended)
from madspark.utils.json_parsing import JsonParser
parser = JsonParser()
result = parser.parse(text)
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

The MadSpark web interface provides a modern React-based UI for generating ideas with real-time progress updates. **Now with multi-modal support!** Add URLs and upload files directly from the browser for enhanced context.

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
- **Multi-modal input: Add URLs and upload files (PDFs, images, documents)**
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
│   ├── agents/             # Agent definitions & response schemas
│   ├── core/               # Coordinators & enhanced reasoning
│   ├── utils/              # Utilities
│   │   ├── json_parsing/   # Structured JSON parsing (NEW!)
│   │   │   ├── patterns.py      # Pre-compiled regex patterns
│   │   │   ├── strategies.py    # 5 fallback parsing strategies
│   │   │   ├── parser.py        # JsonParser orchestrator
│   │   │   └── telemetry.py     # Usage tracking
│   │   └── logical_inference_engine.py  # LLM-based reasoning
│   ├── cli/                # CLI interface
│   └── web_api/            # Web backend
├── tests/                  # Test suite (90%+ coverage)
├── web/frontend/           # React TypeScript app
├── docs/                   # Documentation
└── config/                 # Configuration files
```

## ⚙️ Configuration

MadSpark provides centralized configuration through `src/madspark/config/execution_constants.py`.

### Configuration Classes

```python
from madspark.config.execution_constants import (
    MultiModalConfig,      # File size limits, supported formats
    TimeoutConfig,         # Workflow step timeouts
    ConcurrencyConfig,     # Thread pool sizes
    RetryConfig,           # Agent retry parameters
    LimitsConfig,          # Size limits, cache settings
    ThresholdConfig,       # Similarity thresholds
    TemperatureConfig,     # LLM temperature values
    ContentSafetyConfig    # Gemini safety settings
)
```

### Key Configuration Examples

**Adjust Timeouts:**
```python
# Default workflow step timeouts (in seconds)
TimeoutConfig.IDEA_GENERATION_TIMEOUT = 60
TimeoutConfig.EVALUATION_TIMEOUT = 60
TimeoutConfig.IMPROVEMENT_TIMEOUT = 120
```

**Multi-Modal File Limits:**
```python
MultiModalConfig.MAX_FILE_SIZE = 20_000_000      # 20MB
MultiModalConfig.MAX_IMAGE_SIZE = 8_000_000      # 8MB
MultiModalConfig.MAX_PDF_SIZE = 40_000_000       # 40MB
```

**Concurrency Settings:**
```python
ConcurrencyConfig.MAX_ASYNC_WORKERS = 4          # Async coordinator
ConcurrencyConfig.MAX_BATCH_WORKERS = 4          # Batch operations
```

**Agent Retry Behavior:**
```python
RetryConfig.IDEA_GENERATOR_MAX_RETRIES = 3
RetryConfig.CRITIC_MAX_RETRIES = 3
RetryConfig.ADVOCATE_MAX_RETRIES = 2
```

For complete configuration details, see `docs/CONFIGURATION_GUIDE.md`.

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

- **[System Architecture](docs/ARCHITECTURE.md)** - Complete technical architecture, data flows, and component details
- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Common usage patterns
- **[Batch Processing Guide](docs/BATCH_PROCESSING_GUIDE.md)** - Process multiple themes
- **[Interactive Mode Guide](docs/INTERACTIVE_MODE_GUIDE.md)** - Conversational interface
- **[Web Interface Guide](docs/WEB_INTERFACE_GUIDE.md)** - Modern web UI
- **[Cost & Time Analysis](docs/COST_TIME_ANALYSIS.md)** - Detailed pricing and performance metrics

## Session Handover

For detailed session handover information including recently completed work, next priority tasks, session learnings, and historical context, see **[session_handover.md](session_handover.md)**.

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides

