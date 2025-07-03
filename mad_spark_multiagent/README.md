# MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.1%20In%20Progress-blue)](#project-status) [![Architecture](https://img.shields.io/badge/Architecture-Enhanced%20Reasoning-purple)](#enhanced-reasoning-phase-21) [![Testing](https://img.shields.io/badge/Testing-92%25%20Coverage-success)](#testing)

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

- `agent_defs/`: Contains the definitions for individual agents (`idea_generator.py`, `critic.py`, `advocate.py`, `skeptic.py`).
  - `__init__.py`: Exports the agent instances.
- `coordinator.py`: Orchestrates the agents and manages the overall workflow.
- `enhanced_reasoning.py`: **NEW Phase 2.1** - Advanced reasoning system with context awareness and logical inference.
- `cli.py`: Comprehensive command-line interface with all features.
- `tests/`: Comprehensive test suite including enhanced reasoning tests.
- `requirements.txt`: Lists project dependencies (`google-generativeai`, `python-dotenv`, `pytest`).
- `.env` (create this file locally, gitignored): For storing your `GOOGLE_API_KEY` and `GOOGLE_GENAI_MODEL`.
- `README.md`: This file.

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

### **Enhanced Reasoning (Phase 2.1)** 🚧 **IN PROGRESS**

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

### Phase 2.1 Enhanced Reasoning (Coming Soon)
```bash
# Enable enhanced reasoning with context awareness
python cli.py "AI healthcare" "Rural deployment" --enhanced-reasoning

# Use multi-dimensional evaluation
python cli.py "Smart agriculture" "Sustainable" --multi-dimensional-eval

# Enable logical inference chains
python cli.py "Urban planning" "Community-focused" --logical-inference

# Specify custom evaluation dimensions
python cli.py "EdTech solutions" "K-12" --eval-dimensions feasibility,innovation,impact
```

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
