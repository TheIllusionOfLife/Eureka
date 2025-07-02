# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-1%20Complete-green)](https://github.com/your-repo/issues/4) [![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20ADK%2BDirect-blue)](./CLAUDE.md) [![Testing](https://img.shields.io/badge/Testing-Multi--Level-success)](#testing--development)

An AI-powered idea generation and evaluation system using Google's Gemini API with multiple specialized agents. This system implements a **hybrid architecture** combining the best features from multiple implementation approaches, providing both production-ready ADK framework integration and development-friendly direct API calls.

## Table of Contents
- [Project Status](#project-status)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Testing & Development](#testing--development)
- [Configuration](#configuration)
- [Known Issues & Troubleshooting](#known-issues--troubleshooting)
- [Team Development](#team-development)
- [API Reference](#api-reference)

## Project Status

### Current Phase: **Phase 1 Complete** ✅
- ✅ **Mock Mode**: Cost-free testing and development
- ✅ **Direct Function Approach**: Production-ready Gemini API integration  
- ⚠️ **ADK Framework Approach**: Implemented with known integration challenges
- ✅ **Comprehensive Testing**: Unit, integration, CI/CD, and Docker testing
- ✅ **Temperature Control**: Implemented across all agents
- ✅ **Multi-Agent Workflow**: IdeaGenerator → Critic → Advocate + Skeptic

### Implementation Context
This implementation resulted from analyzing and combining the best features of three different approaches:
- **PR #42**: Proper ADK usage, clean package structure, workflow organization
- **PR #43**: Robust error handling, comprehensive testing infrastructure  
- **PR #44**: Temperature control, direct API simplicity, streamlined configuration

**Latest Commit**: `6fdc01d` - Hybrid architecture implementation combining all approaches

## Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.10, 3.11, 3.12, 3.13)
- Google Gemini API access
- Git

### 1. Setup (Recommended)
```bash
# Clone and navigate to project
cd mad_spark_multiagent

# Set up virtual environment and install dependencies
make install

# Verify installation with basic tests (no API key required)
make test-basic

# Optional: Copy environment template for API testing
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY=your_actual_api_key_here
```

### 2. Run the System
```bash
# Run with hybrid approach testing (includes mock mode)
make run

# Or run specific modes
python coordinator.py  # Interactive mode
```

### 3. Verify Everything Works
```bash
# Quick functionality test (no API costs)
make test-basic

# Full test suite (if you have API key configured)
make test

# Check available commands
make help
```

**⚠️ Important**: Always run commands from the `mad_spark_multiagent` directory, not the parent directory.

## Architecture

### System Overview
```
Theme + Constraints → IdeaGenerator → [Ideas] → Critic → [Scored Ideas] 
                                        ↓
                    Top Ideas → Advocate + Skeptic → [Final Candidates with Debate]
```

### Hybrid Architecture (Key Innovation)

The system supports **three operational modes**:

#### 1. **Mock Mode** 🔄 (Default for testing)
```python
result = run_multistep_workflow(theme, constraints, mock_mode=True)
```
- **Purpose**: Cost-free development and testing
- **Benefits**: No API calls, consistent responses, perfect for CI/CD
- **Status**: ✅ Fully functional

#### 2. **Direct Function Mode** 🚀 (Recommended for production)
```python
result = run_multistep_workflow(theme, constraints, use_adk=False)
```
- **Purpose**: Production-ready with direct Gemini API calls
- **Benefits**: Simple, reliable, easy to debug
- **Status**: ✅ Fully functional
- **Based on**: PR #44 simplicity approach

#### 3. **ADK Framework Mode** 🏗️ (Advanced integration)
```python
result = run_multistep_workflow(theme, constraints, use_adk=True)
```
- **Purpose**: Uses Google ADK framework for advanced agent management
- **Benefits**: Better abstraction, following ADK best practices
- **Status**: ⚠️ Implemented with integration challenges
- **Based on**: PR #42 proper ADK usage

### Specialized Agents

Each agent implemented with **dual architecture** (ADK + Direct function):

1. **IdeaGenerator** (`agent_defs/idea_generator.py`)
   - **Purpose**: Creative idea generation with theme and constraint integration
   - **Temperature**: 0.9 (high creativity)
   - **Features**: Reverse thinking mode, keyword integration
   - **Output**: 3-5 creative ideas per theme

2. **Critic** (`agent_defs/critic.py`)
   - **Purpose**: Objective evaluation on 1-5 scale with detailed reasoning
   - **Temperature**: 0.3 (consistent evaluation)
   - **Features**: Scoring criteria, constructive feedback
   - **Output**: Scored ideas with evaluation comments

3. **Advocate** (`agent_defs/advocate.py`)
   - **Purpose**: Highlights benefits and positive potential
   - **Temperature**: 0.5 (balanced analysis)
   - **Features**: Constructive arguments, implementation insights
   - **Output**: Supportive analysis for each idea

4. **Skeptic** (`agent_defs/skeptic.py`)
   - **Purpose**: Critical analysis and risk identification
   - **Temperature**: 0.5 (balanced criticism)
   - **Features**: Risk assessment, counterarguments
   - **Output**: Critical evaluation highlighting potential issues

### Temperature Control System
All agents support fine-tuned creativity control:
- **0.1-0.3**: Conservative, focused responses
- **0.4-0.6**: Balanced creativity and coherence  
- **0.7-0.9**: High creativity, varied outputs
- **1.0**: Maximum creativity (may be less coherent)

## Testing & Development

### Multi-Level Testing Strategy

#### 1. **Basic Tests** (No API key required)
```bash
make test-basic
# ✅ Import verification
# ✅ Function signature validation
# ✅ Helper function testing
# ✅ Temperature parameter verification
```

#### 2. **Local Virtual Environment**
```bash
# Setup and activate
make install
source test_env/bin/activate

# Run tests
python test_basic.py
python coordinator.py
```

#### 3. **Docker Development**
```bash
# Build and test containerized environment
make docker-build
make docker-test

# Start development container
make docker-dev
```

#### 4. **CI/CD Pipeline** (GitHub Actions)
- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Test scenarios**: Unit tests, integration tests, security scanning
- **Triggers**: Push to main, Pull requests
- **Status**: ✅ Comprehensive coverage

#### 5. **Integration Testing**
```bash
# Full workflow testing with mocked API calls
make test

# Run specific test categories
pytest tests/ -v
pytest tests/test_coordinator.py
pytest tests/test_agent_functions.py
```

### Development Commands Reference

| Command | Purpose | Requirements |
|---------|---------|--------------|
| `make install` | Set up virtual environment | Python 3.10+ |
| `make test-basic` | Quick functionality test | None |
| `make run` | Run MadSpark system | Virtual env setup |
| `make test` | Full test suite | Virtual env + optional API key |
| `make docker-build` | Build Docker image | Docker |
| `make docker-test` | Test in container | Docker |
| `make clean` | Clean up generated files | None |
| `make help` | Show all commands | None |

## Configuration

### Environment Setup
```bash
# Copy template
cp .env.example .env

# Configure (add your actual API key)
GOOGLE_API_KEY=your_actual_api_key_here
TEMPERATURE_DEFAULT=0.7
```

### Constraint Types
```python
constraints = {
    "mode": "逆転",                    # Reverse thinking approach
    "random_words": ["猫", "宇宙船"],   # Force integration of keywords
    "focus": "sustainability"          # Additional focus areas
}
```

### Response Format
```json
{
  "status": "success|error",
  "results": [
    {
      "idea": "Generated idea text",
      "score": 4,
      "critic_comment": "Detailed evaluation reasoning",
      "advocacy": "Positive analysis and benefits",
      "criticism": "Critical analysis and risks"
    }
  ],
  "metadata": {
    "approach": "direct|adk|mock",
    "temperature": 0.7,
    "agents_used": ["IdeaGenerator", "Critic", "Advocate", "Skeptic"]
  }
}
```

## Known Issues & Troubleshooting

### Common Issues

#### ❌ "make: *** No rule to make target 'install'. Stop."
**Cause**: Running from wrong directory  
**Solution**: 
```bash
cd mad_spark_multiagent  # Navigate to project directory
make install
```

#### ❌ "Virtual environment not found"
**Cause**: Virtual environment not created  
**Solution**:
```bash
make install  # This creates test_env/ directory
make test-basic
```

#### ❌ ADK Integration Errors
**Current Status**: ADK approach returns "ERROR: No response text extracted from ADK agent"  
**Workaround**: Use direct function approach:
```python
# Use this instead of ADK approach
result = run_multistep_workflow(theme, constraints, use_adk=False)
```

#### ❌ Import Errors for Google ADK
**Cause**: ADK API changes or version incompatibility  
**Solution**: System uses graceful fallback - no action needed
```bash
# Verify fallback is working
make test-basic  # Should show "✓ All imports successful"
```

### Status Dashboard

| Component | Status | Notes |
|-----------|--------|-------|
| Mock Mode | ✅ Working | Perfect for development |
| Direct API | ✅ Working | Recommended for production |
| ADK Framework | ⚠️ Issues | Integration challenges |
| Temperature Control | ✅ Working | All agents support |
| Multi-Agent Workflow | ✅ Working | Full pipeline functional |
| Testing Infrastructure | ✅ Working | Comprehensive coverage |
| CI/CD Pipeline | ✅ Working | Multi-Python support |
| Docker Support | ✅ Working | Full containerization |

### Getting Help

1. **Check Logs**: Look for detailed error messages in terminal output
2. **Run Diagnostics**: `make test-basic` shows system health
3. **Check Environment**: Ensure you're in the `mad_spark_multiagent` directory
4. **Verify Setup**: `make install` should complete without errors
5. **Test Components**: Use mock mode for testing without API costs

## Team Development

### Development Workflow

1. **PR Analysis Process**: The current implementation resulted from thorough analysis of three different architectural approaches, establishing best practices for future development.

2. **Testing Philosophy**: 
   - All changes must pass `make test-basic`
   - Mock mode enables cost-free development
   - CI/CD pipeline prevents regressions
   - Docker ensures reproducible environments

3. **Architecture Evolution**:
   - **Phase 1**: ✅ Hybrid multi-agent system (Current)
   - **Phase 2**: Planned GA core with MOEA
   - **Phase 3**: Planned MAP-Elites diversity extension
   - **Phase 4**: Planned plugin ecosystem and UI polish

### Best Practices Established

1. **Always use virtual environment** for Python dependencies
2. **Test both approaches** (direct and ADK) during development
3. **Mock API calls in tests** to avoid costs and rate limits
4. **Use structured error responses** for consistent handling
5. **Document architectural decisions** in CLAUDE.md
6. **Implement graceful fallbacks** for optional dependencies
7. **Use CI/CD for multi-Python version testing**

### Contributing Guidelines

- **Setup**: Run `make install && make test-basic` before development
- **Testing**: Always test with mock mode first (`mock_mode=True`)
- **Documentation**: Update CLAUDE.md for architectural decisions
- **Commits**: Use conventional commit format (`feat:`, `fix:`, `docs:`)
- **PRs**: Ensure CI passes across all Python versions

## API Reference

### Core Functions

#### `run_multistep_workflow(theme, constraints, temperature=0.7, use_adk=True, mock_mode=False)`

**Parameters**:
- `theme` (str): Main topic for idea generation (e.g., "未来の移動手段")
- `constraints` (Dict[str, Any]): Additional constraints and modes
- `temperature` (float): Creativity level (0.1-1.0)
- `use_adk` (bool): Use ADK framework (True) or direct functions (False)
- `mock_mode` (bool): Use mock responses for testing (no API costs)

**Returns**: Dictionary with status, results, and metadata

#### Individual Agent Functions

```python
from agent_defs.idea_generator import generate_ideas
from agent_defs.critic import evaluate_ideas
from agent_defs.advocate import advocate_idea
from agent_defs.skeptic import criticize_idea

# All support temperature parameter
ideas = generate_ideas(theme, constraints, temperature=0.9)
scores = evaluate_ideas(ideas, temperature=0.3)
advocacy = advocate_idea(idea, temperature=0.5)
criticism = criticize_idea(idea, temperature=0.5)
```

---

## Project Structure

```
mad_spark_multiagent/
├── agent_defs/                 # Agent implementations
│   ├── __init__.py            # Agent exports
│   ├── idea_generator.py      # Creative idea generation
│   ├── critic.py              # Idea evaluation (1-5 scale)
│   ├── advocate.py            # Positive analysis
│   └── skeptic.py             # Critical analysis
├── tests/                     # Comprehensive test suite
│   ├── conftest.py           # Test configuration
│   ├── test_coordinator.py   # Workflow testing
│   └── test_agent_functions.py # Individual agent testing
├── coordinator.py             # Main workflow orchestration
├── test_basic.py             # Basic functionality tests
├── Makefile                  # Development commands
├── requirements.txt          # Dependencies
├── pytest.ini               # Test configuration
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Container orchestration
├── .github/workflows/ci.yml  # CI/CD pipeline
├── .env.example             # Environment template
├── CLAUDE.md               # Development documentation
└── README.md              # This file
```

---

**Last Updated**: 2025-07-02  
**Version**: Phase 1 Complete  
**Architecture**: Hybrid ADK + Direct Function Approach  
**Status**: Production-ready with comprehensive testing

For detailed development notes and architectural decisions, see [CLAUDE.md](./CLAUDE.md).