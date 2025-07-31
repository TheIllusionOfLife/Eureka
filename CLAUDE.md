# MadSpark Multi-Agent System - Project Guidelines

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Eureka features the MadSpark Multi-Agent System, a sophisticated AI-powered experimental platform implementing a hybrid architecture with multiple operational modes.

## Architecture Patterns
- **Package Structure**: Uses standard `src/madspark/` layout with subpackages for agents, core, utils, cli (web_api package is placeholder)
- **Import Strategy**: Try/except blocks with relative fallbacks for multi-environment compatibility
- **Mock-First Development**: All functionality must work in mock mode without API keys
- **Operational Modes**: Mock (development), Direct API (production), ADK Framework (experimental)

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

## Dependencies
- **Python**: 3.10+ required for TypedDict and modern features
- **Core**: google-genai, python-dotenv (from `config/requirements.txt`)
- **Testing**: pytest, pytest-mock, pytest-asyncio
- **Caching**: redis (available but optional)
- **Optional**: ruff for linting, mypy for type checking
- **Web**: FastAPI, React 18.2, TypeScript, Docker (in `web/` directory)

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

## Session Learnings

### PR #130: AI-Powered MultiDimensional Evaluation (July 31, 2025)
- **AI-Powered Evaluation**: Replaced keyword-based evaluation with AI-powered system for language-agnostic support
- **Mock-Mode Compatibility**: Use try/except with SimpleNamespace fallback to maintain mock-first development
- **No Graceful Degradation**: System explicitly fails with clear error messages when API key not configured
- **Human-Readable Prompts**: Format context as "Theme: X. Constraints: Y" instead of raw dictionary strings
- **Systematic PR Review**: Successfully addressed feedback from claude[bot], coderabbitai[bot], cursor[bot], and gemini-code-assist[bot]

### PR #121: Usability Improvements
- **Similarity Detection**: Implemented Jaccard similarity (intersection over union) to detect duplicate text
- **Auto-Async**: Automatically enable async mode when `num_candidates > 1` for better performance
- **Timeout Handling**: Added proper timeout support in async coordinator with graceful degradation
- **AI Artifact Removal**: Added 9 new regex patterns to clean AI response artifacts