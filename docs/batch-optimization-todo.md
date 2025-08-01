# MadSpark API Optimization Todo

## API Call Batching Implementation Plan

### Current State Analysis
- **Per workflow with 1 candidate**: 18 API calls
- **Per workflow with 5 candidates**: 82 API calls
- **Issue**: Sequential multi-dimensional evaluation (7 calls per idea per evaluation)

### Target State
- **All workflows**: 7 API calls regardless of candidate count
- **91% reduction in API calls for 5 candidates**

### Implementation Sequences

#### Sequence 1: Idea Generation (1 call)
- No changes needed

#### Sequence 2: Critic Evaluation (1 call)
- Already batched ✓

#### Sequence 3: Advocate + Skeptic (2 calls)
- **Advocate**: Batch all N ideas with their critiques (1 call)
- **Skeptic**: Batch all N ideas with advocacies (1 call)
- Note: Skeptic depends on Advocate output

#### Sequence 4: Improvement (1 call)
- Batch all N improvements with full context

#### Sequence 5: Re-evaluation (2 calls)
- **Critic Re-eval**: Batch all N improved ideas (1 call)
- **Multi-dimensional**: Batch all dimensions × N ideas (1 call)

### Implementation Details

#### 1. New Batch Functions

**agents/advocate.py**
```python
def advocate_ideas_batch(
    ideas_with_evaluations: List[Dict[str, str]], 
    context: str, 
    temperature: float = 0.5
) -> List[Dict[str, Any]]:
    """Batch advocate for multiple ideas with structured output."""
```

**agents/skeptic.py**
```python
def criticize_ideas_batch(
    ideas_with_advocacies: List[Dict[str, str]], 
    context: str, 
    temperature: float = 0.5
) -> List[Dict[str, Any]]:
    """Batch skeptic analysis for multiple ideas."""
```

**agents/idea_generator.py**
```python
def improve_ideas_batch(
    ideas_with_feedback: List[Dict[str, str]], 
    theme: str, 
    temperature: float = 0.9
) -> List[Dict[str, Any]]:
    """Batch improvement for multiple ideas."""
```

**core/enhanced_reasoning.py**
```python
def evaluate_ideas_all_dimensions_batch(
    self, 
    ideas: List[str], 
    context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Evaluate multiple ideas across all 7 dimensions in one call."""
```

#### 2. Structured Output Schemas

```python
BATCH_ADVOCACY_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "idea_index": {"type": "INTEGER"},
            "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
            "opportunities": {"type": "ARRAY", "items": {"type": "STRING"}},
            "addressing_concerns": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["idea_index", "strengths", "opportunities", "addressing_concerns"]
    }
}

MULTI_DIMENSIONAL_BATCH_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "idea_index": {"type": "INTEGER"},
            "feasibility": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "innovation": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "impact": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "cost_effectiveness": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "scalability": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "risk_assessment": {"type": "NUMBER", "minimum": 1, "maximum": 10},
            "timeline": {"type": "NUMBER", "minimum": 1, "maximum": 10}
        },
        "required": ["idea_index", "feasibility", "innovation", "impact", 
                    "cost_effectiveness", "scalability", "risk_assessment", "timeline"]
    }
}
```

#### 3. Coordinator Updates

Both `coordinator.py` and `async_coordinator.py` need updates to:
1. Collect all candidates before processing
2. Call batch functions instead of loops
3. Parse batch responses appropriately

#### 4. Monitoring & Error Handling

```python
class BatchMonitor:
    """Monitor batch API performance."""
    
    def track_batch_call(self, batch_type: str, item_count: int, 
                        tokens: int, duration: float, cost: float):
        """Track metrics for analysis."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "batch_type": batch_type,
            "items": item_count,
            "tokens": tokens,
            "duration_seconds": duration,
            "estimated_cost": cost,
            "tokens_per_item": tokens / item_count,
            "items_per_second": item_count / duration
        }
```

### Implementation Priority

1. **Phase 1**: Multi-dimensional batch evaluation
   - Biggest impact: reduces 14N calls to 1 call
   - File: `core/enhanced_reasoning.py`

2. **Phase 2**: Advocate + Skeptic batching
   - Reduces 2N calls to 2 calls
   - Files: `agents/advocate.py`, `agents/skeptic.py`

3. **Phase 3**: Improvement batching
   - Reduces N calls to 1 call
   - File: `agents/idea_generator.py`

4. **Phase 4**: Coordinator integration
   - Files: `core/coordinator.py`, `core/async_coordinator.py`

### Key Considerations

1. **No feature flags**: Always use batch processing (more efficient)
2. **Token monitoring**: Critical since batch calls use more tokens per call
3. **Error handling**: Implement fallback to sequential if batch fails
4. **Response validation**: Ensure all items in batch are processed
5. **Testing**: Validate with 1, 2, and 5 candidate scenarios

### Expected Benefits

- **Cost reduction**: 91% fewer API calls
- **Speed improvement**: Reduced latency from fewer round trips
- **Consistency**: All items evaluated in same context
- **Simplified code**: Less looping, cleaner structure

### Next Steps

1. Start with Phase 1 (multi-dimensional batching)
2. Add comprehensive logging and monitoring
3. Test thoroughly with different candidate counts
4. Roll out remaining phases based on Phase 1 success