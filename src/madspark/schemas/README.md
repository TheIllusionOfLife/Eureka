# MadSpark Pydantic Schema Models

## Overview

This package contains type-safe Pydantic models that define the structured output schemas for all MadSpark agents. These models replace the legacy dict-based `response_schemas.py` definitions and provide a provider-agnostic foundation for future multi-LLM support.

## Architecture

### Package Structure
```
schemas/
├── __init__.py               # Public API exports
├── base.py                  # Base model classes (TitledItem, ConfidenceRated, Scored, ScoredEvaluation)
├── evaluation.py            # Evaluation agent models (EvaluatorResponse, CriticEvaluations)
├── generation.py            # Idea generation models (IdeaItem, GeneratedIdeas, ImprovementResponse)
├── advocacy.py              # Advocate agent models (AdvocacyResponse, StrengthItem, OpportunityItem)
├── skepticism.py            # Skeptic agent models (SkepticismResponse, CriticalFlaw, RiskChallenge)
├── logical_inference.py     # Logical inference models (InferenceResult, CausalAnalysis, etc.)
├── adapters.py              # GenAI conversion utilities (pydantic_to_genai_schema)
└── README.md                # This file
```

### Base Models

Three base classes provide common patterns across all agent schemas:

#### 1. **TitledItem**
For title+description items used in Advocate/Skeptic agents.

```python
from madspark.schemas.base import TitledItem

item = TitledItem(
    title="Innovation Potential",
    description="Leverages emerging AI capabilities for market advantage"
)
```

**Constraints:**
- `title`: 1-200 characters
- `description`: 1-2000 characters

#### 2. **ConfidenceRated**
For analysis with confidence scores (0.0-1.0), used in logical inference.

```python
from madspark.schemas.base import ConfidenceRated

analysis = ConfidenceRated(confidence=0.85)
# Automatically rounds to 2 decimal places: 0.85
```

**Constraints:**
- `confidence`: 0.0 to 1.0 (enforced by Gemini API)
- Automatically rounds to 2 decimal places

#### 3. **ScoredEvaluation**
For numeric evaluations (0-10 scale) from Critic/Evaluator agents.

```python
from madspark.schemas.base import ScoredEvaluation

eval_obj = ScoredEvaluation(
    score=8.5,
    critique="Strong concept with clear market fit and viable execution path"
)
# Score automatically rounds to 1 decimal place: 8.5
```

**Constraints:**
- `score`: 0.0 to 10.0 (enforced by Gemini API)
- `critique`: 10-5000 characters
- Score automatically rounds to 1 decimal place

## Evaluation Models

### EvaluatorResponse
Extends `ScoredEvaluation` with optional strengths/weaknesses arrays.

```python
from madspark.schemas.evaluation import EvaluatorResponse

eval_obj = EvaluatorResponse(
    score=7.5,
    critique="Solid concept with room for improvement",
    strengths=["Clear value proposition", "Large addressable market"],
    weaknesses=["High competition", "Complex implementation"]
)
```

**Replaces:** `EVALUATOR_SCHEMA` from `response_schemas.py`

### DimensionScore
Single dimension score for multi-dimensional evaluations.

```python
from madspark.schemas.evaluation import DimensionScore

dim = DimensionScore(
    score=8.5,
    reasoning="High feasibility due to existing infrastructure and proven tech stack"
)
```

**Replaces:** `DIMENSION_SCORE_SCHEMA` from `response_schemas.py`

### CriticEvaluation / CriticEvaluations
Array wrapper for multiple critic evaluations.

```python
from madspark.schemas.evaluation import CriticEvaluation, CriticEvaluations

# Single evaluation
eval_item = CriticEvaluation(
    score=6.5,
    comment="Interesting concept but execution challenges remain significant",
    strengths=["Innovative approach"],
    weaknesses=["High risk factor"]
)

# Multiple evaluations (array)
evals = CriticEvaluations([
    CriticEvaluation(score=8, comment="Great innovative idea with clear value"),
    CriticEvaluation(score=6, comment="Needs significant refinement and validation")
])

# List-like behavior
print(len(evals))  # 2
print(evals[0].score)  # 8.0
```

**Replaces:** `CRITIC_SCHEMA` from `response_schemas.py`

## Adapter Pattern

The `adapters.py` module converts between Pydantic and provider-specific formats, enabling future multi-provider support.

### pydantic_to_genai_schema()
Converts Pydantic model to Google GenAI dict format.

```python
from madspark.schemas.evaluation import EvaluatorResponse
from madspark.schemas.adapters import pydantic_to_genai_schema

# Convert Pydantic model to GenAI schema
schema = pydantic_to_genai_schema(EvaluatorResponse)

# Use with Google GenAI API
from google.genai import types

config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=schema,  # GenAI dict format
    system_instruction="..."
)
```

**Features:**
- Preserves `minimum`/`maximum` constraints (new Gemini API feature)
- Resolves `$ref` references from Pydantic `RootModel`
- Handles nested objects and arrays recursively
- Converts nullable fields appropriately

### genai_response_to_pydantic()
Parses GenAI JSON response into validated Pydantic model.

```python
from madspark.schemas.evaluation import EvaluatorResponse
from madspark.schemas.adapters import genai_response_to_pydantic

response_text = '{"score": 8.5, "critique": "Good idea with strong potential"}'

# Parse and validate
result = genai_response_to_pydantic(response_text, EvaluatorResponse)

# Type-safe access
print(result.score)  # 8.5 (float)
print(result.critique)  # "Good idea..." (str)
```

**Benefits:**
- Automatic validation with clear error messages
- Raises `ValidationError` if response doesn't match schema
- Raises `JSONDecodeError` if response isn't valid JSON

## Usage with GenAI API

### Complete Example: Critic Agent

```python
from google import genai
from google.genai import types

from madspark.schemas.evaluation import CriticEvaluations
from madspark.schemas.adapters import pydantic_to_genai_schema, genai_response_to_pydantic

# 1. Convert Pydantic model to GenAI schema
critic_schema = pydantic_to_genai_schema(CriticEvaluations)

# 2. Create API config with schema
config = types.GenerateContentConfig(
    temperature=0.7,
    response_mime_type="application/json",
    response_schema=critic_schema,
    system_instruction="Evaluate ideas critically..."
)

# 3. Make API call
client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Evaluate these ideas: ...",
    config=config
)

# 4. Parse and validate response
evaluations = genai_response_to_pydantic(response.text, CriticEvaluations)

# 5. Type-safe iteration
for eval_item in evaluations:
    print(f"Score: {eval_item.score}")  # IDE autocomplete works!
    print(f"Comment: {eval_item.comment}")

# 6. Convert to dict for backward compatibility
dict_list = [item.model_dump() for item in evaluations]
```

## Field Constraints & Validation

All numeric fields leverage the new Gemini API features for constraint enforcement:

### Numeric Constraints
- **minimum/maximum**: Enforced at API generation time (not just validation)
- **ge/le**: Pydantic validators ensure runtime safety

### String Constraints
- **minLength/maxLength**: String length validation
- **min_length/max_length**: Pydantic field validators

### Required vs Optional
- **required**: Mandatory fields raise `ValidationError` if missing
- **Optional[T]**: Optional fields via type hints

### Examples

```python
from madspark.schemas.evaluation import DimensionScore
from pydantic import ValidationError

# Valid
dim = DimensionScore(score=8.5)  # ✓

# Invalid: score exceeds maximum
try:
    dim = DimensionScore(score=11.0)
except ValidationError as e:
    print(e)  # Clear error message: score must be <= 10.0

# Invalid: score below minimum
try:
    dim = DimensionScore(score=-1.0)
except ValidationError as e:
    print(e)  # Clear error message: score must be >= 0.0
```

## Testing

All schemas have comprehensive test coverage across 5 test modules:

- **149 total test cases** covering:
  - **test_schemas_pydantic.py**: 60 tests for base models and evaluation schemas
  - **test_schemas_generation.py**: 30 tests for IdeaItem, GeneratedIdeas, ImprovementResponse
  - **test_schemas_advocacy.py**: 20 tests for AdvocacyResponse and components
  - **test_schemas_skepticism.py**: 21 tests for SkepticismResponse and components
  - **test_schemas_logical_inference.py**: 18 tests for InferenceResult and analysis types

Test coverage includes:
- Field validation and constraints
- Adapter conversion (Pydantic ↔ GenAI)
- JSON serialization and deserialization
- Backward compatibility via .model_dump()
- Edge cases (unicode, boundary values, nested structures)

Run tests:
```bash
# All schema tests
pytest tests/test_schemas*.py -v

# Individual modules
pytest tests/test_schemas_generation.py -v        # Idea generation
pytest tests/test_schemas_advocacy.py -v          # Advocate agent
pytest tests/test_schemas_skepticism.py -v        # Skeptic agent
pytest tests/test_schemas_logical_inference.py -v # Logical inference

# With coverage
pytest tests/test_schemas*.py --cov=src/madspark/schemas --cov-report=html
```

## Migration from Dict Schemas

### Old Pattern (dict schemas)
```python
from madspark.agents.response_schemas import EVALUATOR_SCHEMA
from google.genai import types

config = types.GenerateContentConfig(
    response_schema=EVALUATOR_SCHEMA  # dict
)

data = json.loads(response.text)  # manual parsing
score = data['score']  # no type checking, no IDE help
```

### New Pattern (Pydantic)
```python
from madspark.schemas.evaluation import EvaluatorResponse
from madspark.schemas.adapters import pydantic_to_genai_schema, genai_response_to_pydantic

config = types.GenerateContentConfig(
    response_schema=pydantic_to_genai_schema(EvaluatorResponse)
)

validated = genai_response_to_pydantic(response.text, EvaluatorResponse)
score = validated.score  # type-safe, IDE autocomplete works!
```

## Backward Compatibility

Pydantic models maintain full backward compatibility via `.model_dump()`:

```python
from madspark.schemas.evaluation import EvaluatorResponse

# Create Pydantic model
eval_obj = EvaluatorResponse(
    score=8.0,
    critique="Strong concept",
    strengths=["Innovative"]
)

# Convert to dict (old format)
eval_dict = eval_obj.model_dump()

# Legacy code works unchanged
print(eval_dict['score'])  # 8.0
print(eval_dict['critique'])  # "Strong concept"
```

## Migration Status

### ✅ Phase 1: Base & Evaluation Schemas (Completed)
- Base models (TitledItem, ConfidenceRated, Scored, ScoredEvaluation)
- Evaluation agent models (EvaluatorResponse, DimensionScore, CriticEvaluations)
- Critic agent migrated to Pydantic schemas

### ✅ Phase 2: Core Agent Schemas (Completed)
- **Idea generation**: IdeaItem, GeneratedIdeas, ImprovementResponse
- **Advocacy**: AdvocacyResponse, StrengthItem, OpportunityItem, ConcernResponse
- **Skepticism**: SkepticismResponse, CriticalFlaw, RiskChallenge, QuestionableAssumption, MissingConsideration
- **Logical inference**: InferenceResult, CausalAnalysis, ConstraintAnalysis, ContradictionAnalysis, ImplicationsAnalysis
- **Migrated agents**: Advocate, Skeptic, Idea Generator, Logical Inference Engine
- **Test coverage**: 149 comprehensive tests across all schemas

### 🚧 Phase 3: Integration & Cleanup (In Progress)
- Update coordinators for backward compatibility
- Integration testing with real API
- Documentation updates
- Performance benchmarking

### 📋 Phase 4: Provider Abstraction (Future)
Multi-LLM provider support via adapter pattern:
```
llm/
├── providers/
│   ├── google.py      # Google GenAI
│   ├── openai.py      # OpenAI GPT-4
│   ├── anthropic.py   # Claude
│   └── local.py       # Local LLMs
└── factory.py
```

### 📋 Phase 5: Full Migration (Future)
- Remove legacy `response_schemas.py` entirely
- Complete provider-agnostic infrastructure

## Contributing

When adding new schemas:

1. **Inherit from appropriate base model** (`TitledItem`, `ConfidenceRated`, `ScoredEvaluation`)
2. **Use `Field()` for all fields** with constraints
3. **Add docstrings with examples**
4. **Create comprehensive tests** in `tests/test_schemas_pydantic.py`
5. **Update this README** with usage examples

## Benefits Over Dict Schemas

✅ **Type Safety**: Catch errors at assignment time, not runtime
✅ **IDE Support**: Full autocomplete for all response fields
✅ **Better Testing**: Pydantic factory patterns simplify mocks
✅ **Automatic Validation**: No manual `validate_response_against_schema()`
✅ **Clear Error Messages**: Pydantic `ValidationError` shows exactly what's wrong
✅ **Self-Documenting**: Auto-generated docs from Pydantic models
✅ **Provider-Agnostic**: Works with any LLM via adapter pattern
✅ **New Gemini Features**: Leverage `minimum`/`maximum` API constraints

## See Also

- **Gemini API Documentation**: https://ai.google.dev/api/python/google/generativeai
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Project-level CLAUDE.md**: Pydantic usage patterns
