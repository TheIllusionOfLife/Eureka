# MadSpark Multi-Agent System - Project Guidelines

## Architecture Patterns
- **Package Structure**: Uses standard `src/madspark/` layout with subpackages for agents, core, utils, cli, and web_api
- **Import Strategy**: Try/except blocks with relative fallbacks for multi-environment compatibility
- **Mock-First Development**: All functionality must work in mock mode without API keys

## Common Tasks
- **Run Coordinator**: `PYTHONPATH=src python -m madspark.core.coordinator`
- **CLI Interface**: `PYTHONPATH=src python -m madspark.cli.cli "theme" "constraints"`
- **Web Interface**: `cd web && docker-compose up`
- **Run Tests**: `python tests/test_basic_imports_simple.py` (no pytest required)

## Testing Approach
- **CI-Safe Tests**: Tests must run without external API calls
- **Import Tests**: Basic functionality verified through import tests
- **Mock Mode**: Primary testing mode to avoid API costs

## Dependencies
- **Python**: 3.10+ required for TypedDict and modern features
- **Google Gemini API**: Optional, falls back to mock mode
- **Docker**: Required only for web interface
- **pytest**: Optional, basic tests work without it
