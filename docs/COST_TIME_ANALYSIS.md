# MadSpark Cost & Time Analysis

## Overview

This document provides detailed cost and time estimates for various MadSpark usage scenarios using **Gemini 2.5 Flash** model.

### Pricing (as of August 2025)
- **Input tokens**: $0.30 per 1M tokens (batch: $0.15)
- **Output tokens**: $2.50 per 1M tokens (batch: $1.25)
- **Average token usage**: ~1,298 tokens per idea
- **Batch API**: 50% cost reduction

## Usage Scenarios

### 1. Simple Query
```bash
ms "renewable energy ideas"
```

**Components**:
- IdeaGenerator: 1 idea
- Critic: Evaluation
- Improvement: Final refinement

**API Calls**: 3
- Generate idea (1x)
- Critique idea (1x)  
- Improve idea (1x)

**Token Usage** (estimated):
- Input: ~500 tokens per call × 3 = 1,500 tokens
- Output: ~800 tokens per call × 3 = 2,400 tokens

**Cost**:
- Input: 1,500 × $0.15/1M = $0.000225
- Output: 2,400 × $1.25/1M = $0.003000
- **Total: $0.0032**

**Time**: ~25-30 seconds

---

### 2. Query with Context
```bash
ms "renewable energy ideas" "budget-friendly for homes"
```

**Components**: Same as simple query
**API Calls**: 3

**Token Usage** (with context):
- Input: ~600 tokens × 3 = 1,800 tokens
- Output: ~900 tokens × 3 = 2,700 tokens

**Cost**:
- Input: 1,800 × $0.15/1M = $0.000270
- Output: 2,700 × $1.25/1M = $0.003375
- **Total: $0.0036**

**Time**: ~28-35 seconds

---

### 3. Multiple Ideas (5)
```bash
ms "game concepts" --top-ideas 5
```

**Components**:
- IdeaGenerator: 5 ideas (1 batch call)
- Critic: 5 evaluations (1 batch call)
- Improvement: 5 refinements (1 batch call)

**API Calls**: 3 (batch optimized!)

**Token Usage**:
- Input: ~800 tokens × 3 = 2,400 tokens
- Output: ~4,000 tokens × 3 = 12,000 tokens

**Cost**:
- Input: 2,400 × $0.15/1M = $0.000360
- Output: 12,000 × $1.25/1M = $0.015000
- **Total: $0.0154**

**Time**: ~40-50 seconds (async parallel)

---

### 4. Enhanced Reasoning
```bash
ms "sustainable agriculture" --enhanced
```

**Components**:
- IdeaGenerator: 1 idea
- Critic: Evaluation
- Advocate: Strengths analysis (NEW)
- Skeptic: Challenges analysis (NEW)
- Improvement: Final refinement

**API Calls**: 5

**Token Usage**:
- Input: ~600 tokens × 5 = 3,000 tokens
- Output: ~1,000 tokens × 5 = 5,000 tokens

**Cost**:
- Input: 3,000 × $0.15/1M = $0.000450
- Output: 5,000 × $1.25/1M = $0.006250
- **Total: $0.0067**

**Time**: ~45-55 seconds

---

### 5. Logical Inference
```bash
ms "urban farming solutions" --logical
```

**Components**:
- Standard workflow (3 calls)
- LogicalInferenceEngine: 1 additional call

**API Calls**: 4

**Token Usage**:
- Input: ~600 tokens × 4 = 2,400 tokens
- Output: ~1,200 tokens × 4 = 4,800 tokens

**Cost**:
- Input: 2,400 × $0.15/1M = $0.000360
- Output: 4,800 × $1.25/1M = $0.006000
- **Total: $0.0064**

**Time**: ~35-45 seconds

---

### 6. Complex Full Feature Query
```bash
ms "create a new game concept as a game director" "implementable within a month, solo" \
   --top-ideas 5 --enhanced --logical --detailed --remix --remix-ids bookmark_123,bookmark_456
```

**Components**:
- IdeaGenerator: 5 ideas + remix context
- Critic: 5 evaluations
- Multi-dimensional: 7 dimensions × 5 ideas (1 batch)
- Advocate: 5 analyses (1 batch)
- Skeptic: 5 analyses (1 batch)
- LogicalInference: 5 analyses (1 batch)
- Improvement: 5 refinements (1 batch)
- Re-evaluation: 5 ideas (1 batch)

**API Calls**: 8 (all batch optimized!)

**Token Usage** (with remix context):
- Input: ~1,500 tokens × 8 = 12,000 tokens
- Output: ~5,000 tokens × 8 = 40,000 tokens

**Cost**:
- Input: 12,000 × $0.15/1M = $0.001800
- Output: 40,000 × $1.25/1M = $0.050000
- **Total: $0.0518**

**Time**: ~9-10 minutes (real-world testing)

---

## Cost Comparison Table

| Scenario | API Calls | Input Tokens | Output Tokens | Cost | Time |
|----------|-----------|--------------|---------------|------|------|
| Simple Query | 3 | 1,500 | 2,400 | $0.0032 | ~30s |
| With Context | 3 | 1,800 | 2,700 | $0.0036 | ~35s |
| 5 Ideas | 3 | 2,400 | 12,000 | $0.0154 | ~45s |
| Enhanced | 5 | 3,000 | 5,000 | $0.0067 | ~50s |
| Logical | 4 | 2,400 | 4,800 | $0.0064 | ~40s |
| Full Complex | 8 | 12,000 | 40,000 | $0.0518 | ~9-10m |

## Cost Optimization Tips

1. **Use Batch Processing**: Already implemented! Saves 50% on costs
2. **Enable Caching**: Redis caching for repeated queries
3. **Optimize Idea Count**: Each additional idea adds ~$0.003
4. **Select Features Wisely**: 
   - Enhanced adds ~$0.003
   - Logical adds ~$0.003
   - Both together add ~$0.006

## Performance Insights

### Batch API Benefits
- **Before**: 5 ideas = 15 API calls (individual processing)
- **After PR #154**: 5 ideas = 3 API calls in batch coordinator (80% reduction!)
- **After Async Optimization**: 5 ideas = 3-8 API calls in async coordinator (batch operations)
- **Cost Savings**: 45-50% with batch pricing

### Async Processing
- Parallel execution reduces time by ~40% for simple queries
- Multiple ideas processed simultaneously
- Enhanced features run concurrently

### Important Note on Complex Query Timing
- **Real-world testing shows complex queries take 9-10 minutes**, not the initially estimated 75 seconds
- This is due to:
  - Sequential API calls that cannot be parallelized (8+ calls)
  - Network latency compounding with each call
  - Token generation time for detailed responses (40,000+ output tokens)
  - Rate limiting between API calls
- Simple queries (1-3 ideas) remain fast (30-50 seconds)
- **Update**: With async coordinator batch optimizations, expected 60-70% reduction in execution time for multi-idea workflows

### Token Efficiency
- Average ~1,298 tokens per complete idea workflow
- Remix adds ~200-500 tokens depending on bookmark content
- Detailed output adds ~30% more tokens

## Monthly Usage Estimates

Assuming daily usage:

| Usage Pattern | Daily Runs | Monthly Cost | Ideas/Month |
|--------------|------------|--------------|-------------|
| Light (simple) | 10 | $0.96 | 300 |
| Regular (3 ideas) | 10 | $2.77 | 900 |
| Power (5 ideas + features) | 10 | $15.54 | 1,500 |
| Heavy (complex) | 20 | $31.08 | 3,000 |

## Recommendations

1. **For Experimentation**: Use simple queries ($0.003 each, ~30s)
2. **For Brainstorming**: Use 3-5 ideas without extras ($0.01-0.02, ~45s)
3. **For Deep Analysis**: Add --enhanced --logical ($0.02-0.03, ~50s)
4. **For Complex Projects**: Full features take 9-10 minutes - plan accordingly
5. **For Production**: Enable Redis caching to reduce repeated costs
6. **Time-Sensitive Work**: Set appropriate timeouts (--timeout 600 for complex queries)

## Notes

- Costs are based on Gemini 2.5 Flash batch API pricing
- Times assume average network latency
- Token usage varies with prompt complexity
- Remix feature adds context proportional to bookmark content
- All multi-idea operations use batch API automatically