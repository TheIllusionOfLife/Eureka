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
# Edit .env to add your GOOGLE_API_KEY
```

### Running the Application
```bash
# Direct workflow execution
python coordinator.py

# Full CLI interface
python cli.py --help
python cli.py generate-ideas "AI in healthcare" --count 3 --temperature creative
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
- Environment variables via `.env` file (GOOGLE_API_KEY, GOOGLE_GENAI_MODEL)
- Temperature presets in `constants.py`
- Agent configurations in `agent_defs/`

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
