# MadSpark Phase 1 Implementation

MadSpark is an AI system consisting of idea generation and review agents using Google's Agent Development Kit (ADK). This implementation covers Phase 1 "Quick Wins" features.

## 🚀 Features

### Phase 1 Quick Wins (Implemented)
- **Temperature Slider & Structured Prompts**: Dynamic creativity control through temperature settings
- **Multi-Agent System**: Coordinated agents for idea generation, critique, and debate
- **Evaluation Cascade**: Tier-based filtering and evaluation system

## 📋 Prerequisites

- Python 3.10 or higher
- Google Cloud Project with Vertex AI API enabled
- Google Cloud authentication configured

## 🛠️ Installation

1. Clone the repository
2. Navigate to the `mad_spark_multiagent` directory
3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Google Cloud credentials
   ```

## 🏗️ Architecture

The system consists of four main agents:

1. **IdeaGeneratorAgent** (`agent_defs/idea_generator.py`)
   - Generates creative ideas based on themes and constraints
   - Uses configurable temperature for creativity control
   
2. **CriticAgent** (`agent_defs/critic.py`)
   - Evaluates generated ideas on a 1-5 scale
   - Provides reasoned critiques
   
3. **AdvocateAgent** (`agent_defs/advocate.py`)
   - Provides positive perspectives on ideas
   - Highlights potential benefits and opportunities
   
4. **SkepticAgent** (`agent_defs/skeptic.py`)
   - Offers critical analysis of ideas
   - Identifies potential risks and challenges

The **Coordinator** (`coordinator.py`) orchestrates the workflow:
1. Idea generation based on user input
2. Initial evaluation by the Critic
3. Multi-perspective analysis by Advocate/Skeptic
4. Final candidate list with comprehensive feedback

## 🎯 Usage

### Command Line

Run the coordinator directly:

```bash
python coordinator.py
```

### Programmatic Usage

```python
from coordinator import run_multistep_workflow

theme = "未来の移動手段"
constraints = {"mode": "逆転", "random_words": ["猫", "宇宙船"]}
results = run_multistep_workflow(theme, constraints)
```

### API Integration

The coordinator can be wrapped in a web API endpoint:

```python
from flask import Flask, request, jsonify
from coordinator import run_multistep_workflow

app = Flask(__name__)

@app.route('/api/madspark/generate', methods=['POST'])
def generate_ideas():
    data = request.json
    result = run_multistep_workflow(
        theme=data['theme'],
        constraints=data['constraints']
    )
    return jsonify(result)
```

## 📁 Project Structure

```
mad_spark_multiagent/
├── agent_defs/
│   ├── __init__.py
│   ├── idea_generator.py    # Idea generation agent
│   ├── critic.py            # Evaluation agent
│   ├── advocate.py          # Positive perspective agent
│   └── skeptic.py           # Critical perspective agent
├── coordinator.py           # Workflow orchestration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variable template
└── README.md               # This file
```

## 🔄 Next Steps (Phase 2-4)

- **Phase 2**: GA core implementation, MOEA multi-objective evaluation
- **Phase 3**: MAP-Elites diversity optimization, tournament debates
- **Phase 4**: Conceptual Moves plugin system, open API ecosystem

## 📝 Notes

- The current implementation includes dummy scoring in the CriticAgent for demonstration
- Actual LLM responses will require proper Google Cloud API configuration
- Consider implementing async/parallel agent calls for improved performance

## 🤝 Contributing

Please ensure all agents follow the established patterns and maintain consistency with the multi-agent architecture.