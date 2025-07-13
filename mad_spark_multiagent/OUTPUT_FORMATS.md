# MadSpark Output Formats Guide

## Available Output Formats

### 1. Summary Format (Default)
```bash
madspark "Your theme" "Your constraints" --output-format summary
```
- Shows original ideas with scores
- Includes advocacy and skepticism summaries
- Shows score improvements but NOT the improved idea text
- Best for: Quick overview of results

### 2. Text Format (Detailed)
```bash
madspark "Your theme" "Your constraints" --output-format text
```
- Shows complete workflow details
- Includes original AND improved ideas
- Full agent responses (advocacy, skepticism)
- Multi-dimensional evaluation details
- Best for: Understanding the full analysis

### 3. JSON Format (Structured)
```bash
madspark "Your theme" "Your constraints" --output-format json
```
- Machine-readable format
- Contains all data including improved ideas
- Structured multi-dimensional scores
- Best for: Integration with other tools

## Example Commands

### See Full Details with Improved Ideas
```bash
# Text format shows everything
madspark "How to draw better" "Within a week" --output-format text --async --num-candidates 1

# Save to file for easier reading
madspark "How to draw better" "Within a week" --output-format text --output-file drawing_ideas.txt --async
```

### Export All Formats
```bash
# Export to multiple formats at once
madspark "How to draw better" "Within a week" --export all --async
# Creates files in exports/ directory
```

## Understanding Multi-Dimensional Scores

Each idea is evaluated on 7 dimensions (always active):
1. **Feasibility**: How practical/achievable (1-10)
2. **Innovation**: How creative/novel (1-10)
3. **Impact**: Potential effect/benefit (1-10)
4. **Cost-Effectiveness**: Value for resources (1-10)
5. **Scalability**: Growth potential (1-10)
6. **Risk Assessment**: Risk level (1-10, lower is better)
7. **Timeline**: Time efficiency (1-10)

## Interpreting Score Changes

- **Original Score**: Initial critic evaluation
- **Improved Score**: After feedback loop enhancement
- **Delta (Δ)**: Improvement amount
  - Positive Δ: Idea improved
  - Negative Δ: Overcorrection occurred
  - Zero Δ: No significant change

## Tips for Better Output

1. **Use --verbose** for detailed processing logs
2. **Use --output-file** to save long outputs
3. **Use --export markdown** for readable reports
4. **Reduce --num-candidates** for faster results
5. **Add --enhanced-reasoning** for deeper analysis