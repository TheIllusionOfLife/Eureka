# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.2%20Complete-success)](#project-status) [![Testing](https://img.shields.io/badge/Testing-85%25%20Coverage-success)](#testing) [![CI/CD](https://img.shields.io/badge/CI%2FCD-Optimized-brightgreen)](#development)

A sophisticated multi-agent system for idea generation and refinement using Google's Gemini API. Features specialized agents for idea generation, criticism, advocacy, and skepticism with advanced reasoning capabilities.

## 🚀 Key Features

- **🧠 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🔗 Feedback Loop**: Ideas are improved based on agent insights with score comparison
- **📚 OpenAPI Documentation**: Interactive API docs at `/docs` and `/redoc`
- **🌐 Web Interface**: React frontend with WebSocket progress updates
- **⌨️ Keyboard Shortcuts**: Ctrl+Enter to submit, Ctrl+S to save, Ctrl+/ for help
- **🔍 Duplicate Detection**: Intelligent similarity-based bookmark filtering
- **📤 Export Formats**: JSON, CSV, Markdown, and PDF export support

## Quick Start

### Prerequisites
- Python 3.10+ (required for TypedDict and modern features)
- Google Gemini API key (optional - mock mode available)

### Installation

```bash
# Clone and setup (2 steps!)
git clone https://github.com/TheIllusionOfLife/Eureka.git
cd Eureka
./setup.sh  # Interactive setup with API key configuration
```

### Usage

```bash
# Generate ideas with simplified syntax
mad_spark "consciousness" "what is it?"
mad_spark "sustainable cities"  # Context is optional

# Run the coordinator
mad_spark coordinator

# Even shorter with aliases
ms "future of AI"

# Web interface
cd web && docker compose up
```

<details>
<summary>Manual Setup (if needed)</summary>

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r config/requirements.txt

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Configure API
echo 'GOOGLE_API_KEY="YOUR_API_KEY_HERE"' > src/madspark/.env
echo 'GOOGLE_GENAI_MODEL="gemini-2.5-flash"' >> src/madspark/.env

# Run commands
mad_spark coordinator
mad_spark "Sustainable transportation" "Low-cost solutions"
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

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run test suite: `pytest tests/`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

## Session Handover

##### Last updated: 2025-07-24

#### Recently Completed

- ✅ **PR #115**: User-friendly setup and bookmark fixes
  - Created `run.py` and `setup.sh` for 2-step installation (was 8+ steps)
  - Consolidated API key management to single `.env` file
  - Fixed bookmark API field mismatch (theme→topic, constraints→context)
  - Added character truncation for 10k char database limits
  - Resolved all TypeScript compilation errors
  - Addressed feedback from 5 review bots (claude, coderabbit, cursor, gemini, windsurf)

- ✅ **PR #112**: Restored validation scripts and documentation
  - Fixed shell script error handling (removed `set -e` for complete reporting)
  - Dynamic git default branch detection
  - Case-insensitive markdown file categorization

- ✅ **PR #111**: Restored comprehensive integration tests
  - System, Docker, Web API, error handling, and performance tests
  - 759 lines of test coverage improvements

- ✅ **PR #110**: Restored CI/CD improvements and pre-commit hooks
  - Fixed coverage upload for main branch
  - Corrected misleading error messages

- ✅ **PR #107**: CI/CD performance optimization (20min → 2-4min, 85-90% improvement)
  - Conditional Python matrix, parallel execution, workflow separation

#### Next Priority Tasks

1. **Test-Heavy PR Support**: Update pr-validation.yml to handle test-heavy PRs (>70% test files) with extended limits
   - Source: PR #111 exceeded size limits despite being valuable tests
   - Context: Current logic only extends limits for CI/infrastructure PRs
   - Approach: Add similar logic for test-heavy PRs

2. **Performance Test Markers**: Add @pytest.mark.slow/@pytest.mark.integration markers to restored tests
   - Source: New integration tests in PR #111
   - Context: Enables better test filtering in CI
   - Approach: Review test_system_integration.py and add appropriate markers

3. **CI Performance Monitoring**: Set up regression detection alerts
   - Source: PR #107 optimization gains
   - Context: Prevent CI time from creeping back up
   - Approach: GitHub Actions workflow to track CI duration trends

#### Session Learnings

- **FILE VERIFICATION DISCIPLINE**: Always read shared files/screenshots before responding to avoid critical mistakes
- **TypeScript Compilation**: Run `tsc --noEmit` after any .ts/.tsx changes to catch type errors early
- **Field Truncation**: Database fields have character limits (10k chars) - truncate with ellipsis preservation
- **API Field Mapping**: Frontend/backend field name mismatches need transformation layers
- **URL Parameter Limits**: Keep URL parameters under 500 chars (browser limit ~2048)
- **CI YAML Arrays**: Use `fromJSON()` for array literals in GitHub Actions expressions
- **Shell Error Handling**: `set -e` prevents complete error reporting in validation scripts
- **PR Review Bots**: cursor[bot] provides valuable critical feedback on shell scripts and CI config
- **PR Size Policy**: CI validation rules for PR size should be flexible to accommodate valuable, test-heavy PRs

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides