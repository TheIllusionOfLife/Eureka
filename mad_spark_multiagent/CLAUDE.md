# MadSpark Multi-Agent System - Development Documentation

## Project Overview

MadSpark is an AI-powered idea generation and evaluation system using Google's Gemini API with multiple specialized agents. This document captures key architectural decisions, lessons learned, and development practices for this project.

## Architecture Decisions

### Hybrid Architecture (Key Innovation)

After analyzing PRs #42, #43, and #44, we implemented a **hybrid architecture** that combines the best of all approaches:

```python
# Production-ready ADK framework approach
result = run_multistep_workflow(theme, constraints, use_adk=True)

# Development-friendly direct API calls
result = run_multistep_workflow(theme, constraints, use_adk=False)
```

**Rationale**: 
- **PR #42**: Proper ADK usage, clean package structure, workflow organization
- **PR #43**: Robust error handling, comprehensive testing infrastructure
- **PR #44**: Temperature control, direct API simplicity, streamlined configuration

### Agent Architecture

Four specialized agents with dual implementation:
1. **IdeaGenerator**: Creative idea generation with temperature control
2. **Critic**: 1-5 scale evaluation with reasoning
3. **Advocate**: Positive analysis and benefits highlighting
4. **Skeptic**: Critical analysis and risk identification

Each agent implemented as:
- **ADK Agent**: For production use with proper framework abstraction
- **Direct Function**: For development, testing, and debugging

## Technical Implementation

### Temperature Control

All agent functions support temperature parameters:
```python
generate_ideas(theme, constraints, temperature=0.9)  # High creativity
evaluate_ideas(ideas, temperature=0.3)              # Consistent evaluation
advocate_idea(idea, temperature=0.5)                # Balanced advocacy
criticize_idea(idea, temperature=0.5)               # Balanced criticism
```

### Import Strategy (Critical Learning)

**Issue**: Google ADK `Tool` class not available in current version
**Solution**: Graceful fallback pattern
```python
try:
    from google.adk.agents import Agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    Agent = None

if ADK_AVAILABLE:
    agent = Agent(...)
else:
    agent = None
```

### Error Handling Patterns

- **Structured responses**: `{"status": "success/error", "data": ..., "message": "..."}`
- **Graceful degradation**: System works even if ADK unavailable
- **Comprehensive logging**: All failures logged with context

## Testing Infrastructure

### Multi-Level Testing Strategy

1. **Basic Tests** (`test_basic.py`): Import verification, function signatures, helper functions
2. **Unit Tests** (`tests/`): Comprehensive mocked API testing
3. **Integration Tests**: Full workflow testing with both approaches
4. **CI/CD**: GitHub Actions across Python 3.10-3.13
5. **Docker**: Containerized testing environment

### Key Testing Patterns

```bash
# Quick verification (no API calls)
make test-basic

# Comprehensive testing
make test  

# Production testing
make run
```

### Virtual Environment Requirements

**Critical**: Always use virtual environment for dependencies
```bash
# Correct
source test_env/bin/activate && python coordinator.py
# or
make run

# Incorrect (will fail)
python coordinator.py  # Uses system Python
```

## Development Workflow

### Setup Process
1. `make install` - Set up virtual environment
2. `make test-basic` - Verify installation
3. `make run` - Test with real API
4. Development with either approach

### Makefile Commands
- `make run` - Run main system
- `make test-basic` - Quick functionality test
- `make test` - Full test suite
- `make docker-build` - Container testing
- `make clean` - Cleanup

## Lessons Learned

### 1. PR Analysis Was Critical
Comparing multiple implementations revealed:
- ADK framework provides abstraction but adds complexity
- Direct API calls easier for debugging
- Temperature control essential for creativity
- Error handling makes or breaks production use

### 2. Testing Infrastructure Investment
- Mock testing enables development without API costs
- CI/CD prevents regressions across Python versions
- Docker ensures reproducible environments
- Basic tests provide quick feedback loop

### 3. Import Issues Are Common
- ADK API changes frequently
- Graceful fallbacks essential
- Test both import paths
- Virtual environment isolation critical

### 4. Hybrid Approach Benefits
- Production gets robust ADK framework
- Development gets simple direct calls
- Both approaches share same business logic
- Testing covers both patterns

## Known Issues & Solutions

### Issue: ADK `invoke()` Method Missing
**Error**: `'LlmAgent' object has no attribute 'invoke'`
**Investigation**: ADK API has changed, need to find correct method
**Workaround**: Use direct function approach (`use_adk=False`)

### Issue: Output Truncation in Claude Code CLI
**Problem**: Output shows "+12 lines (ctrl+r to expand)"
**Solutions**: 
- Press `Ctrl+R` to expand
- Use `make run | less` for scrollable output
- Save to file: `make run > output.txt`

### Issue: Virtual Environment Confusion
**Problem**: Dependencies only in virtual environment
**Solution**: Always use Makefile commands or activate environment

## Future Development

### Phase 2 Features (Planned)
- GA core implementation with MOEA
- API Gateway & frontend integration
- Enhanced LLM self-scoring

### Phase 3 Features (Planned)
- MAP-Elites diversity extension
- Multi-agent debate tournaments
- Dynamic parameter adjustment

### Phase 4 Features (Planned)
- Conceptual Moves plugin library
- Open API & plugin ecosystem
- UI/UX polish & demo scenarios

## Best Practices Established

1. **Always use virtual environment** for Python dependencies
2. **Test both ADK and direct approaches** during development
3. **Mock API calls in tests** to avoid costs and rate limits
4. **Use structured error responses** for consistent handling
5. **Document architectural decisions** for future reference
6. **Implement graceful fallbacks** for optional dependencies
7. **Use CI/CD for multi-Python version testing**

## Quick Reference

### Essential Commands
```bash
make run           # Run MadSpark system
make test-basic    # Quick functionality test
make help          # See all available commands
```

### Key Files
- `coordinator.py` - Main workflow orchestration
- `agent_defs/` - Individual agent implementations
- `tests/` - Comprehensive test suite
- `Makefile` - Development commands
- `requirements.txt` - Dependencies
- `.env` - API configuration (create from .env.example)

---

**Last Updated**: 2025-06-27  
**Architecture**: Hybrid ADK + Direct Function Approach  
**Status**: Phase 1 Complete, Testing Infrastructure Ready