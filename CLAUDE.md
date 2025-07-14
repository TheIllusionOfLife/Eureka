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
- **CLI Interface**: `PYTHONPATH=src python -m madspark.cli.cli "theme" "constraints"`
- **Web Interface**: `cd web && docker-compose up`
- **Run Tests**: `PYTHONPATH=src pytest` (comprehensive test suite with 90%+ coverage) or `python tests/test_basic_imports_simple.py` (basic imports only)

## Testing Approach
- **CI-Safe Tests**: Tests must run without external API calls using comprehensive mocking
- **Current Infrastructure**: Full comprehensive test suite with 6 test modules (agents, coordinators, utils, cli, integration, interactive EOF)
- **Mock Mode**: Primary testing mode to avoid API costs
- **Coverage Goals**: 90%+ for critical paths (achieved with PR #84 comprehensive test suite)

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
cd web && docker-compose up

# Use Playwright MCP for testing
mcp__playwright__playwright_navigate(url="http://localhost:3000")
mcp__playwright__playwright_fill(selector="input[name='theme']", value="test theme")
mcp__playwright__playwright_screenshot(name="test_results", fullPage=true)
```

## Development Philosophy

- **Test-Driven Development**: Write tests first, verify failure, then implement
- **Systematic Approaches**: No shortcuts - follow complete protocols
- **Branch Workflow**: Always create feature branches before any work
- **Commit at Milestones**: Commit when completing logical units of work