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

## Manual Verification Workflows

### Pre-Development Setup (One-time)
```bash
# Install pre-commit hooks to prevent CI failures
pip install pre-commit
pre-commit install

# Verify environment is properly configured
./scripts/check_dependencies.sh
```

### Daily Development Verification
```bash
# Before starting work - verify clean state
./scripts/check_dependencies.sh

# Create feature branch (ALWAYS required)
git checkout -b feature/descriptive-name

# During development - hooks run automatically on commit
# Manual verification if needed:
pre-commit run --all-files

# Before creating PR - final verification
./scripts/check_dependencies.sh
PYTHONPATH=src pytest tests/ -v
cd web/frontend && npm test
```

### Comprehensive Testing Commands
```bash
# Backend testing (set PYTHONPATH first)
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run comprehensive test suite
pytest tests/ -v --cov=src --cov-report=html

# Test individual components
pytest tests/test_agents.py -v           # Agent functionality
pytest tests/test_coordinator.py -v     # Core coordination logic  
pytest tests/test_utils.py -v           # Utilities and helpers
pytest tests/test_cli.py -v             # CLI interface
pytest tests/test_integration.py -v     # End-to-end integration

# Quick import verification (no API keys needed)
python tests/test_basic_imports_simple.py

# Frontend testing
cd web/frontend
npm ci                                   # Install dependencies
npm test -- --coverage --watchAll=false # Run tests with coverage
npm run build                           # Verify build process

# API integration testing  
cd web/backend
PYTHONPATH=../../src MADSPARK_MODE=mock python main.py &
sleep 5                                 # Wait for server
curl http://localhost:8000/health       # Health check
python test_openapi.py                  # API documentation tests
pkill -f "python main.py"              # Stop server
```

### Code Quality Verification
```bash
# Pre-commit hooks (automatic)
pre-commit run --all-files

# Manual quality checks
ruff check src/ tests/ web/backend/      # Linting
ruff check src/ --fix                   # Auto-fix issues
mypy src/ --ignore-missing-imports      # Type checking
bandit -r src/ web/backend/             # Security scanning
safety check                           # Vulnerability checking

# Performance benchmarking
python tools/benchmark/benchmark_performance.py
python tools/benchmark/generate_report.py
```

### CI/CD Pipeline Verification
```bash
# Check recent CI runs
gh run list --limit 5

# View specific failure details
gh run view <run_id> --log

# Local CI simulation (key checks)
./scripts/check_dependencies.sh         # Dependency validation
ruff check src/ tests/ web/backend/     # Code quality
pytest tests/ -v                       # Backend tests
cd web/frontend && npm test            # Frontend tests
```

### Troubleshooting Common Issues
```bash
# Dependency resolution problems
./scripts/verify_python_deps.sh         # Python dependencies
./scripts/verify_npm_deps.sh           # npm dependencies
./scripts/verify_frontend.sh           # Frontend build verification

# Reset lock files if needed
cd web/frontend && rm package-lock.json && npm install

# Docker container issues
cd web && docker compose build --no-cache
cd web && docker compose up
```

## Testing Approach
- **CI-Safe Tests**: Tests must run without external API calls using comprehensive mocking
- **Current Infrastructure**: Full comprehensive test suite with 6 test modules (agents, coordinators, utils, cli, integration, interactive EOF)
- **Mock Mode**: Primary testing mode to avoid API costs
- **Coverage Goals**: 90%+ for critical paths (achieved with PR #84 comprehensive test suite)
- **TypeScript Projects**: ALWAYS run `npm run typecheck` or `tsc --noEmit` after any .ts/.tsx file changes
- **Frontend Changes**: Test in browser after modifications, especially after fixing compilation errors

## CI/CD Management

### Current CI Structure (Streamlined)
- **ci.yml**: Main pipeline with phased validation (syntax → tests → quality → integration)
- **pr-validation.yml**: PR-specific checks (size limits, automated checklist)
- **post-merge-validation.yml**: Post-merge health checks with issue creation
- **claude.yml**: Manual AI reviews (triggered by @claude comments)
- **claude-code-review.yml**: Automated AI reviews for new PRs

### CI Test Policy
See **[docs/ci-policy.md](docs/ci-policy.md)** for complete guidelines on:
- When to add/modify/remove CI tests
- Performance targets (< 5 min total CI time)
- Required checks before merge
- Optimization strategies

### Key CI Principles
1. **No Duplication**: Each test runs exactly once per trigger
2. **Fail Fast**: Quick checks first (< 30s) to catch obvious issues
3. **Mock by Default**: All CI uses `MADSPARK_MODE=mock`
4. **Clear Purpose**: Every workflow has single responsibility
5. **Performance Matters**: Cache aggressively, parallelize when possible

### CI Performance Optimizations

- **Conditional Python Matrix**: Only test Python 3.10 for PRs/feature branches, full matrix on main
- **Conditional Execution**: A simpler condition for jobs on non-main branches is `${{ github.ref != 'refs/heads/main' }}`
- **Parallel Execution**: Use pytest-xdist for faster test runs
- **Coverage Strategy**: Upload coverage only from single Python version to avoid duplication
- **PR Size Intelligence**: Extended limits for CI/infrastructure/documentation PRs (70% threshold)
- **Test-Heavy PR Exception**: PRs with >60% test files acceptable over 500-line limit (follows TDD best practices)
  - Example: PR #172 had 693 changes (67% test files) - acceptable for comprehensive test coverage

## Dependencies
- **Python**: 3.10+ required for TypedDict and modern features
- **Core**: google-genai, python-dotenv, ollama, diskcache (from `config/requirements.txt`)
- **Testing**: pytest, pytest-mock, pytest-asyncio
- **Caching**: redis (available but optional), diskcache (LLM response caching)
- **Optional**: ruff for linting, mypy for type checking
- **Web**: FastAPI, React 18.2, TypeScript, Docker (in `web/` directory)

## LLM Provider Abstraction Layer (NEW)

MadSpark now supports multiple LLM providers through an abstraction layer with automatic fallback and caching.

### Package Structure
```text
src/madspark/llm/
├── __init__.py          # Main exports
├── base.py              # LLMProvider abstract base class
├── config.py            # LLMConfig, ModelTier configuration
├── response.py          # LLMResponse metadata dataclass
├── exceptions.py        # Provider-specific exceptions
├── cache.py             # ResponseCache with diskcache backend
├── router.py            # LLMRouter with fallback logic
├── agent_adapter.py     # Bridge for agent integration
└── providers/
    ├── ollama.py        # OllamaProvider (local, free)
    └── gemini.py        # GeminiProvider (cloud, paid)
```

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
```bash
# Provider selection
ms "topic" --provider auto         # Default: Ollama primary, Gemini fallback
ms "topic" --provider ollama       # Force local inference
ms "topic" --provider gemini       # Force cloud API

# Model tier
ms "topic" --model-tier fast       # gemma3:4b-it-qat (quick)
ms "topic" --model-tier balanced   # gemma3:12b-it-qat (better)
ms "topic" --model-tier quality    # gemini-2.5-flash (best)

# Cache control
ms "topic" --no-cache              # Disable caching
ms --clear-cache "topic"           # Clear cache first

# Statistics
ms "topic" --show-llm-stats        # Display usage metrics
```

### Environment Variables
```bash
MADSPARK_LLM_PROVIDER=auto        # auto, ollama, gemini
MADSPARK_MODEL_TIER=fast           # fast, balanced, quality
MADSPARK_FALLBACK_ENABLED=true     # Enable provider fallback
MADSPARK_CACHE_ENABLED=true        # Enable response caching
MADSPARK_CACHE_TTL=86400           # Cache TTL in seconds (24h)
MADSPARK_CACHE_DIR=.cache/llm      # Cache directory
OLLAMA_HOST=http://localhost:11434 # Ollama server
OLLAMA_MODEL_FAST=gemma3:4b-it-qat # Fast tier model
OLLAMA_MODEL_BALANCED=gemma3:12b-it-qat # Balanced tier model
```

### Key Features
- **Zero-Cost Local Inference**: Ollama provides free inference with gemma3 models
- **Automatic Fallback**: Routes to Gemini when Ollama unavailable
- **Response Caching**: 30-50% reduction in API calls via disk cache
- **Usage Metrics**: Track tokens, cost, latency, cache hit rate
- **Provider Health Monitoring**: Check availability via router.health_status()
- **Multimodal Support**: Images via Ollama, PDF/URL via Gemini

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

## PR Review Management

### 4-Phase Review Protocol

**CRITICAL**: Always follow this systematic approach to prevent missing reviewer feedback.

**Phase 1: Complete Discovery (NO FILTERING)**
```bash
# Get PR context
PR_NUM=$(gh pr view --json number | jq -r '.number')
REPO=$(gh repo view --json owner,name | jq -r '.owner.login + "/" + .name')

# Check ALL three review sources
echo "=== PR COMMENTS ==="
gh api "/repos/${REPO}/issues/${PR_NUM}/comments" | jq -r '.[].body'

echo "=== PR REVIEWS ==="
gh api "/repos/${REPO}/pulls/${PR_NUM}/reviews" | jq -r '.[].body // "No summary"'

echo "=== LINE COMMENTS ==="
gh api "/repos/${REPO}/pulls/${PR_NUM}/comments" | jq -r '.[].body'
```

**Phase 2: Systematic Feedback Extraction**
- Extract feedback from each reviewer found in Phase 1
- Group by reviewer for clear attribution

**Phase 3: User Verification**
- List all found reviewers
- Ask user to confirm no reviewers were missed
- Only proceed after confirmation

**Phase 4: Process and Verify**
- Implement fixes by priority
- Verify CI passes
- Confirm PR is mergeable

### Common Pitfalls to Avoid
- Never use WebFetch for GitHub URLs - use GitHub CLI API
- Never filter during discovery phase
- Always handle 404 errors gracefully with `2>/dev/null || echo "[]"`
- Always verify complete content retrieval (no truncation)

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

## Development Philosophy

- **Test-Driven Development**: Write tests first, verify failure, then implement
- **Systematic Approaches**: No shortcuts - follow complete protocols
- **Branch Workflow**: Always create feature branches before any work
- **Commit at Milestones**: Commit when completing logical units of work

## Code Design Patterns

### Separation of Concerns
- **Business Logic vs Presentation**: Always keep business logic (e.g., similarity calculations, data processing) in coordinator/core modules, not in CLI/formatting layers
- **Example**: Jaccard similarity detection moved from `cli.py` formatting to `coordinator.py` business layer

### Testing Patterns
- **Warning Tests**: Use pytest's `caplog` fixture instead of skipping tests for logging behavior
- **Example**: `test_coordinator_warnings.py` uses `caplog.at_level(logging.WARNING)` to verify warning suppression

### CI Debugging
- **Local First**: When CI fails, immediately run the same check locally (e.g., `uv run ruff check`)
- **Common Issues**: Unused imports, incorrect assertion syntax (`is True` not `== True`)

## Web Interface Development Patterns

### Content Rendering (August 3, 2025)
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

## Session Learnings

### PR #130: AI-Powered MultiDimensional Evaluation (July 31, 2025)
- **AI-Powered Evaluation**: Replaced keyword-based evaluation with AI-powered system for language-agnostic support
- **Mock-Mode Compatibility**: Use try/except with SimpleNamespace fallback to maintain mock-first development
- **Explicit Failures**: System fails with clear error messages when API key not configured (no graceful degradation)
- **Human-Readable Prompts**: Format context as "Theme: X. Constraints: Y" instead of raw dictionary strings
- **Systematic PR Review**: Successfully addressed feedback from claude[bot], coderabbitai[bot], cursor[bot], and gemini-code-assist[bot]

### PR #133: Performance Test Markers (August 1, 2025)
- **Performance Optimization**: Achieved 30-50% CI speedup using pytest markers (@pytest.mark.slow, @pytest.mark.integration)
- **Systematic PR Review**: Successfully addressed feedback from 6 reviewers using 4-phase protocol (discover → extract → prioritize → fix)
- **Test Categorization**: Applied 47 markers across 6 test files for smart conditional execution (fast tests for PRs, full coverage on main)
- **Mock Mode Compatibility**: Skipif decorators necessary for timeout tests - mock operations are instantaneous
- **Test Path Validation**: Critical to verify test references during marker validation (TestAsyncIntegration vs TestEndToEndWorkflow)

### PR #132: JSON Parsing Enhancement (August 1, 2025)
- **Enhanced JSON Parsing**: Implemented multiple fallback strategies for partial coordinator evaluations with bracket matching
- **ReDoS Prevention**: Limited regex repetition to 500 characters to prevent denial of service attacks
- **Array Extraction**: Added `_extract_json_arrays` helper with proper bracket matching to handle incomplete responses
- **CI Test Requirements**: Parser logic changes require format validation tests to prevent regressions

### PR #135: Test Implementation and CI Fixes (August 1, 2025)
- **Pattern-Based Test Validation**: Replace literal string checks with pattern matching for AI-generated content
- **CI Environment Detection**: Check for dependencies before requiring venv (allows CI/global installs)
- **Argument Parsing Logic**: Carefully calculate flag_start_idx to prevent context duplication in CLI
- **Test Data Management**: Check production files for test data pollution after running tests
- **DRY Principle**: Delegate common functionality (like version display) to avoid duplication

### PR #138-139: Structured Output Support (August 1, 2025)
- **Structured JSON Output**: Implemented frontend/backend support for cleaner AI responses without meta-commentary
- **Cache Bug Prevention**: Never cache results when `genai_client` is None to prevent mock mode poisoning real client checks
- **DRY Helper Functions**: Extract duplicate response creation logic into reusable helpers (e.g., `_create_success_response()`)
- **Test Skip Patterns**: Use `@pytest.mark.skip` decorator only - avoid redundant `pytest.skip()` calls inside functions
- **Attribute Access Safety**: Use `getattr(obj, 'attr', None)` instead of `hasattr()` for safer attribute checking

### PR #121: Usability Improvements
- **Similarity Detection**: Implemented Jaccard similarity (intersection over union) to detect duplicate text
- **Auto-Async**: Automatically enable async mode when `num_candidates > 1` for better performance
- **Timeout Handling**: Added proper timeout support in async coordinator with graceful degradation
- **AI Artifact Removal**: Added 9 new regex patterns to clean AI response artifacts

### PR #145: Logical Inference Feature (August 2, 2025)
- **LLM-Based Logical Inference**: Replaced hardcoded templates with genuine LogicalInferenceEngine using Gemini API
- **Multiple Analysis Types**: Supports full reasoning, causal chains, constraint satisfaction, contradiction detection, and implications
- **Structured Response Parsing**: Robust parsing of LLM responses into structured InferenceResult objects
- **Display Formatting**: Three verbosity levels (brief, standard, detailed) for different use cases
- **Integration Points**: Enhanced reasoning system, async coordinator, and CLI all use the new engine
- **Backward Compatibility**: Falls back to rule-based system when no GenAI client available

### PR #158: Phase 2 Architecture Optimization (August 4, 2025)
- **Coordinator Architecture Unification**: Created `BatchOperationsBase` to eliminate ~180 lines of duplicate code from `AsyncCoordinator`
- **Batch Logical Inference Optimization**: Reduced API calls from O(N) to O(1) for logical inference processing
- **Inheritance Pattern**: `AsyncCoordinator` now inherits from `BatchOperationsBase` for shared functionality
- **Test Method Signature Updates**: Changed `_run_batch_logical_inference(candidates)` to `_run_batch_logical_inference(ideas)` parameter name
- **Batch Function Return Format**: Batch functions return tuples `(results, token_count)` not just results
- **Safe Module Patching**: Patch batch functions where they're imported (`batch_operations_base.BATCH_FUNCTIONS`), not where defined
- **Timing Constraints for CI**: Relaxed concurrent execution tests from 0.15s to 0.25s threshold for CI reliability

### PR #162: Parameter Standardization & Comprehensive Test Fixing (August 6, 2025)
- **Comprehensive Parameter Standardization**: Successfully migrated entire codebase from `theme/constraints/criteria` to unified `topic/context` parameters across 62 files (3,739 additions, 886 deletions)
- **Systematic CI Test Fix Protocol**: Developed 4-phase approach for fixing test failures after major refactoring - categorize failures, fix systematically, target correct mock paths, verify comprehensively
- **Mock Path Targeting**: Critical insight that mocks must target actual production code paths, not indirection layers (e.g., mock `improve_ideas_batch` not `improve_idea` wrapper)
- **Re-evaluation Bias Prevention**: Tests correctly validate that original context is preserved during re-evaluation to prevent inflated scores
- **Logical Inference Integration**: Successfully integrated `logical_inference` parameter into structured output prompts when provided
- **Test Coverage**: Added comprehensive test modules (test_parameter_standardization.py, test_reevaluation_bias.py, test_information_flow.py) for regression prevention
- **Batch Function Compatibility**: Ensured all test mocks match expected return format of batch functions (tuple with results and token count), preventing test failures during batch operation refactoring and maintaining consistency across coordinator architectures

### PR #182: Phase 3.2c AsyncCoordinator Integration (November 8, 2025)
- **Orchestrator Injection Pattern**: Batch methods accept optional `orchestrator` parameter for dependency injection, enabling test flexibility while maintaining stateful workflow orchestrator
- **Lazy Instantiation Fallback**: When both `orchestrator` parameter and `self.orchestrator` are None, batch methods create temporary WorkflowOrchestrator instance, ensuring backward compatibility with existing test patterns
- **Test Pattern Preservation**: Fixed 11 failing tests across 4 modules by restoring lazy instantiation removed in earlier commit, avoiding need to update all tests individually
- **Workflow Delegation**: AsyncCoordinator now delegates 7 of 9 workflow steps to WorkflowOrchestrator (generation, evaluation, advocacy, skepticism, improvement, re-evaluation, results building)
- **Async Feature Preservation**: All async-specific optimizations maintained (parallel execution with asyncio.gather, timeout handling, progress callbacks, semaphore-based concurrency)