# Enhanced Reasoning System API Documentation

## Overview

The Enhanced Reasoning System (Phase 2.1) provides advanced reasoning capabilities for the MadSpark Multi-Agent System. This document provides comprehensive API documentation for developers who want to integrate or extend the enhanced reasoning functionality.

## Core Components API

### ReasoningEngine

The main coordinator class that orchestrates all reasoning capabilities.

#### Class: `ReasoningEngine`

```python
class ReasoningEngine:
    def __init__(self, config: Optional[ReasoningConfig] = None)
    def process_with_context(self, current_input: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]
    def generate_inference_chain(self, premises: List[str], conclusion: str) -> Dict[str, Any]
    def process_complete_workflow(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]
    def process_agent_request(self, request: Dict[str, Any]) -> Dict[str, Any]
    def calculate_consistency_score(self, results: List[Dict[str, Any]]) -> float
```

#### Methods

##### `__init__(config: Optional[ReasoningConfig] = None)`
Initialize the reasoning engine with optional configuration.

**Parameters:**
- `config` (Optional[ReasoningConfig]): Configuration dictionary with the following keys:
  - `memory_capacity` (int): Maximum number of contexts to store (default: 1000)
  - `inference_depth` (int): Maximum depth for logical inference (default: 3)
  - `context_weight` (float): Weight for context in decision making (default: 0.8)
  - `evaluation_dimensions` (Dict): Custom evaluation dimensions

**Example:**
```python
config = {
    'memory_capacity': 500,
    'inference_depth': 5,
    'context_weight': 0.9
}
engine = ReasoningEngine(config=config)
```

##### `process_with_context(current_input, conversation_history) -> Dict[str, Any]`
Process a current input with awareness of conversation history.

**Parameters:**
- `current_input` (Dict[str, Any]): Current agent input with keys:
  - `agent` (str): Agent type ('idea_generator', 'critic', 'advocate', 'skeptic')
  - `idea` (str): The idea being processed
  - `context` (str): Additional context information
- `conversation_history` (List[Dict[str, Any]]): Previous interactions

**Returns:**
- Dictionary containing:
  - `enhanced_reasoning` (Dict): Reasoning analysis results
  - `context_awareness_score` (float): Score from 0.0 to 1.0
  - `reasoning_quality_score` (float): Overall reasoning quality
  - `contextual_insights` (List[str]): Key insights from context analysis

**Example:**
```python
result = engine.process_with_context(
    current_input={
        "agent": "critic",
        "idea": "Smart healthcare diagnostics",
        "context": "Rural deployment challenges"
    },
    conversation_history=[
        {"agent": "idea_generator", "output": "AI-powered diagnostic tools"},
        {"agent": "advocate", "output": "High impact for underserved areas"}
    ]
)
```

##### `generate_inference_chain(premises, conclusion) -> Dict[str, Any]`
Generate a logical inference chain from premises to conclusion.

**Parameters:**
- `premises` (List[str]): List of premise statements
- `conclusion` (str): Target conclusion statement

**Returns:**
- Dictionary containing:
  - `logical_steps` (List[Dict]): Step-by-step logical reasoning
  - `confidence_score` (float): Confidence in the inference chain
  - `validity_assessment` (str): Assessment of logical validity

**Example:**
```python
chain = engine.generate_inference_chain(
    premises=[
        "AI reduces diagnostic errors",
        "Reduced errors improve patient outcomes",
        "Better outcomes save lives"
    ],
    conclusion="AI saves lives through improved diagnostics"
)
```

---

### ContextMemory

Manages storage and retrieval of conversation context with intelligent similarity matching.

#### Class: `ContextMemory`

```python
class ContextMemory:
    def __init__(self, capacity: int = 1000)
    def store_context(self, context_data: Dict[str, Any]) -> str
    def get_context(self, context_id: str) -> Optional[ContextData]
    def get_all_contexts(self) -> List[ContextData]
    def search_by_agent(self, agent_type: str) -> List[ContextData]
    def find_similar_contexts(self, query: str, threshold: float = 0.3) -> List[ContextData]
    def clear_contexts(self) -> None
```

#### Methods

##### `store_context(context_data: Dict[str, Any]) -> str`
Store context data and return unique context ID.

**Parameters:**
- `context_data` (Dict[str, Any]): Context information with keys:
  - `agent` (str): Agent that generated the context
  - `input` (str): Input data
  - `output` (str): Output data
  - `timestamp` (str, optional): ISO format timestamp
  - `metadata` (Dict, optional): Additional metadata

**Returns:**
- `str`: Unique context ID for later retrieval

**Example:**
```python
context_id = memory.store_context({
    "agent": "idea_generator",
    "input": "sustainable technology",
    "output": "Solar-powered water purification",
    "metadata": {"temperature": 0.8}
})
```

##### `find_similar_contexts(query: str, threshold: float = 0.3) -> List[ContextData]`
Find contexts similar to the query string using Jaccard similarity.

**Parameters:**
- `query` (str): Search query
- `threshold` (float): Similarity threshold (0.0 to 1.0, default: 0.3)

**Returns:**
- `List[ContextData]`: List of similar contexts sorted by similarity

**Example:**
```python
similar = memory.find_similar_contexts(
    "healthcare AI diagnosis", 
    threshold=0.4
)
```

---

### LogicalInference

Implements formal logical reasoning with multiple inference rules.

#### Class: `LogicalInference`

```python
class LogicalInference:
    def __init__(self)
    def build_inference_chain(self, premises: List[str]) -> Dict[str, Any]
    def analyze_consistency(self, premises: List[str]) -> Dict[str, Any]
    def calculate_confidence(self, premises: List[str]) -> Dict[str, Any]
    def apply_modus_ponens(self, premise1: str, premise2: str) -> Optional[str]
    def apply_modus_tollens(self, premise1: str, premise2: str) -> Optional[str]
```

#### Supported Inference Rules

1. **Modus Ponens**: If P then Q, P, therefore Q
2. **Modus Tollens**: If P then Q, not Q, therefore not P  
3. **Hypothetical Syllogism**: If P then Q, if Q then R, therefore if P then R
4. **Disjunctive Syllogism**: P or Q, not P, therefore Q

#### Methods

##### `build_inference_chain(premises: List[str]) -> Dict[str, Any]`
Build a logical inference chain from the given premises.

**Parameters:**
- `premises` (List[str]): List of premise statements

**Returns:**
- Dictionary containing:
  - `steps` (List[InferenceStep]): Individual reasoning steps
  - `conclusion` (str): Final conclusion
  - `validity_score` (float): Logical validity assessment
  - `confidence_score` (float): Confidence in the reasoning

**Example:**
```python
chain = inference.build_inference_chain([
    "If AI is implemented, then efficiency increases",
    "AI is implemented in healthcare",
    "If efficiency increases, then costs decrease"
])
```

##### `analyze_consistency(premises: List[str]) -> Dict[str, Any]`
Analyze premises for logical consistency and contradictions.

**Parameters:**
- `premises` (List[str]): List of statements to analyze

**Returns:**
- Dictionary containing:
  - `contradictions` (List[str]): Identified contradictions
  - `consistency_score` (float): Overall consistency score
  - `problematic_pairs` (List[tuple]): Pairs of contradictory statements

---

### MultiDimensionalEvaluator

Provides comprehensive evaluation across multiple dimensions with weighted scoring.

#### Class: `MultiDimensionalEvaluator`

```python
class MultiDimensionalEvaluator:
    def __init__(self, dimensions: Optional[Dict[str, Dict[str, Any]]] = None)
    def evaluate_idea(self, idea: str, context: Dict[str, Any]) -> Dict[str, Any]
    def compare_ideas(self, ideas: List[str], context: Dict[str, Any]) -> Dict[str, Any]
    def get_dimension_weights(self) -> Dict[str, float]
    def set_dimension_weights(self, weights: Dict[str, float]) -> None
```

#### Default Evaluation Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| `feasibility` | 0.20 | Technical and practical implementation possibility |
| `innovation` | 0.15 | Novelty and creative advancement potential |
| `impact` | 0.20 | Expected magnitude of positive outcomes |
| `cost_effectiveness` | 0.15 | Resource efficiency and ROI analysis |
| `scalability` | 0.10 | Growth and expansion potential |
| `risk_assessment` | 0.10 | Potential negative outcomes and mitigation |
| `timeline` | 0.10 | Implementation speed and milestone planning |

#### Methods

##### `evaluate_idea(idea: str, context: Dict[str, Any]) -> Dict[str, Any]`
Evaluate a single idea across all dimensions.

**Parameters:**
- `idea` (str): The idea to evaluate
- `context` (Dict[str, Any]): Evaluation context with keys like:
  - `budget` (str): Budget constraints
  - `timeline` (str): Time constraints
  - `target_audience` (str): Intended users
  - `regulatory_requirements` (str): Compliance needs

**Returns:**
- Dictionary containing:
  - `overall_score` (float): Weighted overall score (1-10)
  - `dimension_scores` (Dict[str, float]): Individual dimension scores
  - `weighted_score` (float): Final weighted score
  - `confidence_interval` (float): Statistical confidence measure

**Example:**
```python
evaluation = evaluator.evaluate_idea(
    "AI-powered telemedicine platform",
    context={
        'budget': 'medium',
        'timeline': '18 months',
        'target_audience': 'rural patients',
        'regulatory_requirements': 'HIPAA compliance required'
    }
)
```

##### `compare_ideas(ideas: List[str], context: Dict[str, Any]) -> Dict[str, Any]`
Compare multiple ideas and provide rankings.

**Parameters:**
- `ideas` (List[str]): List of ideas to compare
- `context` (Dict[str, Any]): Comparison context

**Returns:**
- Dictionary containing:
  - `rankings` (List[Dict]): Ideas ranked by score
  - `relative_scores` (Dict[str, float]): Relative scoring between ideas
  - `recommendation` (str): Top recommendation with justification

---

### AgentConversationTracker

Tracks and analyzes agent conversation patterns and workflow completeness.

#### Class: `AgentConversationTracker`

```python
class AgentConversationTracker:
    def __init__(self)
    def add_interaction(self, interaction: Dict[str, Any]) -> str
    def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]
    def analyze_conversation_flow(self) -> Dict[str, Any]
    def extract_relevant_context(self, query: str) -> List[Dict[str, Any]]
    def get_workflow_completeness(self) -> Dict[str, Any]
```

#### Methods

##### `add_interaction(interaction: Dict[str, Any]) -> str`
Add a new agent interaction to the conversation history.

**Parameters:**
- `interaction` (Dict[str, Any]): Interaction data with keys:
  - `agent` (str): Agent type
  - `input` (str): Input to the agent
  - `output` (str): Agent's output
  - `timestamp` (str, optional): When the interaction occurred
  - `metadata` (Dict, optional): Additional interaction metadata

**Returns:**
- `str`: Unique interaction ID

##### `analyze_conversation_flow() -> Dict[str, Any]`
Analyze the flow and patterns in the conversation.

**Returns:**
- Dictionary containing:
  - `agent_sequence` (List[str]): Sequence of agent interactions
  - `interaction_count` (int): Total number of interactions
  - `workflow_completeness` (float): Completeness score (0.0-1.0)
  - `pattern_analysis` (Dict): Detected conversation patterns
  - `optimization_suggestions` (List[str]): Suggestions for improvement

##### `extract_relevant_context(query: str) -> List[Dict[str, Any]]`
Extract interactions relevant to a specific query.

**Parameters:**
- `query` (str): Search query for relevant context

**Returns:**
- `List[Dict[str, Any]]`: List of relevant interactions sorted by relevance

---

## Data Structures

### TypedDict Definitions

```python
class ReasoningConfig(TypedDict):
    memory_capacity: int
    inference_depth: int
    context_weight: float
    evaluation_dimensions: Dict[str, Dict[str, Any]]

@dataclass
class ContextData:
    agent: str
    timestamp: str
    input_data: str
    output_data: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default="")

@dataclass
class InferenceStep:
    premise: str
    conclusion: str
    confidence: float
    reasoning: str

@dataclass  
class LogicalChain:
    steps: List[InferenceStep]
    overall_conclusion: str
    confidence_score: float
    validity_score: float
```

## Error Handling

### Exception Types

The enhanced reasoning system uses standard Python exceptions with descriptive messages:

- `ValueError`: Invalid input parameters or configuration
- `KeyError`: Missing required dictionary keys
- `TypeError`: Incorrect data types
- `RuntimeError`: Runtime errors during reasoning operations

### Error Recovery

All components implement graceful error handling:

```python
try:
    result = engine.process_with_context(input_data, history)
except ValueError as e:
    logging.warning(f"Invalid input: {e}")
    # Fallback to basic processing
    result = basic_process(input_data)
```

## Performance Considerations

### Optimization Guidelines

1. **Context Memory**: 
   - Optimal capacity: 500-1000 contexts for typical use cases
   - Consider clearing old contexts for long-running sessions

2. **Similarity Search**:
   - Lower thresholds (0.1-0.3) for broader matches
   - Higher thresholds (0.5-0.8) for precise matches

3. **Inference Depth**:
   - Depth 2-3 for most applications
   - Depth 5+ only for complex logical scenarios

4. **Batch Processing**:
   - Process multiple ideas in batches for better performance
   - Use async patterns for concurrent evaluation

### Memory Usage

Approximate memory usage per component:
- ContextMemory: ~50 bytes per stored context
- LogicalInference: ~10KB for typical rule sets
- MultiDimensionalEvaluator: ~5KB for default dimensions
- AgentConversationTracker: ~100 bytes per interaction

## Integration Examples

### Basic Integration

```python
from enhanced_reasoning import ReasoningEngine

# Initialize with default configuration
engine = ReasoningEngine()

# Process with conversation context
result = engine.process_with_context(
    current_input={"agent": "critic", "idea": "Smart city sensors"},
    conversation_history=previous_interactions
)

# Get reasoning insights
context_score = result['context_awareness_score']
reasoning_quality = result['reasoning_quality_score']
insights = result.get('contextual_insights', [])
```

### Advanced Integration

```python
from enhanced_reasoning import (
    ReasoningEngine, ContextMemory, MultiDimensionalEvaluator
)

# Custom configuration
config = {
    'memory_capacity': 2000,
    'inference_depth': 4,
    'context_weight': 0.85,
    'evaluation_dimensions': {
        'technical_feasibility': {'weight': 0.3},
        'market_viability': {'weight': 0.4},
        'social_impact': {'weight': 0.3}
    }
}

# Initialize components
engine = ReasoningEngine(config=config)
evaluator = MultiDimensionalEvaluator(dimensions=config['evaluation_dimensions'])

# Process workflow with enhanced reasoning
workflow_data = {
    'theme': 'sustainable transportation',
    'constraints': 'urban environment, budget-conscious',
    'previous_interactions': conversation_history
}

enhanced_result = engine.process_complete_workflow(workflow_data)
detailed_evaluation = evaluator.evaluate_idea(
    enhanced_result['top_idea'], 
    enhanced_result['context']
)
```

## Testing and Validation

### Unit Testing

The system includes comprehensive unit tests for all components:

```bash
# Run all enhanced reasoning tests
pytest tests/test_enhanced_reasoning.py -v

# Run specific component tests
pytest tests/test_enhanced_reasoning.py::TestContextMemory -v

# Run with coverage reporting
pytest tests/test_enhanced_reasoning.py --cov=enhanced_reasoning
```

### Integration Testing

Integration tests validate component interactions:

```python
def test_full_reasoning_workflow():
    engine = ReasoningEngine()
    result = engine.process_complete_workflow(test_data)
    
    assert 'enhanced_reasoning' in result
    assert result['reasoning_quality_score'] >= 0.0
    assert result['reasoning_quality_score'] <= 1.0
```

## Debugging and Troubleshooting

### Logging

Enable debug logging for detailed reasoning traces:

```python
import logging
logging.getLogger('enhanced_reasoning').setLevel(logging.DEBUG)

# Detailed reasoning steps will be logged
result = engine.process_with_context(input_data, history)
```

### Common Issues

1. **Low Context Awareness Scores**:
   - Ensure conversation history is properly formatted
   - Check that context data includes relevant keywords

2. **Poor Inference Chain Quality**:
   - Verify premises are logically connected
   - Use clear, unambiguous statement formats

3. **Inconsistent Evaluation Scores**:
   - Check dimension weights sum to 1.0
   - Ensure context data provides sufficient information

---

This API documentation provides comprehensive guidance for integrating and extending the Enhanced Reasoning System. For additional examples and advanced usage patterns, refer to the test suite in `tests/test_enhanced_reasoning.py`.