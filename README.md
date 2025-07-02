# Eureka

A collection of AI-powered experimental projects and research initiatives.

## Projects

### MadSpark Multi-Agent System

[![Phase](https://img.shields.io/badge/Phase-1%20Complete-green)](#madspark-multi-agent-system) [![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20ADK%2BDirect-blue)](#architecture) [![Testing](https://img.shields.io/badge/Testing-Multi--Level-success)](#testing--development)

**Location**: `mad_spark_multiagent/`

An AI-powered idea generation and evaluation system using Google's Gemini API with multiple specialized agents. This project implements a **hybrid architecture** combining the best features from multiple implementation approaches, providing both production-ready ADK framework integration and development-friendly direct API calls.

#### Key Features

- **🏗️ Hybrid Architecture**: Three operational modes (Mock, Direct API, ADK Framework)
- **🤖 Multi-Agent System**: IdeaGenerator, Critic, Advocate, and Skeptic agents
- **🎛️ Temperature Control**: Adjustable creativity levels (0.1-1.0) across all agents
- **🧪 Comprehensive Testing**: Unit, integration, CI/CD, and Docker testing
- **📚 Complete Documentation**: Team guides, troubleshooting, and architectural decisions

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
| Mock Mode | ✅ Working | Cost-free development and testing |
| Direct API | ✅ Working | Production-ready Gemini integration |
| ADK Framework | ⚠️ Issues | Integration challenges documented |
| Testing Infrastructure | ✅ Working | Multi-level strategy implemented |
| Documentation | ✅ Complete | Comprehensive guides available |

#### Architecture

The system supports three operational modes:

1. **Mock Mode** 🔄: Cost-free development with consistent test responses
2. **Direct Function Mode** 🚀: Production-ready Gemini API integration (recommended)
3. **ADK Framework Mode** 🏗️: Advanced agent management with Google ADK

**Workflow**: `Theme + Constraints → IdeaGenerator → Critic → Advocate + Skeptic → Final Results`

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