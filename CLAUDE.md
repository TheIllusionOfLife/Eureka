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
- **Type Hint Organization**: Centralized type definitions in `[module]/types.py` files (e.g., `cli/types.py` contains TypedDict, Literal types for all CLI components)

## Common Tasks
- **Run Coordinator**: `PYTHONPATH=src python -m madspark.core.coordinator`
- **CLI Interface**: `PYTHONPATH=src python -m madspark.cli.cli "topic" "context"`
- **Web Interface**: `cd web && docker compose up`
- **Run Tests**: `PYTHONPATH=src pytest` (comprehensive test suite with 90%+ coverage) or `python tests/test_basic_imports_simple.py` (basic imports only)

## Development & Testing

For comprehensive development workflows, testing commands, and CI/CD guidelines, see:
- **Development Setup**: See the "Development" section in `README.md`
- **Testing Commands**: See the "Testing" subsection under "Development" in `README.md`
- **CI/CD Guidelines**: `docs/ci-policy.md` for complete CI management

**Key Reminders:**
- **Mock Mode**: All tests use `MADSPARK_MODE=mock` (no API calls in CI)
- **Coverage**: 90%+ for critical paths (achieved with PR #84)
- **TypeScript**: ALWAYS run `npm run typecheck` after .ts/.tsx changes
- **Branch Workflow**: Create feature branch BEFORE any work

## Dependencies
- **Python**: 3.10+ required for TypedDict and modern features
- **Core**: google-genai, python-dotenv, ollama, diskcache (from `config/requirements.txt`)
- **Testing**: pytest, pytest-mock, pytest-asyncio
- **Caching**: redis (available but optional), diskcache (LLM response caching)
- **Optional**: ruff for linting, mypy for type checking
- **Web**: FastAPI, React 18.2, TypeScript, Docker (in `web/` directory)

## LLM Provider Abstraction Layer (Ollama-First by Default)

**✅ FULL INTEGRATION COMPLETE - Router enabled by default!**

MadSpark now uses **Ollama as the primary LLM provider** by default for cost-free local inference, with automatic fallback to Gemini:

- ✅ Router is enabled by DEFAULT (Ollama-first behavior)
- ✅ Web backend integrates router with configurable provider/tier/cache
- ✅ Frontend has LLM provider selector and metrics display
- ✅ Docker Compose includes Ollama service with persistent model storage
- ✅ CLI has `--no-router` flag for backward compatibility
- ✅ Tests use MADSPARK_NO_ROUTER=true by default for backward compatibility
- ✅ Individual agent calls can route through router when `use_router=True`

**Key Changes:**
- `should_use_router()` returns `True` by default (opt-out instead of opt-in)
- Web API sets router env vars from request parameters
- Response includes LLM metrics (tokens, cost, cache hits, latency)
- `tests/conftest.py` sets MADSPARK_NO_ROUTER=true to maintain backward compatibility

**⚠️ Current Limitations:**
- Batch operations still use direct Gemini API for efficiency (single call for all items)
- Some agent functions don't have `use_router` parameter yet
- Ollama requires local installation or Docker container

MadSpark now supports multiple LLM providers through an abstraction layer with automatic fallback and caching.

### Package Structure
```text
src/madspark/llm/
├── __init__.py          # Main exports
├── base.py              # LLMProvider abstract base class
├── config.py            # LLMConfig, ModelTier configuration (⚠️ token_budgets defined but not used)
├── response.py          # LLMResponse metadata dataclass
├── exceptions.py        # Provider-specific exceptions
├── cache.py             # ResponseCache with diskcache backend
├── router.py            # LLMRouter with fallback logic
├── agent_adapter.py     # Bridge for agent integration (⚠️ defined but not called by any agent)
└── providers/
    ├── ollama.py        # OllamaProvider (local, free)
    └── gemini.py        # GeminiProvider (cloud, paid)
```

**Note on Dead Code**: The following components are defined but not yet integrated:
- `agent_adapter.py`: Provides `generate_structured_via_router()` but no agent imports it
- `config.py` token_budgets: Defines per-request budgets but no production code calls `get_token_budget()`
- These are infrastructure for Phase 2 integration work

### Usage Pattern
```python
from madspark.llm import get_router, LLMConfig, ModelTier
from pydantic import BaseModel

# Define schema
class MySchema(BaseModel):
    score: float
    comment: str

# Get router (singleton)
router = get_router()

# Generate with automatic provider selection
validated, response = router.generate_structured(
    prompt="Rate this idea",
    schema=MySchema,
    temperature=0.7
)

# Access results
print(validated.score)  # Validated Pydantic object
print(response.provider)  # "ollama" or "gemini"
print(response.tokens_used)
print(response.cost)  # $0.0 for Ollama

# Check metrics
metrics = router.get_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.1%}")
```

### CLI Integration
**Router is enabled by default. Use `--no-router` to disable and use direct Gemini API.**

```bash
# Provider selection (router enabled by default)
ms "topic" --provider auto         # Default: Ollama primary, Gemini fallback
ms "topic" --provider ollama       # Force local inference (FREE)
ms "topic" --provider gemini       # Force cloud API

# Model tier (default: balanced)
ms "topic" --model-tier fast       # gemma3:4b (quick, ~3.3GB)
ms "topic" --model-tier balanced   # gemma3:12b (default, ~8.1GB)
ms "topic" --model-tier quality    # gemini-2.5-flash (cloud, best)

# Cache control (enabled by default)
ms "topic" --no-cache              # Disable caching
ms --clear-cache "topic"           # Clear cache first

# Statistics
ms "topic" --show-llm-stats        # Display usage metrics

# Disable router entirely (backward compatibility)
ms "topic" --no-router             # Use direct Gemini API
```

### Environment Variables
```bash
MADSPARK_LLM_PROVIDER=auto        # auto, ollama, gemini
MADSPARK_MODEL_TIER=balanced       # fast, balanced (default), quality
MADSPARK_FALLBACK_ENABLED=true     # Enable provider fallback
MADSPARK_CACHE_ENABLED=true        # Enable response caching
MADSPARK_CACHE_TTL=86400           # Cache TTL in seconds (24h)
MADSPARK_CACHE_DIR=~/.cache/madspark/llm  # Cache directory (absolute path)
MADSPARK_NO_ROUTER=false           # Set to true to disable router
OLLAMA_HOST=http://localhost:11434 # Ollama server
OLLAMA_MODEL_FAST=gemma3:4b        # Fast tier model (non-quantized for reliable JSON)
OLLAMA_MODEL_BALANCED=gemma3:12b   # Balanced tier model (non-quantized for reliable JSON)
```

### Key Features
- **Zero-Cost Local Inference**: Ollama provides free inference with gemma3 models
- **Automatic Fallback**: Routes to Gemini when Ollama unavailable
- **Response Caching**: Disk cache with corruption resilience (invalid entries auto-invalidated)
- **Usage Metrics**: Track tokens, cost, latency, cache hit rate
- **Provider Health Monitoring**: Check availability via router.health_status()
- **Multimodal Support**: Images via Ollama, PDF/URL via Gemini
- **Security**: Thread-safe metrics, prompt length validation, path traversal protection, SecretStr for API keys

### Cache Security and Management
**Important**: The response cache stores prompts and responses in plaintext on disk (default: `.cache/llm/`). For sensitive deployments:
- Cache directory has restrictive permissions (0o700)
- Consider disabling cache for sensitive prompts: `ms "topic" --no-cache`
- Cache entries expire based on TTL (default 24 hours)
- Clear cache manually: `ms --clear-cache` or `rm -rf .cache/llm/`
- Add `.cache/` to `.gitignore` (already configured)

**Cache Cleanup Strategy**:
```bash
# Clear all cached responses
ms --clear-cache

# Manual cleanup of old cache files
rm -rf .cache/llm/

# Check cache statistics
python -c "from madspark.llm.cache import get_cache; print(get_cache().stats())"
```

## CLI Output Formatting Architecture

The CLI uses a **Strategy Pattern** for output formatting, enabling clean separation of concerns and easy extensibility.

### Formatter Package Structure
```text
src/madspark/cli/formatters/
├── base.py              # Abstract ResultFormatter base class
├── brief.py             # BriefFormatter - solution-focused markdown output
├── simple.py            # SimpleFormatter - user-friendly with emojis
├── detailed.py          # DetailedFormatter - comprehensive with all agent interactions
├── summary.py           # SummaryFormatter - improved ideas with evaluations
├── json_formatter.py    # JsonFormatter - machine-readable JSON
└── factory.py           # FormatterFactory - creates formatter instances
```

### Usage Pattern
```python
from madspark.cli.formatters import FormatterFactory

# Create formatter
formatter = FormatterFactory.create('brief')  # or 'simple', 'detailed', 'summary', 'json'

# Format results
output = formatter.format(results, args)
```

### Adding New Formatters
1. Create new formatter class extending `ResultFormatter`
2. Implement `format(results, args) -> str` method
3. Register in `FormatterFactory._formatters` dict
4. Add comprehensive tests in `tests/test_formatters.py`

### Benefits
- **Modularity**: Each formatter <150 lines, testable in isolation
- **Extensibility**: Easy to add new output formats
- **Maintainability**: Clear separation of concerns
- **Type Safety**: Complete type hints for better IDE support

### Output Section Order
Human-readable formatters (brief, simple, detailed, summary) display sections in **workflow execution order**:
1. Original Idea + Initial Score/Critique
2. Advocacy (strengths, opportunities)
3. Skepticism (flaws, risks)
4. **Logical Inference Analysis** (if `--logical` enabled)
5. **Improved Idea** (informed by above analysis)
6. Improved Score + Delta
7. Multi-Dimensional Evaluation

This order reflects the actual data flow: logical inference (Step 4.5) feeds into improvement (Step 5).

**Note**: JSON output preserves raw structure without ordering since JSON objects are unordered by spec.

## Google GenAI API Usage Pattern
When using Google's GenAI SDK, always use the nested API structure:
```python
from google import genai

# Initialize the client (typically done once per module)
genai_client = genai.Client()

# Define your model and prompt
model_name = "gemini-1.5-flash"  # or your preferred model
prompt = "Your prompt text here"

# Configure the request
config = genai.types.GenerateContentConfig(
    temperature=0.7,
    system_instruction="Your system instruction here"
)

# Make the API call using nested models structure
response = genai_client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=config
)

# For structured output (JSON responses), use response_mime_type:
from typing import TypedDict, List

class ResponseSchema(TypedDict):
    field1: str
    field2: List[str]

config = genai.types.GenerateContentConfig(
    temperature=0.7,
    response_mime_type="application/json",
    response_schema=ResponseSchema,
    system_instruction="Your system instruction"
)
```

For testing, mock the complete nested structure:
```python
from unittest.mock import Mock

# Create mock client and response
mock_genai_client = Mock()
mock_response = Mock()
mock_response.text = "Mocked response text"

# Mock the nested structure
mock_models = Mock()
mock_models.generate_content.return_value = mock_response
mock_genai_client.models = mock_models
```

## Pydantic Schema Models (✅ COMPLETE - Phases 1, 2, 3)

MadSpark uses Pydantic v2 models for type-safe schema definitions that work across LLM providers.

**Migration Status**: All production code migrated (PR #200, #201, #202). Zero legacy dict schemas in use.

### Usage Pattern
```python
from madspark.schemas.evaluation import EvaluatorResponse, CriticEvaluations
from madspark.schemas.adapters import pydantic_to_genai_schema, genai_response_to_pydantic
from google import genai
from google.genai import types

# 1. Define schema as Pydantic model (see src/madspark/schemas/)
# 2. Convert to GenAI format for API calls
config = types.GenerateContentConfig(
    temperature=0.7,
    response_mime_type="application/json",
    response_schema=pydantic_to_genai_schema(CriticEvaluations),
    system_instruction="..."
)

# 3. Make API call
client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="...",
    config=config
)

# 4. Validate and parse response
validated = genai_response_to_pydantic(response.text, CriticEvaluations)

# 5. Use type-safe fields
for eval_item in validated:
    print(eval_item.score)  # IDE autocomplete works!
    print(eval_item.comment)

# 6. Convert to dict for backward compatibility
data = [item.model_dump() for item in validated]
```

### Available Models

**Base Models** (`madspark.schemas.base`):
- `TitledItem` - Title+description pairs (for Advocate/Skeptic)
- `ConfidenceRated` - Analysis with confidence scores (0.0-1.0)
- `Scored` - Base class with score field
- `ScoredEvaluation` - Numeric evaluations (0-10 scale) with critique

**Evaluation Models** (`madspark.schemas.evaluation`):
- `EvaluatorResponse` - Evaluator agent output with optional strengths/weaknesses
- `DimensionScore` - Single dimension score for multi-dimensional evaluations
- `CriticEvaluation` - Single critic evaluation
- `CriticEvaluations` - Array of critic evaluations

**Generation Models** (`madspark.schemas.generation`):
- `IdeaItem` - Single generated idea with features and category
- `GeneratedIdeas` - Array of generated ideas (RootModel)
- `ImprovementResponse` - Improved idea with title, description, and improvements

**Advocacy Models** (`madspark.schemas.advocacy`):
- `AdvocacyResponse` - Complete advocacy output
- `StrengthItem` - Identified strength (inherits TitledItem)
- `OpportunityItem` - Identified opportunity (inherits TitledItem)
- `ConcernResponse` - Concern with mitigation response

**Skepticism Models** (`madspark.schemas.skepticism`):
- `SkepticismResponse` - Complete skepticism output
- `CriticalFlaw` - Identified flaw (inherits TitledItem)
- `RiskChallenge` - Identified risk (inherits TitledItem)
- `QuestionableAssumption` - Assumption with concern
- `MissingConsideration` - Overlooked factor with importance

**Logical Inference Models** (`madspark.schemas.logical_inference`):
- `InferenceResult` - Base inference result (inherits ConfidenceRated)
- `CausalAnalysis` - Causal chain analysis
- `ConstraintAnalysis` - Constraint satisfaction analysis
- `ContradictionAnalysis` - Contradiction detection
- `ImplicationsAnalysis` - Implications and second-order effects

### Benefits
- ✅ Type safety with IDE autocomplete
- ✅ Automatic validation with clear error messages
- ✅ Field constraints (min/max) enforced by Gemini API
- ✅ Provider-agnostic (works with any LLM via adapter pattern)
- ✅ Better documentation (schemas are self-documenting)
- ✅ Backward compatible via `.model_dump()`

### Adding New Schemas
1. Create Pydantic model in `src/madspark/schemas/`
2. Inherit from base models when applicable (`TitledItem`, `ConfidenceRated`, `ScoredEvaluation`)
3. Add field validators for custom constraints using `@field_validator`
4. Use `pydantic_to_genai_schema()` adapter in agent code
5. Add comprehensive tests in `tests/test_schemas_pydantic.py`
6. Update `src/madspark/schemas/README.md` documentation

### Example: Creating a New Schema
```python
# src/madspark/schemas/new_agent.py
from pydantic import BaseModel, Field
from typing import List, Optional
from .base import ScoredEvaluation

class NewAgentResponse(ScoredEvaluation):
    """Response from NewAgent."""
    insights: List[str] = Field(
        ...,
        description="Key insights discovered",
        min_length=1
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence in analysis"
    )

# Usage in agent
from madspark.schemas.new_agent import NewAgentResponse
from madspark.schemas.adapters import pydantic_to_genai_schema

schema = pydantic_to_genai_schema(NewAgentResponse)
# ... use schema in API call
```

### Migration Status
- ✅ **Phase 1 Complete:** Base models + Evaluation schemas (EVALUATOR, DIMENSION_SCORE, CRITIC)
- ✅ **Phase 2 Complete:** All core agent schemas (Generation, Advocacy, Skepticism, Logical Inference)
- ✅ **Phase 3 Complete:** Integration & cleanup (enhanced_reasoning, LogicalInferenceEngine, response normalization, structured output parsing)
- ✅ **Migrated Components:** Critic, Advocate, Skeptic, Idea Generator, Logical Inference Engine, MultiDimensionalEvaluator, structured_idea_generator
- ✅ **Test Coverage:** 181 comprehensive tests (149 Phase 1&2 + 32 Phase 3)
- ✅ **LLM Provider Abstraction:** Multi-provider support with Ollama/Gemini (see LLM Provider section above)
- ⏳ **Phase 4 (Future):** Extend Pydantic schemas to support additional LLM providers
- ⏳ **Phase 5 (Future):** Remove legacy dict schemas completely

### Testing Pydantic Schemas
```bash
# Run all schema tests (149 test cases across 5 modules)
PYTHONPATH=src pytest tests/test_schemas*.py -v

# Individual test modules
pytest tests/test_schemas_pydantic.py -v        # 60 tests: base & evaluation
pytest tests/test_schemas_generation.py -v      # 30 tests: idea generation
pytest tests/test_schemas_advocacy.py -v        # 20 tests: advocacy
pytest tests/test_schemas_skepticism.py -v      # 21 tests: skepticism
pytest tests/test_schemas_logical_inference.py -v # 18 tests: logical inference

# Test with coverage
pytest tests/test_schemas*.py --cov=src/madspark/schemas --cov-report=html

# Test migrated agent integration
PYTHONPATH=src pytest tests/test_agents.py::TestCritic -v
PYTHONPATH=src pytest tests/test_agents.py::TestAdvocate -v
PYTHONPATH=src pytest tests/test_agents.py::TestSkeptic -v
```

### See Also
- **Full Documentation:** `src/madspark/schemas/README.md`
- **Test Suites:** 149 tests across 5 test modules
- **Pydantic Documentation:** https://docs.pydantic.dev/

## Web Interface Testing

When testing the web interface, use Playwright MCP server for automated browser testing:

```bash
# Start web interface
cd web && docker compose up

# Use Playwright MCP for testing
mcp__playwright__playwright_navigate(url="http://localhost:3000")
mcp__playwright__playwright_fill(selector="input[name='topic']", value="test topic")
mcp__playwright__playwright_screenshot(name="test_results", fullPage=true)
```

## Web Development Patterns

### Performance Optimization
- **Compression**: GZip middleware configured with minimum_size=1000, compresslevel=6
- **Pagination**: Implement with memoization for filtered results (20 items per page)
- **Rate Limiting**: Use slowapi with 5 requests/minute on critical endpoints

### Error Handling Architecture
- **Centralized Utilities**: Use `errorHandler.ts` for consistent error categorization
- **Toast Notifications**: Replace alert() with react-toastify for non-blocking UX
- **Structured Logging**: Use `logger.ts` with session tracking and log levels

### Docker Container Issues
When encountering module resolution errors in Docker:
1. Install dependencies inside the container (not just package.json)
2. Use type workarounds when @types packages conflict
3. Rebuild containers after dependency changes

### Content Rendering
When rendering dynamic content that can be either JSON or markdown:
- Create type-safe renderers with format detection
- Use TypeScript union types instead of 'any'
- Extract common rendering logic to utilities
- Safe property access with null checks
- Support both formats seamlessly

Example:
```typescript
export const renderContent = (content: string | ContentStructure) => {
  if (typeof content === 'string') {
    try {
      const parsed = JSON.parse(content);
      // Render structured JSON from 'parsed'
      return renderStructuredJSON(parsed);
    } catch (e) {
      // Not valid JSON, render as markdown
      // Log error for debugging if needed: console.debug('JSON parse failed:', e);
      return renderMarkdown(content);
    }
  } else {
    // Render structured JSON from 'content' object
    return renderStructuredJSON(content);
  }
};
```