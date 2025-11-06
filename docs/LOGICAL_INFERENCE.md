# Logical Inference Feature

Comprehensive guide to MadSpark's LLM-powered logical inference system.

## Table of Contents
- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [Architecture](#architecture)
- [Usage](#usage)
- [Implementation Details](#implementation-details)
- [Testing](#testing)

---

## Overview

The MadSpark logical inference system uses LLM-based analysis to provide genuine analytical reasoning, replacing hardcoded templates with intelligent causal chains, constraint resolution, and contradiction detection.

### What It Replaces

**Before** (hardcoded templates):
```python
def _modus_ponens(self, premise1: str, premise2: str):
    return "Therefore, the consequent follows"  # Not real inference!
```

**After** (LLM-powered):
```
Urban density → limited space → vertical solutions →
building-integrated wind turbines → hybrid renewable systems
```

### Key Benefits

1. **Lightweight Implementation** - Leverages existing LLM capabilities
2. **Natural Language Output** - More readable than formal logic notation
3. **Flexible Reasoning** - Handles various types of inference
4. **Cost Effective** - Only 1-2 additional API calls per idea
5. **Practical Value** - Provides genuine analytical insights

---

## Key Capabilities

### 1. Causal Reasoning Chains
Transform vague connections into clear logical progressions:

**Input**: "AI education tools" + "limited internet"
**Inference**:
```
Limited internet → offline capability required →
edge computing → downloadable AI models →
local processing with periodic sync
```

### 2. Constraint Satisfaction
Find creative solutions to conflicting requirements:

**Input**: "High performance" + "Low power consumption"
**Inference**:
```
Typical conflict → neuromorphic chips exist →
quantum annealing for specific tasks →
suggest hybrid architecture (CPU + neuromorphic co-processor)
```

### 3. Contradiction Detection
Identify logical conflicts before they become problems:

**Input**: "Anonymous social network for teenagers"
**Inference**:
```
Anonymity ↔ safety requirements conflict →
need trusted oversight →
pseudo-anonymous with guardian controls + mandatory reporting
```

### 4. Implication Analysis
Identify second-order consequences:

**Input**: "Remote work technology"
**Inference**:
```
Remote work → less commuting → lower emissions →
suburban migration → changed retail patterns →
opportunities in VR offices and collaboration tools
```

### 5. Assumptions Detection
Uncover hidden assumptions:

**Input**: "Blockchain-based voting system"
**Inference**:
```
ASSUMPTIONS:
- Voters have reliable internet (false in rural areas)
- Technical literacy for key management (major barrier)
- Trust in cryptographic systems (not universal)
→ Needs hybrid paper + digital approach
```

---

## Architecture

### Core Components

#### 1. LogicalInferenceEngine (`src/madspark/utils/logical_inference_engine.py`)

**Main class** that uses Gemini API for logical analysis:
```python
class LogicalInferenceEngine:
    def __init__(self, genai_client):
        self.genai_client = genai_client

    def analyze(
        self,
        idea: str,
        topic: str,
        context: str,
        analysis_type: InferenceType = InferenceType.FULL
    ) -> InferenceResult:
        """Perform logical analysis on an idea."""
```

#### 2. InferenceType Enum
Five analysis types available:
- **FULL**: Comprehensive analysis (all types below)
- **CAUSAL**: Cause-effect chains only
- **CONSTRAINTS**: Constraint satisfaction analysis
- **CONTRADICTION**: Conflict detection
- **IMPLICATIONS**: Future consequences and second-order effects

#### 3. InferenceResult Dataclass
Structured output with type-specific fields:
```python
@dataclass
class InferenceResult:
    inference_chain: List[str]      # Step-by-step reasoning
    conclusion: str                  # Final logical conclusion
    confidence: float                # 0.0-1.0
    suggestions: List[str]           # Actionable improvements
    # Type-specific fields
    causal_chain: Optional[List[str]]
    constraint_percentage: Optional[float]
    implications: Optional[List[str]]
    contradictions: Optional[List[str]]
```

### Integration Points

#### Enhanced Reasoning System
- Uses LogicalInferenceEngine when GenAI client available
- Falls back to rule-based system for backward compatibility
- Integrated with `ReasoningEngine` for complete workflow

#### Async Coordinator
- Embeds logical inference results in critique text
- Respects confidence threshold (0.0 by default, configurable)
- Handles errors gracefully without breaking workflow

#### CLI
- `--logical` flag enables LLM-powered inference
- Works in both real API and mock modes
- Displays formatted inference in critiques

---

## Usage

### Basic Usage

```bash
# Enable logical inference
ms "urban farming" "limited space" --logical

# Combined with enhanced reasoning
ms "sustainable cities" "low cost" --enhanced --logical

# With async mode
ms "AI healthcare" "privacy concerns" --async --logical --num-candidates 3
```

### API Usage

```python
from madspark.utils.logical_inference_engine import (
    LogicalInferenceEngine,
    InferenceType
)
from madspark.agents.genai_client import get_genai_client

# Initialize client using the project's helper function
client = get_genai_client()
engine = LogicalInferenceEngine(client)

# Run analysis
result = engine.analyze(
    idea="Building-integrated wind turbines",
    topic="urban renewable energy",
    context="limited space, high population density",
    analysis_type=InferenceType.FULL
)

# Display results
formatted = engine.format_result(result, verbosity='standard')
print(formatted)
```

### Output Format

#### Brief Verbosity
```
LOGICAL ANALYSIS (Confidence: 0.85):
Conclusion: Vertical integration addresses space constraints
```

#### Standard Verbosity (Default)
```
LOGICAL INFERENCE:
→ Urban density limits ground space
→ Buildings have underutilized vertical surfaces
→ Modern turbines scale to small sizes
→ Building integration provides stable mounting
Conclusion: Vertical integration addresses space constraints
Confidence: 0.85
```

#### Detailed Verbosity
```
LOGICAL INFERENCE (FULL ANALYSIS):

Inference Chain:
→ Urban density limits ground space for traditional turbines
→ Buildings have underutilized vertical surfaces (walls, roofs)
→ Modern turbines scale effectively to smaller sizes
→ Building integration provides stable mounting points
→ Grid connectivity simplifies power distribution

Causal Chain:
- Root Cause: Limited horizontal space in cities
- Effect: Need for vertical renewable solutions
- Consequence: Building-integrated systems become viable

Constraint Satisfaction: 85%
- Space constraint: Fully addressed (vertical deployment)
- Population density: Compatible (quiet operation needed)

Implications:
- Architectural standards will need updates
- Maintenance access requirements increase
- Aesthetic considerations become crucial

Conclusion: Vertical integration of small turbines addresses
urban space constraints while maintaining power generation goals

Confidence: 0.85

Suggestions:
- Consider noise regulations for residential areas
- Design for modular installation and replacement
- Include aesthetic design guidelines
```

---

## Implementation Details

### Prompt Engineering

Each analysis type uses a carefully crafted prompt template:

#### Full Analysis Prompt
```python
"""Perform comprehensive logical analysis:

Theme: {topic}
Context: {context}
Idea: {idea}

Provide structured reasoning:

1. CAUSAL CHAIN
   - What problem does this solve?
   - What causes make this necessary?
   - What effects will it have?

2. CONSTRAINT SATISFACTION
   - How does each constraint get addressed?
   - Any conflicts or trade-offs?

3. HIDDEN ASSUMPTIONS
   - What must be true for this to work?
   - What are we taking for granted?

4. LOGICAL IMPLICATIONS
   - If successful, what follows?
   - Second-order consequences?

5. POTENTIAL CONTRADICTIONS
   - Internal conflicts?
   - Reality conflicts?

Format as markdown with clear sections."""
```

### Response Parsing

Robust parsing with multiple fallback strategies:

1. **Structured Parsing**: Extract specific sections (INFERENCE_CHAIN, CONCLUSION, etc.)
2. **Fallback to General**: If structure not found, extract meaningful content
3. **Minimal Fallback**: Return basic analysis with lowered confidence
4. **Error Handling**: Graceful degradation, never breaks workflow

### Display Formatting

Three verbosity levels for different contexts:

- **brief**: Just conclusion and confidence (CLI default for --logical)
- **standard**: Inference chain, conclusion, confidence, suggestions (Web UI)
- **detailed**: All available information including type-specific fields (API/debugging)

---

## Testing

### Test Coverage

#### Unit Tests (`tests/test_logical_inference.py`)
- 15 comprehensive tests covering all functionality
- Tests for each analysis type (FULL, CAUSAL, CONSTRAINTS, etc.)
- Error handling scenarios
- Display formatting verification
- Mock and real API modes

#### Integration Tests (`tests/test_enhanced_reasoning_integration.py`)
- 9 tests for integration with enhanced reasoning
- Verifies engine creation and usage
- Tests complete workflow integration
- Error handling in integrated context

#### CLI Tests (`tests/test_cli_logical_integration.py`)
- Tests `--logical` flag functionality
- Verifies output formatting
- Mock mode compatibility

### Running Tests

```bash
# All logical inference tests
PYTHONPATH=src pytest tests/ -k logical -v

# Specific test file
PYTHONPATH=src pytest tests/test_logical_inference.py -v

# Integration tests
PYTHONPATH=src pytest tests/test_enhanced_reasoning_integration.py -v
```

---

## Configuration

### Confidence Threshold

Control when logical inference results are included:

```python
# In constants.py
LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD = 0.0  # Include all results

# To filter low-confidence results:
LOGICAL_INFERENCE_CONFIDENCE_THRESHOLD = 0.5  # Only include ≥50% confidence
```

### Mock Mode

Logical inference works in mock mode with simulated responses:

```bash
export MADSPARK_MODE=mock
ms "test topic" --logical
```

---

## Best Practices

1. **Use for Complex Ideas**: Most valuable when constraints are nuanced
2. **Combine with Enhanced Reasoning**: `--enhanced --logical` provides comprehensive analysis
3. **Review Assumptions**: Pay attention to hidden assumptions detected
4. **Consider Trade-offs**: Logical inference highlights constraint conflicts
5. **Iterate**: Use suggestions to refine ideas

---

## Known Limitations

1. **LLM Dependency**: Requires Gemini API (or mock mode)
2. **Response Variability**: LLM outputs may vary between runs
3. **Parse Failures**: Rare cases where LLM doesn't follow format (fallback handles this)
4. **Cost**: Adds 1-2 API calls per idea (minimal but measurable)

---

## Future Enhancements

Potential improvements for future versions:

1. **Custom Analysis Types**: User-defined analysis templates
2. **Multi-Step Chains**: Deeper reasoning with iterative refinement
3. **Visualization**: Graphical representation of inference chains
4. **Comparative Analysis**: Compare logical implications across multiple ideas
5. **Historical Learning**: Learn from user feedback on inference quality

---

**Last Updated**: 2025-11-06
**Related**: See `guides/ENHANCED_REASONING_API.md` for integration details
