# MadSpark Multi-Agent System - Project Guidelines

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Eureka features the MadSpark Multi-Agent System, a sophisticated AI-powered experimental platform implementing a hybrid architecture with multiple operational modes.

## Architecture Patterns
- **Package Structure**: Uses standard `src/madspark/` layout with subpackages for agents, core, utils, cli (web_api package is placeholder)
- **Import Strategy**: Try/except blocks with relative fallbacks for multi-environment compatibility
- **Mock-First Development**: All functionality must work in mock mode without API keys
- **Operational Modes**: Mock (development), Direct API (production), ADK Framework (experimental)
- **Logical Inference**: LLM-powered LogicalInferenceEngine replaces hardcoded templates for genuine reasoning
- **Formatter Strategy Pattern**: CLI output formatting uses Strategy Pattern with pluggable formatters (brief, simple, detailed, summary, json)
- **Type Hint Organization**: Centralized type definitions in `[module]/types.py` files

## Common Tasks
- **Run Coordinator**: `PYTHONPATH=src python -m madspark.core.coordinator`
- **CLI Interface**: `PYTHONPATH=src python -m madspark.cli.cli "topic" "context"`
- **Web Interface**: `cd web && docker compose up`
- **Run Tests**: `PYTHONPATH=src pytest` (90%+ coverage) or `python tests/test_basic_imports_simple.py` (basic imports)

## Development & Testing

See `README.md` for development setup, testing commands, and `docs/ci-policy.md` for CI/CD guidelines.

**Key Reminders:**
- **Mock Mode**: All tests use `MADSPARK_MODE=mock` (no API calls in CI)
- **Coverage**: 90%+ for critical paths
- **TypeScript**: ALWAYS run `npm run typecheck` after .ts/.tsx changes
- **Branch Workflow**: Create feature branch BEFORE any work

**Import Patterns:**
```python
# Pattern for scripts that may run standalone or within package
try:
    from madspark.llm.models import GEMINI_MODEL_DEFAULT
except ImportError:
    GEMINI_MODEL_DEFAULT = "gemini-3-flash-preview"  # Fallback value
```

## Dependencies
- **Python**: 3.10+ required for TypedDict and modern features
- **Core**: google-genai, python-dotenv, ollama, diskcache
- **Testing**: pytest, pytest-mock, pytest-asyncio
- **Web**: FastAPI, React 18.2, TypeScript, Docker (in `web/` directory)

## LLM Provider Abstraction (Ollama-First by Default)

**✅ FULL INTEGRATION COMPLETE** - Ollama as primary LLM provider with automatic Gemini fallback.

### Quick Reference
| Component | Location |
|-----------|----------|
| Router | `src/madspark/llm/router.py` |
| Providers | `src/madspark/llm/providers/{ollama,gemini}.py` |
| Cache | `src/madspark/llm/cache.py` |

### CLI Usage
```bash
ms "topic" --provider auto         # Default: Ollama primary, Gemini fallback
ms "topic" --provider ollama       # Force local inference (FREE)
ms "topic" --model-tier fast       # gemma3:4b (~3.3GB)
ms "topic" --model-tier balanced   # gemma3:12b (default, ~8.1GB)
ms "topic" --no-router             # Use direct Gemini API
ms "topic" --show-llm-stats        # Display usage metrics
```

### Environment Variables
```bash
MADSPARK_LLM_PROVIDER=auto        # auto, ollama, gemini
MADSPARK_MODEL_TIER=balanced       # fast, balanced (default), quality
MADSPARK_NO_ROUTER=false           # Set to true to disable router
OLLAMA_HOST=http://localhost:11434
```

### Cache Security
Cache stores prompts/responses in plaintext (`.cache/llm/`). For sensitive deployments:
- Use `--no-cache` for sensitive prompts
- Clear cache: `ms --clear-cache` or `rm -rf .cache/llm/`

## CLI Output Formatting

Strategy Pattern with pluggable formatters in `src/madspark/cli/formatters/`.

### Output Section Order
Human-readable formatters display sections in **workflow execution order**:
1. Original Idea + Initial Score/Critique
2. Advocacy (strengths, opportunities)
3. Skepticism (flaws, risks)
4. **Logical Inference Analysis** (if `--logical` enabled)
5. **Improved Idea** (informed by above analysis)
6. Improved Score + Delta
7. Multi-Dimensional Evaluation

## Google GenAI API Usage
```python
from google import genai

client = genai.Client()
config = genai.types.GenerateContentConfig(
    temperature=0.7,
    response_mime_type="application/json",
    response_schema=MyTypedDict,
    system_instruction="..."
)
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=prompt,
    config=config
)
```

### Testing Mock Pattern
```python
mock_models = Mock()
mock_models.generate_content.return_value = mock_response
mock_genai_client.models = mock_models
```

## Pydantic Schema Models (✅ COMPLETE)

All production code uses Pydantic v2 models. Zero legacy dict schemas in use.

### Package Structure
```
src/madspark/schemas/
├── base.py              # TitledItem, ConfidenceRated, ScoredEvaluation
├── evaluation.py        # EvaluatorResponse, CriticEvaluation(s), DimensionScore
├── generation.py        # IdeaItem, GeneratedIdeas, ImprovementResponse
├── advocacy.py          # AdvocacyResponse, StrengthItem, OpportunityItem
├── skepticism.py        # SkepticismResponse, CriticalFlaw, RiskChallenge
├── logical_inference.py # InferenceResult, CausalAnalysis, ContradictionAnalysis
└── adapters.py          # pydantic_to_genai_schema, genai_response_to_pydantic
```

### Usage Pattern
```python
from madspark.schemas.evaluation import CriticEvaluations
from madspark.schemas.adapters import pydantic_to_genai_schema, genai_response_to_pydantic

config = types.GenerateContentConfig(
    response_schema=pydantic_to_genai_schema(CriticEvaluations),
    ...
)
validated = genai_response_to_pydantic(response.text, CriticEvaluations)
```

See `src/madspark/schemas/README.md` for full documentation.

## Web Development Patterns

### Performance
- **Compression**: GZip middleware (minimum_size=1000, compresslevel=6)
- **Pagination**: Memoization for filtered results (20 items per page)
- **Rate Limiting**: slowapi with 5 requests/minute on critical endpoints

### Error Handling
- **Centralized Utilities**: `errorHandler.ts` for consistent error categorization
- **Toast Notifications**: react-toastify for non-blocking UX
- **Structured Logging**: `logger.ts` with session tracking

### Docker
When encountering module resolution errors:
1. Install dependencies inside the container
2. Use type workarounds when @types packages conflict
3. Rebuild containers after dependency changes

## Web Interface Testing

Use Playwright MCP server for automated browser testing:
```bash
# Start web interface
cd web && docker compose up

# Use Playwright MCP for testing
mcp__playwright__playwright_navigate(url="http://localhost:3000")
mcp__playwright__playwright_fill(selector="input[name='topic']", value="test topic")
mcp__playwright__playwright_screenshot(name="test_results", fullPage=true)
```
