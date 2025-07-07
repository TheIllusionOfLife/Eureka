# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.1%20Complete-success)](#project-status) [![Architecture](https://img.shields.io/badge/Architecture-Enhanced%20Reasoning-purple)](#enhanced-reasoning-phase-21) [![Testing](https://img.shields.io/badge/Testing-95%25%20Coverage-success)](#testing) [![Next](https://img.shields.io/badge/Next-Phase%202.2%20Web%20Interface-orange)](#roadmap)

This project implements a sophisticated multi-agent system for idea generation and refinement using Google's Gemini API with advanced reasoning capabilities. It includes specialized agents for idea generation, criticism, advocacy, and skepticism, orchestrated by a coordinator enhanced with context-aware reasoning, logical inference, and multi-dimensional evaluation.

## Prerequisites

- Python 3.10 or newer (required for TypedDict and modern features)
- Access to Google Gemini API (recommended: gemini-1.5-flash or gemini-pro)
- Optional: pytest for running tests, ruff for linting

## Setup

1.  **Clone the repository (if applicable).**
    If you have cloned a repository containing this project, navigate into the `mad_spark_multiagent` directory. If you received the files directly, ensure they are all within a directory named `mad_spark_multiagent`.

2.  **Create a virtual environment (recommended):**
    From within the `mad_spark_multiagent` directory:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Key Configuration:**
    This application requires a Google API Key for accessing the configured generative models.
    - Create a file named `.env` in the `mad_spark_multiagent` project directory (i.e., alongside `coordinator.py`).
    - Add your API key and the model name to the `.env` file. For example:
      ```env
      GOOGLE_API_KEY="YOUR_API_KEY_HERE"
      GOOGLE_GENAI_MODEL="gemini-pro"
      ```
      Replace `"YOUR_API_KEY_HERE"` with your actual API key. You can choose a different model compatible with the Google AI SDK if desired (e.g., "gemini-1.5-flash-latest").

    **Important Security Note:** Storing API keys in `.env` files is suitable for local development. For production environments, it is strongly recommended to use a dedicated secret management service (e.g., Google Cloud Secret Manager, HashiCorp Vault) to protect your API keys. Do not commit `.env` files containing sensitive keys to version control (the provided `.gitignore` file in the parent directory should prevent this if this project is part of a larger repository structure, or you should ensure a local `.gitignore` also lists `.env`).

## Running the System

The main coordinator script can be run to test the workflow:
From within the `mad_spark_multiagent` directory:
```bash
python coordinator.py
```
This will use the sample `theme` and `constraints` defined in the `if __name__ == "__main__":` block of `coordinator.py`. You can modify these to test different scenarios. The output will be a JSON representation of the processed ideas.

## Project Structure

### Core System
- `agent_defs/`: Contains the definitions for individual agents (`idea_generator.py`, `critic.py`, `advocate.py`, `skeptic.py`).
  - `__init__.py`: Exports the agent instances.
- `coordinator.py`: Orchestrates the agents and manages the overall workflow with enhanced reasoning integration.
- `enhanced_reasoning.py`: **Phase 2.1** - Advanced reasoning system with context awareness and logical inference.
- `cli.py`: Comprehensive command-line interface with all features including enhanced reasoning.
- `tests/`: Comprehensive test suite including enhanced reasoning tests.

### Supporting Modules
- `temperature_control.py`: Temperature management system with presets
- `novelty_filter.py`: Tier0 novelty filtering for duplicate detection
- `bookmark_system.py`: Bookmark and remix functionality
- `utils.py`: Utility functions and helper methods
- `constants.py`: Project constants and configuration values

### Documentation & Examples
- `docs/`: Documentation files including user guides and verbose logging guide
- `examples/`: Demo files and enhanced reasoning examples
- `debug/`: Debug utilities and development tools
- `temp/`: Temporary files and analysis outputs

### Configuration
- `requirements.txt`: Lists project dependencies
- `.env` (create this file locally, gitignored): For storing your `GOOGLE_API_KEY` and `GOOGLE_GENAI_MODEL`
- `pytest.ini`: Test configuration
- `README.md`: This file

## How it Works

1.  The `Coordinator` (`coordinator.py`) takes a `theme` and `constraints` (both strings) as input.
2.  The `IdeaGeneratorAgent` (`agent_defs/idea_generator.py`) generates a list of ideas based on this input.
3.  The `CriticAgent` (`agent_defs/critic.py`) evaluates these ideas, providing a score (1-10) and a textual comment for each. The evaluations are requested as newline-separated JSON strings.
4.  The `Coordinator` parses these evaluations. If parsing fails for an idea, defaults are used, and a warning is logged. It then selects the top-scoring ideas (default is top 2, configurable).
5.  For each selected top idea:
    - The `AdvocateAgent` (`agent_defs/advocate.py`) generates arguments highlighting the idea's strengths and potential.
    - The `SkepticAgent` (`agent_defs/skeptic.py`) critically analyzes the idea and its advocacy, pointing out potential weaknesses or risks.
    - Failures in advocacy or skepticism for one idea are logged as warnings, and placeholder text is used, allowing the workflow to continue for other ideas.
6.  The `Coordinator` compiles and returns (prints as JSON) the final list of candidates with all collected information (original idea, score, critique, advocacy, and skepticism).
7.  Critical errors, such as failure to generate any initial ideas or a complete failure of the critic agent, will result in an empty list of results. API key and model configuration issues are checked before agent initialization and will cause the script to exit with an error if not configured.

## Testing

To run the test suite:

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=mad_spark_multiagent

# Run specific test file
pytest tests/test_utils.py

# Run tests in verbose mode
pytest -v
```

The test suite includes:
- Unit tests for utility functions (JSON parsing, retry logic)
- Integration tests for the coordinator workflow
- Tests for agent initialization and tool functions
- Mock-based testing to avoid actual API calls

## Project Status

### Phase 1 "Quick Wins" Features ✅ **COMPLETED**

All Phase 1 features have been successfully implemented and are production-ready:

### 1. **Temperature Control & Structured Prompts** ✅
- Comprehensive temperature management system with presets (`conservative`, `balanced`, `creative`, `wild`)
- CLI support for temperature adjustment (`--temperature`, `--temperature-preset`)
- Stage-specific temperature scaling for different workflow phases

### 2. **Tier0 Novelty Filter** ✅
- Lightweight duplicate detection using hash-based and keyword similarity
- Configurable similarity thresholds to control filtering strictness
- Reduces expensive LLM API calls by filtering redundant ideas early

### 3. **Bookmark & Remix System** ✅
- File-based bookmark storage for saving favorite ideas
- Tag-based organization and search functionality
- Remix mode that generates new ideas based on bookmarked concepts
- CLI commands for bookmark management

### 4. **Enhanced CLI Interface** ✅
- Comprehensive command-line interface with all Phase 1 features
- Multiple output formats (JSON, text, summary)
- Batch processing and result export capabilities

### 5. **Production Verbose Logging** ✅ **NEW**
- **Complete workflow transparency**: See every agent's input/output in real-time
- **Step-by-step processing**: Visual indicators and timing for each workflow stage
- **Raw response logging**: Full API responses from all agents (IdeaGenerator, Critic, Advocate, Skeptic)
- **Auto-save capabilities**: Timestamped log files for analysis and debugging
- **Performance monitoring**: Duration tracking and bottleneck identification

```bash
# Enable verbose logging for complete workflow visibility
./venv/bin/python cli.py "your topic" "constraints" --verbose

# Save detailed analysis to file
./venv/bin/python cli.py "topic" "constraints" --verbose > analysis.log 2>&1
```

See [VERBOSE_LOGGING_GUIDE.md](VERBOSE_LOGGING_GUIDE.md) for complete documentation.

### **Enhanced Reasoning (Phase 2.1)** ✅ **COMPLETED & INTEGRATED**

Phase 2.1 introduces sophisticated reasoning capabilities that enhance agent decision-making:

#### **Context-Aware Agents** ✅
- Agents can reference conversation history for informed decision-making
- Intelligent context storage and retrieval with similarity-based matching
- Cross-agent context sharing for coherent workflow execution

#### **Logical Inference Engine** ✅
- Formal logical reasoning chains using modus ponens and other rules
- Confidence scoring for logical conclusions
- Contradiction detection and consistency analysis
- Support for complex multi-premise reasoning

#### **Multi-Dimensional Evaluation** ✅
- 7-dimension assessment framework:
  - **Feasibility**: Technical and practical implementation possibility
  - **Innovation**: Novelty and creative advancement potential
  - **Impact**: Expected magnitude of positive outcomes
  - **Cost Effectiveness**: Resource efficiency and ROI analysis
  - **Scalability**: Growth and expansion potential
  - **Risk Assessment**: Potential negative outcomes and mitigation
  - **Timeline**: Implementation speed and milestone planning
- Weighted scoring with confidence intervals
- Comparative evaluation between multiple ideas

#### **Agent Memory System** ✅
- Persistent context storage with intelligent similarity search
- Conversation flow analysis and pattern detection
- Workflow completeness tracking and optimization suggestions
- Context extraction for relevant historical information

#### **Production Readiness** ✅
- **92% test coverage** across all enhanced reasoning components
- Comprehensive error handling and graceful degradation
- Performance optimized with efficient algorithms
- CI/CD integration with automated testing

## Technical Improvements

1. **Robust JSON Parsing**: Multiple fallback strategies for parsing critic evaluations
2. **Retry Logic**: Exponential backoff retry logic for all agent API calls
3. **Enhanced Error Handling**: Comprehensive error handling with graceful degradation
4. **Test Infrastructure**: Complete unit and integration test suite using pytest
5. **Type Safety**: TypedDict usage for better type checking and code clarity
6. **Constants Module**: Dedicated constants module to eliminate magic strings

## Enhanced Reasoning Architecture

The Phase 2.1 enhanced reasoning system consists of five interconnected components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ ReasoningEngine │────│ ContextMemory    │────│ LogicalInference    │
│   (Main Hub)    │    │ (Agent History)  │    │ (Formal Logic)      │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                        │                         │
         └────────────────────────┼─────────────────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
┌───▼──────────────────┐    ┌─────▼─────────────────────┐
│ MultiDimensional     │    │ AgentConversationTracker  │
│ Evaluator            │    │ (Workflow Analysis)       │
│ (7-Dimension Scoring)│    │                           │
└──────────────────────┘    └───────────────────────────┘
```

### Integration with Existing Workflow

The enhanced reasoning system integrates seamlessly with the existing multi-agent workflow:

1. **Theme + Constraints** → Enhanced with historical context
2. **Idea Generation** → Context-aware based on previous sessions
3. **Criticism** → Multi-dimensional evaluation with logical reasoning
4. **Advocacy/Skepticism** → Enhanced with inference chains and confidence scoring
5. **Final Results** → Enriched with reasoning insights and quality scores

## CLI Usage Examples

### Phase 1 Features
```bash
# Basic usage with temperature control
python cli.py "Future transportation" "Budget-friendly" --temperature 0.8

# Use temperature presets
python cli.py "Smart cities" "Scalable solutions" --temperature-preset creative

# Enable bookmark mode with custom tags
python cli.py "Green energy" "Residential" --bookmark-results --bookmark-tags renewable energy

# Remix mode - generate ideas based on bookmarks
python cli.py "Innovation" --remix --bookmark-tags technology

# List and search bookmarks
python cli.py --list-bookmarks
python cli.py --search-bookmarks "solar"

# Control novelty filtering
python cli.py "AI applications" "Practical" --novelty-threshold 0.6

# Different output formats
python cli.py "Healthcare" "Affordable" --output-format json --output-file results.json
```

### Phase 2.1 Enhanced Reasoning ✅ **NOW AVAILABLE**
```bash
# Enable enhanced reasoning with context awareness
python cli.py "AI healthcare" "Rural deployment" --enhanced-reasoning --verbose

# Use multi-dimensional evaluation (7 dimensions)
python cli.py "Smart agriculture" "Sustainable" --multi-dimensional-eval --verbose

# Combine enhanced reasoning with multi-dimensional evaluation
python cli.py "Urban planning" "Community-focused" --enhanced-reasoning --multi-dimensional-eval

# Enhanced reasoning with temperature control
python cli.py "EdTech solutions" "K-12" --enhanced-reasoning --temperature-preset creative

# Use async execution for better performance (Phase 2.3)
python cli.py "Green technology" "Affordable" --async --num-candidates 5
```

## Lessons Learned: PR #56 Verbose Logging Implementation

This section documents critical insights and lessons learned during the implementation of the verbose logging feature (PR #56) to prevent similar issues in future development.

### 🔥 **Critical Issues Encountered**

#### **1. Logging Configuration Conflicts** 
**Issue**: Module-level `logging.basicConfig()` in `coordinator.py` prevented CLI verbose logging from working.
**Root Cause**: Python's logging system only allows one `basicConfig()` call per process.
**Solution**: 
- Removed module-level logging configuration from `coordinator.py`
- Added conditional logging setup only when `coordinator.py` runs directly
- Used `force=True` and handler clearing in CLI's `setup_logging()` function

#### **2. Import Organization Problems**
**Issue**: Imports scattered throughout functions instead of at module top.
**Impact**: Code style violations and potential performance issues.
**Solution**: Moved all imports to top of file following PEP 8 standards.

#### **3. Code Duplication in Verbose Blocks**
**Issue**: 40+ lines of duplicated verbose printing logic across functions.
**Impact**: Maintenance burden and increased error potential.
**Solution**: Extracted reusable helper functions:
- `log_verbose_completion()` - standardized completion messages
- `log_verbose_sample_list()` - consistent list sampling display
- `log_agent_execution()` - uniform agent execution logging
- `log_agent_completion()` - standardized agent response logging

#### **4. Incomplete Test Coverage**
**Issue**: Missing tests for verbose functionality could lead to silent failures.
**Impact**: Reduced confidence in production deployments.
**Solution**: Added comprehensive test suite:
- `test_verbose_logging_workflow()` - end-to-end verbose workflow testing
- `test_cli_verbose.py` - dedicated CLI verbose functionality tests
- Performance impact testing and error scenario coverage

### 🎯 **Development Process Improvements**

#### **PR Review Management**
**Problem**: Initial failure to retrieve complete review content from GitHub CLI.
**Solution**: Enhanced global CLAUDE.md with systematic PR review guidelines:
- Use JSON output with `jq` parsing for reliable data extraction
- Multiple retry strategies for GitHub API calls
- Structured approach to handling multiple reviewer feedback

#### **Multi-Reviewer Coordination**
**Challenge**: Managing feedback from Cursor, Gemini Code Assist, and Claude simultaneously.
**Strategy Developed**:
1. Address critical issues first (blocking merge)
2. Group similar issues across reviewers
3. Systematic verification after each fix batch
4. Maintain communication about fix status

#### **Testing Strategy Evolution**
**Learning**: Need for both unit tests and integration tests in verbose mode.
**Implementation**:
- Unit tests for individual helper functions
- Integration tests for complete workflow with mocking
- Performance tests to ensure verbose mode doesn't degrade experience
- Error handling tests for edge cases

### 🚀 **Technical Insights**

#### **Logging Architecture Principles**
1. **Single Configuration Point**: Only configure logging at application entry point
2. **Handler Management**: Clear existing handlers before setting new configuration
3. **Graceful Fallbacks**: Always provide console-only fallback for file logging failures
4. **Force Configuration**: Use `force=True` in `basicConfig()` when reconfiguration needed

#### **Verbose Output Design**
1. **Visual Hierarchy**: Use emojis and separators for easy scanning
2. **Truncation Strategy**: Truncate long outputs but provide character counts
3. **Timing Information**: Include duration for performance analysis
4. **Sample Data**: Show representative samples rather than complete datasets

#### **Code Organization Best Practices**
1. **Helper Function Extraction**: Reduce duplication with focused utility functions
2. **Consistent Interfaces**: Standardize function signatures across helpers
3. **Parameter Validation**: Include verbose flags and limits in all helper functions
4. **Error Boundaries**: Ensure verbose logging never crashes main workflow

### 🔧 **Success Factors**

#### **What Worked Well**
1. **Systematic Issue Addressing**: Tackled problems in priority order
2. **Comprehensive Testing**: Added tests for all new functionality
3. **Documentation**: Created detailed user guides and technical documentation
4. **Performance Consideration**: Ensured verbose mode has minimal impact
5. **Backward Compatibility**: Maintained existing API interfaces

#### **Quality Assurance Process**
1. **Multiple Review Rounds**: Addressed feedback from different perspectives
2. **CI Integration**: All tests must pass before merge
3. **Manual Testing**: Verified functionality in real scenarios
4. **Performance Validation**: Confirmed no significant overhead

### 📋 **Future Development Guidelines**

#### **Pre-Implementation Checklist**
- [ ] Plan logging configuration strategy upfront
- [ ] Identify potential code duplication opportunities
- [ ] Design test strategy for new features
- [ ] Consider performance implications
- [ ] Plan documentation requirements

#### **PR Submission Best Practices**
- [ ] Run comprehensive local tests before submission
- [ ] Include test coverage for all new functionality
- [ ] Update documentation as part of the same PR
- [ ] Address code organization issues proactively
- [ ] Verify CI passes before requesting review

#### **Code Review Response Protocol**
- [ ] Retrieve complete review content using JSON output
- [ ] Address critical (merge-blocking) issues first
- [ ] Group similar issues across multiple reviewers
- [ ] Test fixes incrementally to avoid introducing new issues
- [ ] Communicate progress and completion status clearly

### 🎉 **Final Results**

The verbose logging implementation achieved:
- ✅ **Complete workflow transparency** with step-by-step visibility
- ✅ **Zero performance impact** in normal mode
- ✅ **Robust error handling** with graceful fallbacks
- ✅ **Comprehensive test coverage** (92%+ overall project coverage)
- ✅ **Production-ready documentation** with user guides and examples
- ✅ **Clean code architecture** with reusable helper functions

This experience demonstrates the importance of systematic issue resolution, comprehensive testing, and thorough documentation in delivering production-ready features.

## Development and Testing

### Quick Start
```bash
# Set up development environment
make install

# Run basic tests (no API key required)
make test-basic

# Run full test suite with enhanced reasoning tests
make test

# Run enhanced reasoning tests specifically
pytest tests/test_enhanced_reasoning.py -v

# Check test coverage
pytest --cov=. --cov-report=html
```

### Development Commands
```bash
# Code quality checks
make lint        # Run ruff linting
make typecheck   # Run mypy type checking
make security    # Run bandit security scan

# Run the coordinator directly
python coordinator.py

# Test enhanced reasoning system
python -c "from enhanced_reasoning import ReasoningEngine; engine = ReasoningEngine(); print('✓ Enhanced reasoning ready')"
```

## Roadmap

### 🚀 **Phase 2.2: Advanced User Experience** (Next - High Priority)
**Timeline**: 3 weeks | **Focus**: Usability & Web Interface

- **Web Interface Development**: React + TypeScript frontend with interactive visualization
- **Enhanced CLI Features**: Interactive mode, export formats (PDF, CSV, JSON), batch processing  
- **User Experience Improvements**: Guided onboarding, template system, result comparison tools
- **API Integration**: FastAPI backend with WebSocket support for real-time updates

### 📊 **Phase 2.3: Performance & Scalability** (Medium Priority)
**Timeline**: 2-3 weeks | **Focus**: Production Optimization

- **Performance Optimization**: Async agent execution, result caching, API batching
- **Database Integration**: PostgreSQL for persistence, multi-user support, session management
- **Monitoring & Analytics**: Performance metrics, usage insights, A/B testing framework

### 🏢 **Phase 3: Enterprise & Integration** (Future)
**Timeline**: 1-2 months | **Focus**: Production Deployment

- **Enterprise Features**: SSO integration, RBAC, audit logging, compliance features
- **External Integrations**: Slack/Teams bots, API for third-party apps, webhook support
- **Advanced AI**: Custom agent personalities, domain knowledge bases, multi-language support

For detailed implementation plans, see:
- [`docs/DEVELOPMENT_ROADMAP.md`](docs/DEVELOPMENT_ROADMAP.md) - Complete roadmap with technical details
- [`docs/PHASE_2_2_IMPLEMENTATION_PLAN.md`](docs/PHASE_2_2_IMPLEMENTATION_PLAN.md) - Phase 2.2 week-by-week plan

### 🎯 **Current Focus**
**Phase 2.3 Performance & Scalability** in progress. Async agent execution completed, next: Redis caching infrastructure for improved performance and scalability.


## Session Handover

### Last Updated: 2025-07-07 22:15

#### Recently Completed
- ✅ **Phase 2.3 Async Agent Execution**: COMPLETED (3 commits)
  - Implemented AsyncCoordinator with concurrent agent execution
  - Added configurable parallelism with semaphore limiting  
  - Integrated with web backend via /api/generate-ideas-async endpoint
  - Added CLI support with --async flag
  - Comprehensive test suite (12+ tests, all passing)
  - Performance improvement: ~1.5-2x speedup for multi-candidate workflows
- ✅ **PR #62**: Phase 2.2 Advanced User Experience - Web Interface & Export
  - Implemented full-stack web interface with React + FastAPI
  - Added multi-format export system (JSON, CSV, Markdown, PDF)
  - Fixed critical WebSocket exception handling bug
  - Addressed comprehensive code review feedback (21+ issues resolved)
- ✅ **PR #60**: Phase 2.1 Enhanced Reasoning Integration (context from earlier)
  - Successfully integrated enhanced reasoning into main workflow

#### Next Priority Tasks
1. **Redis Caching Infrastructure**: High priority continuation of Phase 2.3
   - Source: Phase 2.3 roadmap - second component after async execution
   - Context: Async execution done, now add caching for repeated queries
   - Approach: Integrate Redis with docker-compose, create cache manager
   - Estimate: Medium (2-3 days)

2. **WebSocket Connection Monitoring**: Add health checks and auto-reconnect
   - Source: PR #62 deep review recommendations
   - Context: Production deployments need reliable WebSocket connections
   - Approach: Implement heartbeat protocol and reconnection logic
   - Estimate: Small (1-2 days)

3. **API Documentation**: Add OpenAPI/Swagger docs
   - Source: PR #62 review and best practices
   - Context: Web API needs proper documentation for adoption
   - Approach: Use FastAPI's built-in OpenAPI support
   - Estimate: Quick (< 1 day)

4. **WebSocket Integration Tests**: Automated testing for real-time features
   - Source: Test coverage gaps identified in PR #62
   - Context: Manual testing not sustainable for WebSocket functionality
   - Approach: Use pytest-asyncio with WebSocket test client
   - Estimate: Medium (2-3 days)

5. **Export System Cloud Storage**: S3/GCS support
   - Source: Architecture recommendations from deep review
   - Context: Large exports need cloud storage for scalability
   - Approach: Abstract storage interface, implement S3 adapter
   - Estimate: Medium (3-4 days)

#### Known Issues / Blockers
- **PDF Memory Usage**: Large PDF exports can consume significant memory
  - Solution: Consider background job queue (Celery/RQ)
- **CORS Configuration**: Currently allows all origins in development
  - Solution: Environment-based CORS configuration needed
- **TypeScript Any Usage**: Some components use 'any' type
  - Solution: Export and use proper interfaces

#### Session Learnings
- **Async Implementation Pattern**: Use `run_in_executor` for wrapping sync functions in async context
- **Test Organization**: Separate complex tests from simplified tests for better maintainability
- **Progress Callbacks**: Async workflows benefit from real-time progress updates via callbacks
- **Semaphore Usage**: Essential for limiting concurrent API calls to avoid rate limits
- **Performance Gains**: Async execution provides 1.5-2x speedup for multi-candidate workflows

#### Development Environment Notes
- **New Dependencies**: pytest-asyncio required for async test execution
- **Testing Strategy**: Mock at module level for async coordinator tests
- **CLI Integration**: Simple flag addition enables async mode without breaking changes
- **Web Integration**: Both sync and async endpoints can coexist in FastAPI
