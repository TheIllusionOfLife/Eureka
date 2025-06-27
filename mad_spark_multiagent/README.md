# MadSpark Multi-Agent System

An AI-powered idea generation and evaluation system using Google's Gemini API with multiple specialized agents.

## Features

- **Hybrid Architecture**: Choose between ADK framework (production) or direct API calls (development)
- **Temperature Control**: Adjust creativity levels from conservative (0.1) to highly creative (1.0)
- **Multi-Agent Architecture**: Specialized agents for generation, evaluation, advocacy, and criticism
- **Structured Workflows**: Coordinated multi-step processes for idea refinement
- **Japanese Language Support**: Optimized for Japanese prompts and responses

## Quick Start

1. **Setup Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   pip install -r requirements.txt
   ```

2. **Basic Usage**
   ```bash
   python coordinator.py
   ```

3. **Programmatic Usage**
   ```python
   from coordinator import run_multistep_workflow
   
   theme = "未来の移動手段"
   constraints = {"mode": "逆転", "random_words": ["猫", "宇宙船"]}
   
   # ADK Framework approach (recommended for production)
   result = run_multistep_workflow(theme, constraints, temperature=0.8, use_adk=True)
   
   # Direct function approach (good for debugging/development)
   result = run_multistep_workflow(theme, constraints, temperature=0.8, use_adk=False)
   ```

## Architecture

### Agents

1. **IdeaGenerator** (`agent_defs/idea_generator.py`)
   - Generates creative ideas based on themes and constraints
   - Temperature controls creativity level
   - Supports reverse thinking mode and keyword integration

2. **Critic** (`agent_defs/critic.py`)
   - Evaluates ideas on a 1-5 scale
   - Provides detailed feedback and reasoning
   - Uses lower temperature for consistent evaluation

3. **Advocate** (`agent_defs/advocate.py`)
   - Highlights positive aspects and potential benefits
   - Supports ideas with constructive arguments
   - Balanced temperature for nuanced advocacy

4. **Skeptic** (`agent_defs/skeptic.py`)
   - Identifies risks, problems, and weaknesses
   - Provides critical analysis and counterarguments
   - Helps ensure thorough evaluation

### Workflow

```
Theme + Constraints → IdeaGenerator → [Ideas]
    ↓
[Ideas] → Critic → [Scored Ideas]
    ↓
Top Ideas → Advocate + Skeptic → [Final Candidates with Debate]
```

## API Response Format

```json
{
  "status": "success|error",
  "results": [
    {
      "idea": "Generated idea text",
      "score": 4,
      "critic_comment": "Evaluation reasoning",
      "advocacy": "Positive arguments",
      "criticism": "Critical analysis"
    }
  ]
}
```

## Configuration

### Temperature Settings
- **0.1-0.3**: Conservative, focused responses
- **0.4-0.6**: Balanced creativity and coherence
- **0.7-0.9**: High creativity, more varied outputs
- **1.0**: Maximum creativity (may be less coherent)

### Constraint Types
- `mode: "逆転"`: Enables reverse thinking approach
- `random_words: ["word1", "word2"]`: Forces integration of specific keywords

## Project Structure

```
mad_spark_multiagent/
├── agent_defs/           # Agent implementations
│   ├── idea_generator.py # Creative idea generation
│   ├── critic.py         # Idea evaluation
│   ├── advocate.py       # Positive analysis
│   └── skeptic.py        # Critical analysis
├── coordinator.py        # Main workflow orchestration
├── requirements.txt      # Dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## Requirements

- Python 3.8+
- Google Gemini API access
- Dependencies: `google-generativeai`, `google-adk`, `python-dotenv`

## Architecture Approaches

### **ADK Framework Mode (`use_adk=True`)** - Recommended for Production
- Uses proper Google ADK `agent.invoke()` calls
- Better abstraction and error handling
- Follows ADK best practices from PR #42
- More robust for production deployment

### **Direct Function Mode (`use_adk=False`)** - Good for Development  
- Direct API calls to agent tool functions
- Simpler debugging and development
- Faster iteration cycles
- Based on PR #44 simplicity approach

### **Best of Both Worlds**
The hybrid implementation combines:
- **PR #42**: Proper ADK usage, clean package structure, workflow organization
- **PR #43**: Robust error handling patterns and comprehensive architecture
- **PR #44**: Temperature control, direct API flexibility, simplified configuration

Each agent is implemented as both an ADK agent and a standalone function, giving you flexibility to choose the approach that best fits your use case.