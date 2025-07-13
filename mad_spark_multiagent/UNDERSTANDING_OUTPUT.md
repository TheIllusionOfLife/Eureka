# Understanding MadSpark Output

## Quick Summary

The MadSpark system generates:
1. **Original Ideas** - Initial creative ideas
2. **Multi-Dimensional Evaluation** - 7 aspects scored 1-10
3. **Agent Feedback** - Advocacy (strengths) & Skepticism (weaknesses)
4. **Improved Ideas** - Enhanced versions based on feedback
5. **Score Comparison** - Shows improvement amount

## Where to Find Each Component

### In Summary Format (Default)
- ✅ Original idea text
- ✅ Initial score
- ✅ Multi-dimensional analysis summary
- ✅ Advocacy & Skepticism summaries
- ✅ Score change (but NOT improved idea text)
- ❌ Full improved idea

### In Text Format
- ✅ Everything from summary format
- ❌ Improved idea (display bug - being generated but not shown)

### In JSON Format
- ✅ EVERYTHING including improved ideas
- Access improved idea: `.improved_idea` field
- Access all scores: `.dimension_scores` object

## Best Commands for Different Needs

### Quick Overview
```bash
madspark "Your theme" "Your constraints" --async
```

### See Improved Ideas
```bash
# Save as JSON and extract
madspark "Your theme" "Your constraints" --output-format json --output-file results.json --async

# View improved idea
cat results.json | jq '.[0].improved_idea'
```

### Full Analysis Report
```bash
# Export all formats
madspark "Your theme" "Your constraints" --export all --async

# Check exports folder
ls exports/
```

### Interactive Exploration
```bash
# Save and explore with jq
madspark "Your theme" "Your constraints" --output-format json | \
  jq '.[] | {
    original: .idea,
    improved: .improved_idea,
    score_change: (.new_score - .score),
    dimensions: .dimension_scores
  }'
```

## Understanding the Multi-Dimensional Scores

Each idea gets 7 dimension scores:
- **Feasibility**: How practical/achievable (higher = easier)
- **Innovation**: How creative/novel (higher = more innovative)
- **Impact**: Potential benefit/effect (higher = more impactful)
- **Cost-Effectiveness**: Value for resources (higher = better value)
- **Scalability**: Growth potential (higher = more scalable)
- **Risk Assessment**: Risk level (LOWER = less risky)
- **Timeline**: Time efficiency (higher = faster to implement)

## Pro Tips

1. **Improved ideas are ALWAYS generated** - they're just not visible in summary/text format due to a display issue
2. **Use JSON format + jq** for full data access
3. **Export to markdown** for readable reports: `--export markdown`
4. **Score changes** show effectiveness of the feedback loop:
   - Positive Δ: Improvement successful
   - Negative Δ: May have overcorrected
   - Zero Δ: No significant change

## Example: Complete Analysis

```bash
# Generate and save
madspark "Sustainable cities" "Under $1M budget" \
  --num-candidates 3 \
  --enhanced-reasoning \
  --async \
  --output-format json \
  --output-file cities.json

# View original ideas
cat cities.json | jq '.[] | .idea'

# View improved ideas
cat cities.json | jq '.[] | .improved_idea'

# Compare scores
cat cities.json | jq '.[] | {
  idea: .idea[0:50] + "...",
  original_score: .score,
  improved_score: .new_score,
  improvement: (.new_score - .score)
}'

# View multi-dimensional analysis
cat cities.json | jq '.[0].dimension_scores'
```