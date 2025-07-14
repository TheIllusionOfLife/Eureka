# Quick Start Examples

## Basic Examples

### 1. Your First Idea Generation

```bash
# Simple idea generation
python cli.py "Smart home technology" "Affordable"

# With more specific constraints
python cli.py "AI for education" "K-12 students, no internet required"
```

### 2. Control Creativity Level

```bash
# Conservative (practical ideas)
python cli.py "Healthcare innovation" "FDA compliant" --temperature-preset conservative

# Creative (innovative ideas)
python cli.py "Future transportation" "Eco-friendly" --temperature-preset creative

# Custom temperature
python cli.py "Space technology" "Near-term" --temperature 0.6
```

### 3. Process Multiple Ideas

```bash
# Process top 3 ideas in detail
python cli.py "Renewable energy" "Residential" --num-candidates 3

# Quick single idea
python cli.py "IoT devices" "Privacy-first" --num-candidates 1
```

## Enhanced Features

### 4. Advanced Reasoning

```bash
# Enable all enhanced features
python cli.py "Mental health apps" "Teens" \
  --enhanced-reasoning \
  --multi-dimensional-eval \
  --logical-inference
```

### 5. Bookmark & Remix

```bash
# Generate and bookmark ideas
python cli.py "Urban farming" "Small spaces" \
  --bookmark-results \
  --bookmark-tags urban sustainability food

# List bookmarked ideas
python cli.py --list-bookmarks

# Remix bookmarked ideas
python cli.py "Agriculture innovation" --remix --bookmark-tags urban
```

### 6. Export Formats

```bash
# Export as JSON
python cli.py "Robotics" "Home use" --export json

# Export all formats
python cli.py "Green technology" "Affordable" \
  --export all \
  --export-dir my_exports/

# Export with custom filename
python cli.py "AI assistant" "Privacy-focused" \
  --export markdown \
  --export-filename ai_privacy_ideas
```

## Performance Options

### 7. Async Execution

```bash
# Faster async processing
python cli.py "Blockchain applications" "Real-world" \
  --async \
  --timeout 90
```

### 8. Caching

```bash
# Enable caching (requires Redis)
python cli.py "Machine learning" "Beginner-friendly" \
  --enable-cache
```

## Batch Processing

### 9. Process Multiple Themes

```bash
# Create sample batch file
python cli.py --create-sample-batch csv

# Process batch
python cli.py --batch sample_batch.csv \
  --batch-concurrent 3 \
  --batch-export-dir results/
```

### 10. Interactive Mode

```bash
# Start interactive session
python cli.py --interactive

# In the session:
# - Enter theme: Climate solutions
# - Add constraints: Local community
# - Choose temperature: Creative
# - Enable features as needed
```

## Common Use Cases

### 11. Startup Ideation

```bash
python cli.py "B2B SaaS ideas" \
  "Low competition, high demand, solo founder" \
  --temperature-preset creative \
  --num-candidates 5 \
  --enhanced-reasoning \
  --export all
```

### 12. Research Brainstorming

```bash
python cli.py "Quantum computing applications" \
  "Near-term, practical" \
  --temperature-preset balanced \
  --multi-dimensional-eval \
  --logical-inference \
  --output-format json > quantum_ideas.json
```

### 13. Product Feature Ideas

```bash
python cli.py "Mobile app features" \
  "Fitness tracking, unique selling points" \
  --bookmark-results \
  --bookmark-tags product mobile fitness \
  --verbose
```

### 14. Content Creation

```bash
python cli.py "YouTube channel concepts" \
  "Tech education, beginner-friendly" \
  --temperature-preset wild \
  --num-candidates 3 \
  --export markdown
```

## Advanced Combinations

### 15. Full Analysis Pipeline

```bash
# Generate with all features and export
python cli.py "Environmental tech" "Developing countries" \
  --enhanced-reasoning \
  --multi-dimensional-eval \
  --logical-inference \
  --num-candidates 3 \
  --async \
  --enable-cache \
  --bookmark-results \
  --bookmark-tags environment international \
  --export all \
  --export-dir environmental_analysis/ \
  --verbose > analysis.log 2>&1
```

### 16. Iterative Refinement

```bash
# Round 1: Broad exploration
python cli.py "Healthcare AI" "General" \
  --temperature-preset creative \
  --bookmark-results \
  --bookmark-tags healthcare round1

# Round 2: Focused refinement
python cli.py "Healthcare AI" \
  "Elderly care, home monitoring" \
  --remix \
  --bookmark-tags round1 \
  --temperature-preset balanced \
  --enhanced-reasoning
```

### 17. Competitive Analysis

```bash
# Generate ideas in competitor's space
python cli.py "E-commerce innovation" \
  "Better than Amazon Prime" \
  --temperature-preset creative \
  --multi-dimensional-eval \
  --num-candidates 5 \
  --export-dir competitive_analysis/
```

## Tips for Best Results

### Theme Writing
- Be specific but not too narrow
- Good: "AI for elderly care"
- Too broad: "Technology"
- Too narrow: "AI chatbot for 85+ year olds with dementia in nursing homes"

### Constraint Guidelines
- 2-3 constraints work best
- Make them actionable
- Good: "Under $1000, works offline"
- Vague: "Easy to use, innovative"

### Temperature Selection
- 0.3-0.5: Practical, proven concepts
- 0.6-0.8: Balanced innovation
- 0.9-1.2: Creative, experimental
- 1.3-2.0: Wild, unconventional

### Processing Options
- Start with 1-2 candidates for testing
- Use 3-5 for comprehensive analysis
- Enable features selectively based on needs
- Always bookmark interesting results

## Troubleshooting Quick Fixes

```bash
# API key issues
export GOOGLE_API_KEY="your-key-here"

# Timeout issues  
--timeout 120 --async

# Memory issues
--num-candidates 1

# See what's happening
--verbose

# Save everything
--export all --output-file backup.json
```