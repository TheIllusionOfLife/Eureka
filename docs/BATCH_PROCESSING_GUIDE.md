# Batch Processing Guide

> **Note**: This guide covers batch processing of multiple topics/themes. For information about API call optimization through intelligent batch processing (which reduces API calls by 50%), see the [API Monitoring section](../README.md#-batch-api-monitoring--cost-analysis) in the main README.

## Overview

The MadSpark Multi-Agent System supports batch processing, allowing you to generate ideas for multiple themes simultaneously. This is perfect for:
- Exploring variations of a concept
- Processing multiple client requests
- Generating ideas across different domains
- A/B testing different constraints

## Quick Start

### 1. Using Sample Batch Files

```bash
# Create a sample CSV batch file
python cli.py --create-sample-batch csv

# Create a sample JSON batch file  
python cli.py --create-sample-batch json

# Process the batch
python cli.py --batch sample_batch.csv
```

### 2. CSV Format

Create a CSV file with the following columns:

```csv
theme,constraints,temperature_preset,num_candidates,tags
"AI in healthcare","Budget-friendly, implementable within 6 months",balanced,2,"healthcare,ai,budget"
"Sustainable urban farming","Small spaces, minimal water usage",creative,3,"sustainability,urban,farming"
"Remote education technology","Works offline, accessible to all ages",conservative,2,"education,remote,accessibility"
```

**Column Descriptions:**
- `theme` (required): The main topic for idea generation
- `constraints` (optional): Specific requirements or limitations
- `temperature_preset` (optional): One of: conservative, balanced, creative, wild
- `num_candidates` (optional): Number of top ideas to fully process (1-5)
- `tags` (optional): Comma-separated tags for organization

### 3. JSON Format

For more complex configurations, use JSON:

```json
[
  {
    "theme": "AI in healthcare",
    "constraints": "Budget-friendly, HIPAA compliant",
    "temperature_preset": "balanced",
    "num_candidates": 2,
    "enhanced_reasoning": true,
    "multi_dimensional_eval": true,
    "tags": ["healthcare", "ai", "compliance"]
  },
  {
    "theme": "Green energy solutions",
    "constraints": "Residential scale",
    "temperature": 0.8,
    "num_candidates": 3,
    "logical_inference": true,
    "tags": ["energy", "residential"]
  }
]
```

## Advanced Options

### Concurrent Processing

Process multiple items in parallel for faster results:

```bash
# Process 3 items concurrently
python cli.py --batch input.csv --batch-concurrent 3

# Use all available CPU cores
python cli.py --batch input.json --batch-concurrent -1
```

### Export Options

Save results to a specific directory:

```bash
# Export to custom directory
python cli.py --batch input.csv --batch-export-dir results/batch_001/

# Export with all formats
python cli.py --batch input.csv --batch-export-dir results/ --export all
```

### Combining with Other Features

```bash
# Batch with async processing and caching
python cli.py --batch input.csv --async --enable-cache

# Batch with enhanced features
python cli.py --batch input.json --enhanced-reasoning --logical-inference

# Batch with verbose logging
python cli.py --batch input.csv --verbose > batch_log.txt 2>&1
```

## Output Structure

Batch results are saved as:
```
batch_export_dir/
├── item_001_[theme_slug]/
│   ├── results.json
│   ├── results.csv
│   ├── results.md
│   └── results.pdf
├── item_002_[theme_slug]/
│   └── ...
└── batch_summary.json
```

### Batch Summary Format

The `batch_summary.json` contains:
```json
{
  "total_items": 3,
  "successful": 3,
  "failed": 0,
  "total_time": 125.4,
  "timestamp": "2025-07-14T12:00:00",
  "items": [
    {
      "theme": "AI in healthcare",
      "status": "success",
      "ideas_generated": 2,
      "processing_time": 42.1,
      "output_dir": "item_001_ai_in_healthcare"
    }
  ]
}
```

## Best Practices

1. **Start Small**: Test with 2-3 items before running large batches
2. **Use Concurrent Processing**: Set `--batch-concurrent` based on your API limits
3. **Monitor Progress**: Use `--verbose` to track processing
4. **Set Appropriate Timeouts**: Increase timeout for large batches
5. **Tag Consistently**: Use tags for easy organization and retrieval

## Error Handling

- Failed items are logged but don't stop the batch
- Partial results are saved even if batch is interrupted
- Use `--verbose` to see detailed error messages
- Check `batch_summary.json` for overview of successes/failures

## Example Workflows

### Research Batch
```bash
# Create research batch file
cat > research_topics.csv << EOF
theme,constraints,temperature_preset,num_candidates,tags
"Quantum computing applications","Practical, near-term",balanced,3,"quantum,research"
"Biotechnology breakthroughs","Ethical, sustainable",creative,3,"biotech,research"
"Space exploration tech","Cost-effective",conservative,2,"space,research"
EOF

# Process with full analysis
python cli.py --batch research_topics.csv \
  --enhanced-reasoning \
  --multi-dimensional-eval \
  --batch-export-dir research_results/
```

### Client Ideation Batch
```bash
# Process multiple client requests
python cli.py --batch client_requests.json \
  --batch-concurrent 5 \
  --export all \
  --batch-export-dir client_results/$(date +%Y%m%d)/
```

## Tips & Tricks

- Use `temperature_preset` for consistency across batch items
- Include relevant tags for easy searching later
- Set `num_candidates` lower (1-2) for faster processing
- Use JSON format when you need different settings per item
- Always backup your input files before large batches