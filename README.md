# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.1%20Complete-success)](#project-status) [![Enhancement](https://img.shields.io/badge/Enhancement-Feedback%20Loop%20MERGED-brightgreen)](#feedback-loop-enhancement) [![Testing](https://img.shields.io/badge/Testing-95%25%20Coverage-success)](#testing) [![Next](https://img.shields.io/badge/Next-User%20Testing-blue)](#roadmap)

This project implements a sophisticated multi-agent system for idea generation and refinement using Google's Gemini API with advanced reasoning capabilities. It includes specialized agents for idea generation, criticism, advocacy, and skepticism, orchestrated by a coordinator enhanced with context-aware reasoning, logical inference, and multi-dimensional evaluation.

## 🚀 NEW: Feedback Loop Enhancement

The system now implements a **feedback loop mechanism** where agent outputs are used to generate improved ideas:

### Previous Flow (Static):
```
IdeaGen → Critic(score₁) → Advocate → Skeptic → [END - just display]
```

### New Flow (Dynamic Improvement):
```
IdeaGen → Critic(score₁) → Advocate → Skeptic → IdeaGen_v2 → Critic(score₂) → [Display with comparison]
```

### Key Features:
- **Structured Agent Outputs**: Advocate and Skeptic now output bullet-point lists for clear, actionable feedback
- **Idea Improvement**: Ideas are regenerated based on all agent feedback, maintaining strengths while addressing weaknesses
- **Score Comparison**: Visual comparison between original and improved scores with delta indicators
- **Transparent Process**: Users see both original and improved ideas with full critique history

### Example Output:
```
Original Idea: AI-powered personal assistant for elderly care
Score: 6.5/10

[Advocate Points] → [Skeptic Concerns] → [Improvement Process]

Improved Idea: Privacy-first AI companion with local processing and family oversight
Score: 8.2/10 (↑ +1.7 points, 26% improvement)
```

This enhancement addresses the limitation where valuable agent insights were only displayed without influencing the final output, resulting in more refined and robust ideas.

## Quick Start

### Prerequisites
- Python 3.10 or newer (required for TypedDict and modern features)
- Access to Google Gemini API (recommended: gemini-2.5-flash)
- Optional: pytest for running tests, ruff for linting

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TheIllusionOfLife/Eureka.git
   cd Eureka
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r config/requirements.txt
   ```

4. **Set Python path (required for the new structure):**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # On Windows: set PYTHONPATH=%PYTHONPATH%;%cd%\src
   ```

5. **API Key Configuration:**
   Create a `.env` file in the `src/madspark/` directory:
   ```env
   GOOGLE_API_KEY="YOUR_API_KEY_HERE"
   GOOGLE_GENAI_MODEL="gemini-2.5-flash"
   ```

### Basic Usage

```bash
# Run the basic workflow
python -m madspark.core.coordinator

# Use the CLI interface
python -m madspark.cli.cli "Your theme" "Your constraints" --temperature 0.8

# Interactive mode
python -m madspark.cli.interactive_mode

# Web interface
cd web && docker-compose up
```

## Project Structure

```
eureka/                               # MadSpark Multi-Agent System
├── README.md                         # This file
├── docs/                            # User guides & tutorials
│   ├── QUICK_START_EXAMPLES.md      # Common usage patterns
│   ├── BATCH_PROCESSING_GUIDE.md    # Batch processing guide
│   ├── INTERACTIVE_MODE_GUIDE.md    # Interactive CLI guide
│   └── WEB_INTERFACE_GUIDE.md       # Web UI guide
├── src/                             # Core application code
│   └── madspark/                    # Main package
│       ├── agents/                  # Agent definitions
│       ├── core/                    # Coordinators & core logic
│       ├── utils/                   # Utilities (cache, bookmark, etc.)
│       ├── cli/                     # CLI interface
│       └── web_api/                 # Web API backend
├── tests/                           # All test files
├── tools/                           # Development & utility tools
│   ├── benchmark/                   # Performance benchmarking
│   ├── debug/                       # Debug utilities
│   └── batch/                       # Batch processing tools
├── data/                            # Runtime data
│   ├── exports/                     # Generated exports
│   ├── logs/                        # Application logs
│   └── temp/                        # Temporary files
├── config/                          # Configuration files
│   ├── requirements.txt             # Python dependencies
│   ├── pytest.ini                  # Test configuration
│   └── constants.py                 # Application constants
├── web/                             # Web frontend
│   └── frontend/                    # React TypeScript app
└── scripts/                         # Setup & utility scripts
```

## Core Features

### Phase 1 Foundation (Completed)
- **🏗️ Hybrid Architecture**: Three operational modes (Mock, Direct API, ADK Framework)
- **🤖 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🌡️ Temperature Control**: Full preset system with stage-specific creativity control
- **🔍 Novelty Filtering**: Lightweight duplicate detection and similarity filtering
- **📚 Bookmark & Remix**: Persistent idea storage with tagging and remix capabilities
- **🖥️ Enhanced CLI**: Comprehensive command-line interface

### Phase 2 Complete (All Features Implemented)
- **🧠 Context-Aware Agents**: Agents reference conversation history for informed decisions
- **🔗 Logical Inference**: Sophisticated reasoning chains with confidence scoring
- **📊 Multi-Dimensional Evaluation**: 7-dimension assessment framework with radar chart visualization
- **💾 Agent Memory**: Persistent context storage with intelligent similarity search
- **💬 Conversation Analysis**: Workflow pattern detection and completeness tracking
- **🚀 Performance Optimization**: Redis caching with LRU eviction for workflow results
- **📈 Batch Processing**: Process multiple themes from CSV/JSON with parallel execution
- **🎯 Interactive CLI**: Real-time conversational mode with guided refinement
- **🌐 Web Interface**: React frontend with WebSocket progress updates
- **📤 Export Formats**: Support for JSON, CSV, Markdown, and PDF exports
- **🧪 Production Ready**: 95% test coverage, CI/CD validation, and comprehensive error handling

## Development

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality
```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Security scanning
bandit -r src/ -x tests/
```

### Performance Benchmarking
```bash
# Run performance benchmarks
python tools/benchmark/benchmark_performance.py

# Generate benchmark report
python tools/benchmark/generate_report.py
```

## Documentation

For detailed usage instructions, see the documentation in the `docs/` directory:

- **[Quick Start Examples](docs/QUICK_START_EXAMPLES.md)** - Common usage patterns and recipes
- **[Batch Processing Guide](docs/BATCH_PROCESSING_GUIDE.md)** - Process multiple themes from CSV/JSON
- **[Interactive Mode Guide](docs/INTERACTIVE_MODE_GUIDE.md)** - Real-time conversational interface
- **[Web Interface Guide](docs/WEB_INTERFACE_GUIDE.md)** - Modern web UI with real-time updates

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest tests/`
5. Commit your changes: `git commit -m "Add your feature"`
6. Push to the branch: `git push origin feature/your-feature`
7. Create a Pull Request

## Session Handover

##### Last updated (UTC): 2025-07-15

#### Recently Completed

- ✅ **PR #89**: Implemented bookmark persistence and share functionality
  - Implemented full CRUD operations for bookmark management system
  - Added `BookmarkManager` component supporting search, filtering, and export
  - Fixed critical bugs: bookmark removal logic and score precision loss
  - Enhanced security with Pydantic validators for input sanitization
  - Comprehensive accessibility improvements (ARIA labels, button types)
  - Addressed feedback from five reviewers (Claude, CodeRabbit, Copilot, Gemini, Cursor)
  - Performance optimizations via `useMemo` and other React best practices

- ✅ **PR #88**: Resolved scoring display consistency
  - Fixed null score handling in ComparisonRadarChart
  - Ensured consistent score prop passing in web components
  - Addressed division by zero edge cases

- ✅ **PR #87**: Documentation and pattern updates
  - Enhanced session handover documentation
  - Updated core patterns with lessons learned

#### Next Priority Tasks

1. **Implement Toast Notifications**: Replace `alert()` with a modern notification system
   - Source: Deferred from PR #89 review feedback
   - Context: Current implementation uses browser alerts which interrupt UX
   - Approach: Implement react-toastify or similar for non-blocking notifications

2. **Rate Limiting Implementation**: Add API rate limiting for security
   - Source: Security recommendation from PR #89 review
   - Context: Bookmark endpoints currently lack rate limiting protection
   - Approach: Use `slowapi` or a similar library for FastAPI rate limiting

3. **Performance Benchmarking**: Validate bookmark system performance
   - Source: New bookmark feature needs performance validation
   - Context: Test with large bookmark collections (100+ items)
   - Approach: Benchmark API response times and UI rendering performance

#### Session Learnings

- **Critical Bug Pattern**: Toggle features using temporary IDs will always fail — must match against persisted data (from PR #89)
- **Comprehensive PR Reviews**: Successfully handled feedback from 5 different bot reviewers systematically (from PR #89)
- **Security First**: Pydantic validators provide excellent input sanitization at the model level (from PR #89)
- **React Anti-Patterns**: useEffect for prop syncing causes state management issues — use callbacks instead (from PR #89)
- **Precision Matters**: Type casting (int()) can cause silent data loss — preserve float precision (from PR #89)
- **Accessibility Standards**: Systematic addition of button types and ARIA attributes improves UX for all users (from PR #89)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: See the `docs/` directory for comprehensive guides
- **Examples**: Check `docs/QUICK_START_EXAMPLES.md` for common usage patterns
