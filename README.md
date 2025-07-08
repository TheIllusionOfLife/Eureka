# Eureka

A collection of AI-powered experimental projects and research initiatives.

## Projects

### MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-2.1%20In%20Progress-blue)](#madspark-multi-agent-system) [![Architecture](https://img.shields.io/badge/Architecture-Enhanced%20Reasoning-purple)](#architecture) [![Testing](https://img.shields.io/badge/Testing-92%25%20Coverage-success)](#testing--development)

**Location**: `mad_spark_multiagent/`

An AI-powered idea generation and evaluation system using Google's Gemini API with multiple specialized agents. This project implements a **sophisticated reasoning architecture** that evolves from basic agent coordination to advanced context-aware behaviors with logical inference, multi-dimensional evaluation, and agent memory systems.

#### Key Features

**Phase 1 Foundation (Completed)**:
- **🏗️ Hybrid Architecture**: Three operational modes (Mock, Direct API, ADK Framework)
- **🤖 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🌡️ Temperature Control**: Full preset system with stage-specific creativity control
- **🔍 Novelty Filtering**: Lightweight duplicate detection and similarity filtering
- **📚 Bookmark & Remix**: Persistent idea storage with tagging and remix capabilities
- **🖥️ Enhanced CLI**: Comprehensive command-line interface

**Phase 2.1 Enhanced Reasoning (In Progress)**:
- **🧠 Context-Aware Agents**: Agents reference conversation history for informed decisions
- **🔗 Logical Inference**: Sophisticated reasoning chains with confidence scoring
- **📊 Multi-Dimensional Evaluation**: 7-dimension assessment framework (feasibility, innovation, impact, etc.)
- **💾 Agent Memory**: Persistent context storage with intelligent similarity search
- **💬 Conversation Analysis**: Workflow pattern detection and completeness tracking
- **🧪 Production Ready**: 92% test coverage, CI/CD validation, and comprehensive error handling

#### Quick Start

```bash
cd mad_spark_multiagent

# Set up environment (requires Python 3.10+)
make install

# Run basic tests (no API key required)
make test-basic

# Run the system (requires GOOGLE_API_KEY in .env)
make run
```

#### Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Phase 1 Foundation** | ✅ Complete | All basic multi-agent features implemented |
| Mock Mode | ✅ Working | Cost-free development and testing |
| Direct API | ✅ Working | Production-ready Gemini integration |
| ADK Framework | ⚠️ Issues | Integration challenges documented |
| **Phase 2.1 Enhanced Reasoning** | 🚧 In Progress | Advanced reasoning system implemented |
| Context Memory | ✅ Working | Intelligent context storage and retrieval |
| Logical Inference | ✅ Working | Reasoning chains with confidence scoring |
| Multi-Dimensional Evaluation | ✅ Working | 7-dimension assessment framework |
| Agent Conversation Tracking | ✅ Working | Workflow analysis and pattern detection |
| Testing Infrastructure | ✅ Working | 92% test coverage across all components |
| Documentation | ✅ Complete | Comprehensive guides and API documentation |

#### Architecture

**Core System Architecture**:
1. **Mock Mode** 🔄: Cost-free development with consistent test responses
2. **Direct Function Mode** 🚀: Production-ready Gemini API integration (recommended)
3. **ADK Framework Mode** 🏗️: Advanced agent management with Google ADK

**Enhanced Reasoning Architecture (Phase 2.1)**:
- **ReasoningEngine**: Main coordinator for all reasoning capabilities
- **ContextMemory**: Persistent storage with intelligent similarity-based retrieval
- **LogicalInference**: Reasoning chains using formal logic rules (modus ponens, etc.)
- **MultiDimensionalEvaluator**: Sophisticated evaluation across 7 dimensions
- **AgentConversationTracker**: Workflow analysis and pattern detection

**Enhanced Workflow**: `Theme + Constraints → Context-Aware Agents → Reasoning Engine → Multi-Dimensional Evaluation → Final Results with Reasoning Insights`

#### Development

- **Requirements**: Python 3.10+, Google Gemini API access
- **Testing**: `make test-basic` for quick verification, `make test` for comprehensive testing
- **Documentation**: See `mad_spark_multiagent/README.md` for detailed setup and usage
- **Architecture Notes**: See `mad_spark_multiagent/CLAUDE.md` for implementation decisions

#### Implementation Background

This implementation resulted from analyzing and combining the best features from three different architectural approaches:
- **PR #42**: Proper ADK usage and clean package structure
- **PR #43**: Robust error handling and comprehensive testing infrastructure  
- **PR #44**: Temperature control and direct API simplicity

The hybrid approach provides flexibility to choose between ADK framework or direct API calls based on specific needs, with graceful fallbacks ensuring system reliability.

---

## Getting Started

Each project directory contains its own README with specific setup instructions. Most projects require:

- Python 3.10 or higher
- Appropriate API keys for external services
- Virtual environment setup (automated via Makefiles where available)

## Contributing

1. Navigate to the specific project directory
2. Follow the project-specific README for setup
3. Run tests before making changes
4. Document any architectural decisions

## License

See [LICENSE](LICENSE) file for details.