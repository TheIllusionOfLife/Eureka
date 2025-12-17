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

**For CLI Usage:**
- Python 3.10+ (required for TypedDict and modern features)
- Google Gemini API key (optional - Ollama/mock mode available)
- Ollama (optional - for free local inference, Docker not required)

**For Web Interface:**
- Docker and Docker Compose
- **~12GB disk space** (for Ollama models - gemma3:4b + gemma3:12b)
- Google Gemini API key (optional - Ollama is auto-configured in Docker)

### CLI Installation

```bash
# Clone the repo
git clone https://github.com/TheIllusionOfLife/Eureka.git
cd Eureka

# Run interactive setup for CLI commands (mad_spark/ms)
./scripts/setup.sh

# Configure your API key (for real AI responses)
mad_spark config  # Interactive configuration
```

### Web Interface Installation

```bash
# After cloning the repo
cd Eureka/web

# Run interactive setup (auto-downloads Ollama models)
./setup.sh

# Follow the prompts to choose:
# 1) Ollama (Free, Local) - Recommended, downloads ~12GB models
# 2) Gemini (Cloud, Requires API Key)
# 3) Mock (Testing only, no AI)

# Access the interface at http://localhost:3000
```

**Note:** You can run both setup scripts to use both CLI and web interface!

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

### Usage

```bash
# Get help and see all available options
ms --help

# Basic usage with any alias
# command "topic" "context"
mad_spark "how to reduce carbon footprint?" "small business"
madspark "innovative teaching methods" "high school science"
ms "Come up with innovative ways to teach math" "elementary school"

# Single argument works too - context will use default
ms "future technology"                                                 

# Output modes for different needs
ms "healthcare AI" --brief              # Quick summary (default)
ms "education innovation" --detailed     # Full agent analysis
ms "climate solutions" --simple         # Clean

# Advanced options
# Generate ideas with high creativity. Check `ms --help` for more options.
ms "space exploration" --top-ideas 3 --temperature-preset creative

# Enhanced reasoning with advocate & skeptic agents    
ms "quantum computing" --enhanced

# Add logical inference analysis
ms "renewable energy" --logical

# Cache results with Redis for instant repeated queries                   
ms "how the universe began" --enable-cache

# Combined options
ms "create a new game concept as a game director" "implementable within a month, solo" --top-ideas 5 --temperature-preset creative --enhanced --logical --enable-cache --detailed
```

### Multi-Modal Input

Enhance idea generation with visual and document context - provide images, PDFs, documents, and URLs alongside text prompts.

**Quick Examples:**
```bash
# Add images for context
ms "Modern app redesign" "Clean, minimal" --image mockup.png --image wireframe.jpg

# Analyze documents
ms "Summarize findings" --file research.pdf --url https://competitor.com
```

**Supported Formats:**
- **Images**: PNG, JPG, JPEG, WebP, GIF, BMP (max 8MB)
- **Documents**: PDF (max 40MB), TXT, MD, DOC, DOCX (max 20MB)
- **URLs**: HTTP/HTTPS

**📖 For Python API usage, detailed examples, and best practices, see [`docs/MULTIMODAL_GUIDE.md`](docs/MULTIMODAL_GUIDE.md)**

### LLM Provider Selection (Ollama by Default)

MadSpark uses a multi-LLM provider system with **Ollama as the default** for cost-free local inference, automatically falling back to Gemini when needed.

**Installing Ollama for CLI (Optional):**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download

# Pull the models used by MadSpark (non-quantized for reliable JSON output)
ollama pull gemma3:4b       # Fast tier (~3.3GB)
ollama pull gemma3:12b      # Balanced tier (~8.1GB)

# Verify installation
ollama list
```

**Usage:**

```bash
# Default: Auto-select provider (Ollama primary, Gemini fallback)
# Runs on Ollama for FREE when available!
ms "urban farming" --show-llm-stats

# Force specific provider
ms "quantum computing" --provider gemini    # Cloud API (paid)

# Control model quality tier (default: balanced)
ms "space exploration" --model-tier fast      # gemma3:4b (~3.3GB, quick)
ms "climate solutions" --model-tier balanced  # gemma3:12b (~8.1GB, default)

# Cache management (enabled by default)
ms "education innovation" --no-cache       # Disable caching
ms --clear-cache "healthcare AI"           # Clear cache first

# Disable fallback (fail if primary provider unavailable)
ms "future transportation" --no-fallback

# Track tokens, cost, cache hits
ms "AI in 2035" --show-llm-stats
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

### Bookmark Management

MadSpark automatically saves all generated ideas in CLI interface as bookmarks for future reference and remixing. 
Each bookmark includes the improved idea text, score, topic, and timestamp.

#### Key Features:
- **Automatic Deduplication**: Uses Jaccard similarity (default threshold: 0.8) to prevent saving duplicate ideas
- **Smart Display**: Bookmarks are truncated to 300 characters in list view for better readability
- **Full Text Storage**: Complete idea text is preserved in the bookmarks file
- **Flexible Management**: Add tags, search, remove, and remix bookmarks easily

```bash
# Generate ideas with custom tags
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

### Web Interface Usage

**Features:**
- All the features that the CLI interface has
- Interactive bookmark management
- Export results in multiple formats
- Keyboard shortcuts for power users

```bash
cd web && ./setup.sh            # Initial setup (interactive)
cd web && docker compose up -d  # Start services. Or use `docker compose restart` to restart.
Access at http://localhost:3000
docker compose logs -f          # View logs
docker compose down            # Stop services
```

<details>
<summary><b>Advanced: Shell Aliases (Optional)</b></summary>

For power users who want quick commands from anywhere:

```bash
# Add to your ~/.zshrc or ~/.bashrc:
alias madspark-web="cd ~/Eureka/web && docker compose up -d"
alias madspark-web-stop="cd ~/Eureka/web && docker compose down"
alias madspark-web-logs="cd ~/Eureka/web && docker compose logs -f"

# Reload shell configuration
source ~/.zshrc  # or ~/.bashrc

# Use the aliases from anywhere
madspark-web       # Start at http://localhost:3000
madspark-web-logs  # View logs
madspark-web-stop  # Stop services
```

</details>

**Notes:**
- First startup downloads ~12GB of Ollama models (5-15 minutes depending on internet speed)
- You may see webpack deprecation warnings - these are harmless and don't affect functionality
- For detailed web interface documentation, see `web/README.md`

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

## Project Structure

```
eureka/
├── src/madspark/           # Core application
│   ├── agents/             # Agent definitions & response schemas
│   ├── core/               # Coordinators & enhanced reasoning
│   ├── utils/              # Utilities
│   │   ├── json_parsing/   # Structured JSON parsing
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

MadSpark provides centralized configuration through `src/madspark/config/execution_constants.py`. Available configuration classes: `MultiModalConfig`, `TimeoutConfig`, `ConcurrencyConfig`, `RetryConfig`, `LimitsConfig`, `ThresholdConfig`, `TemperatureConfig`, `ContentSafetyConfig`.

**Quick Example:**
```python
from madspark.config.execution_constants import TimeoutConfig
TimeoutConfig.IDEA_GENERATION_TIMEOUT = 60  # Adjust workflow timeouts
```

**📖 For complete configuration details, examples, and best practices, see [`docs/CONFIGURATION_GUIDE.md`](docs/CONFIGURATION_GUIDE.md)**

## Development

**Quick Setup:**
```bash
pip install pre-commit && pre-commit install
./scripts/check_dependencies.sh
git checkout -b feature/your-feature-name
```

**Quick Testing:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
pytest tests/ -v --cov=src --cov-report=html
```

**📖 For comprehensive development workflows, testing strategies, and CI/CD guidelines, see:**
- Testing: README has basic commands above; detailed testing guide coming soon
- CI/CD: [`docs/ci-policy.md`](docs/ci-policy.md) - Complete CI management guidelines

## Documentation

- **[System Architecture](docs/ARCHITECTURE.md)** - Complete technical architecture, data flows, and component details
- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Common usage patterns
- **[Batch Processing Guide](docs/BATCH_PROCESSING_GUIDE.md)** - Process multiple topics
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

