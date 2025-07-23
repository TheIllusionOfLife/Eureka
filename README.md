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
- Google Gemini API access

### Installation

```bash
# Clone and setup
git clone https://github.com/TheIllusionOfLife/Eureka.git
cd Eureka
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r config/requirements.txt

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Configure API
echo 'GOOGLE_API_KEY="YOUR_API_KEY_HERE"' > src/madspark/.env
echo 'GOOGLE_GENAI_MODEL="gemini-2.5-flash"' >> src/madspark/.env
```

### Usage

```bash
# Basic workflow
python -m madspark.core.coordinator

# CLI with topic and context
python -m madspark.cli.cli "Sustainable transportation" "Low-cost solutions"

# Web interface
cd web && docker-compose up
```

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

##### Last updated: 2025-07-23

#### Recently Completed

- ✅ **PR #107**: CI/CD performance optimization (20min → 2-4min, 85-90% improvement)
  - Parallel test execution, conditional Python matrix, workflow streamlining
  - Fixed test exclusion logic, resolved test fallback masking issue
  - Created comprehensive test management policy

- ✅ **PR #101**: OpenAPI documentation and CI/CD enhancements
  - Interactive API documentation, enhanced pipeline with pre-commit hooks

#### Next Priority Tasks

1. **PR #105 Cleanup**: Review/close open validation PR from earlier work
2. **Performance Test Markers**: Add @pytest.mark.slow/@pytest.mark.integration markers
3. **CI Performance Monitoring**: Set up regression detection alerts

#### Key Learnings

- **CI Performance**: Systematic optimization achieves 85-90% time reduction through parallel execution and workflow separation
- **Test Exclusion**: Keyword-based (`-k "not performance"`) more reliable than marker-based when tests lack proper markers
- **Test Fallback**: Avoid `||` operators between pytest commands - they mask genuine test failures

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/TheIllusionOfLife/Eureka/issues)
- **Documentation**: `docs/` directory for comprehensive guides