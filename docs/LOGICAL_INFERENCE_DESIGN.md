# Logical Inference Feature Design

## Overview

The MadSpark system currently has a `--logical` flag that enables "logical inference", but the implementation is overly simplistic, using hardcoded templates like "Therefore, the consequent follows". This document outlines a practical approach to transform this into a genuinely useful feature using LLM-based logical analysis.

## Current Problems

### Hardcoded Templates
```python
# From enhanced_reasoning.py:341
def _modus_ponens(self, premise1: str, premise2: str) -> InferenceStep:
    return InferenceStep(
        premise=f"{premise1}; {premise2}",
        conclusion="Therefore, the consequent follows",  # Not real inference!
        confidence=0.8,
        reasoning="Modus ponens: If P then Q, P, therefore Q"
    )
```

This provides no actual value to users and may be misleading.

## Proposed Solution: LLM-Based Logical Inference

Instead of building a complex formal logic system, we leverage the LLM's existing reasoning capabilities through structured prompts.

### Key Benefits

1. **Lightweight Implementation** - No complex infrastructure needed
2. **Natural Language Output** - More readable than formal logic notation
3. **Flexible Reasoning** - Can handle various types of inference
4. **Quick to Implement** - Estimated 3-4 hours
5. **Cost Effective** - Only adds 1-2 API calls per idea

## How It Would Enhance User Experience

### 1. Deeper Reasoning Chains
Transform vague connections into clear logical progressions:
- **Current**: "Theme: renewable energy → generic idea"
- **Enhanced**: "Urban density → limited space → vertical solutions → building-integrated wind turbines"

### 2. Context-Aware Deductions
Make intelligent connections between constraints:
```
Input: "AI education tools" + "limited internet"
Inference: Limited internet → offline capability → edge computing → 
           downloadable AI models with local processing
```

### 3. Constraint Resolution
Find creative solutions to conflicting requirements:
```
Input: "High performance" + "Low power consumption"
Inference: Typical conflict → but neuromorphic chips exist → 
           also quantum annealing for specific tasks → 
           suggest hybrid architectures
```

### 4. Causal Understanding
Identify cause-effect relationships:
```
Idea: "Remote work technology"
Inference: Remote work → less commuting → lower emissions → 
           suburban migration → changed retail patterns → 
           opportunities in VR offices
```

### 5. Contradiction Detection
Identify logical conflicts before they become problems:
```
Idea: "Anonymous social network for teenagers"
Inference: Anonymity ↔ safety requirements → 
           need trusted oversight → 
           pseudo-anonymous with guardian controls
```

## Implementation Design

### Core Components

#### 1. LogicalInferenceEngine Class
```python
class LogicalInferenceEngine:
    """LLM-based logical inference for MadSpark."""
    
    def __init__(self, genai_client):
        self.genai_client = genai_client
        self.inference_types = [
            'causal',      # Cause-effect chains
            'constraints', # Constraint satisfaction
            'contradiction', # Conflict detection
            'implications', # Future consequences
            'analogical'   # Similar domain insights
        ]
```

#### 2. Main Analysis Method
```python
def analyze(self, idea: str, theme: str, context: str, 
            analysis_type: str = 'full') -> InferenceResult:
    """
    Perform logical analysis on an idea.
    
    Args:
        idea: The generated idea to analyze
        theme: Original theme/topic
        context: Constraints and requirements
        analysis_type: 'full' or specific type
        
    Returns:
        InferenceResult with reasoning chain, confidence, and suggestions
    """
```

### Prompt Templates

#### Full Analysis Prompt
```python
FULL_ANALYSIS_PROMPT = """Perform comprehensive logical analysis:

Theme: {theme}
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

Format as:
INFERENCE_CHAIN:
- [Step 1]: [Reasoning]
- [Step 2]: [Reasoning]
...
CONCLUSION: [Summary]
CONFIDENCE: [0.0-1.0]
IMPROVEMENTS: [Suggestions]
"""
```

#### Specialized Prompts

**Causal Analysis**:
```python
CAUSAL_PROMPT = """Trace the causal relationships:
1. Root causes making this necessary
2. Direct effects of implementation
3. Second-order consequences
4. Feedback loops
"""
```

**Constraint Checking**:
```python
CONSTRAINT_PROMPT = """Verify constraint satisfaction:
For each requirement in '{context}':
- How is it addressed?
- Degree of satisfaction (0-100%)
- Any compromises made?
"""
```

**Contradiction Detection**:
```python
CONTRADICTION_PROMPT = """Identify logical conflicts:
1. Internal contradictions
2. Constraint violations  
3. Practical impossibilities
4. Suggested resolutions
"""
```

### Integration Points

#### 1. CLI Enhancement
```python
# In cli.py
if args.logical_inference:
    # Generate idea first
    idea = generator.generate(theme, context)
    
    # Apply logical analysis
    inference = logical_engine.analyze(idea, theme, context)
    
    # Display both idea and reasoning
    display_with_inference(idea, inference)
```

#### 2. Coordinator Integration
```python
# In coordinator.py
class Coordinator:
    def __init__(self, ...):
        self.logical_inference = LogicalInferenceEngine(genai_client)
    
    def evaluate_ideas(self, ideas, theme, context):
        for idea in ideas:
            if self.enable_logical_inference:
                idea.logical_analysis = self.logical_inference.analyze(
                    idea.text, theme, context
                )
```

#### 3. Web API Support
```python
# In web_api/main.py
@app.post("/generate-ideas")
async def generate_ideas(request: IdeaRequest):
    if request.enable_logical_inference:
        # Include logical analysis in response
```

### Output Format

#### Example Enhanced Output
```
🎯 Generated Idea:
"Develop an RPG where mathematical operations are disguised as spell 
combinations, with adaptive difficulty maintaining 80% success rate"

🧠 Logical Analysis:

INFERENCE CHAIN:
- [Problem]: Math anxiety stems from fear of judgment
- [Insight]: Games provide safe, low-stakes practice
- [Solution]: Disguise math as game mechanics
- [Mechanism]: Adaptive difficulty prevents frustration
- [Result]: Confidence builds through success

CONCLUSION: Addresses root cause (anxiety) while achieving goal (learning)
CONFIDENCE: 0.85
IMPROVEMENTS: Add peer support without competition
```

### Display Options

1. **Brief Mode**: Show only conclusion
2. **Standard Mode**: Show inference chain + conclusion  
3. **Detailed Mode**: Full analysis with all reasoning steps

## Implementation Plan

### Phase 1: Core Engine (1 hour)
- Create `LogicalInferenceEngine` class
- Implement basic `analyze()` method
- Add prompt templates

### Phase 2: Integration (2 hours)
- Update CLI to use inference engine
- Modify display functions
- Add to coordinator workflow

### Phase 3: Testing & Refinement (1 hour)
- Test with various themes/contexts
- Refine prompts based on output quality
- Add error handling

## Success Metrics

1. **Output Quality**: Logical analysis adds genuine insight
2. **Performance**: Adds <2 seconds to generation time
3. **User Value**: Users find reasoning helpful for understanding ideas
4. **API Efficiency**: Uses single LLM call for full analysis

## Future Enhancements

1. **Caching**: Store inference results for similar themes
2. **Learning**: Track which inference types are most valuable
3. **Customization**: Let users choose inference focus areas
4. **Visualization**: Graphical representation of reasoning chains

## Conclusion

This LLM-based approach transforms the currently useless `--logical` flag into a powerful feature that provides genuine logical analysis. It's practical to implement, adds real value, and enhances the overall intelligence of the MadSpark system without requiring complex infrastructure.