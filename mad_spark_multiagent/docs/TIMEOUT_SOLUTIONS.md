# Timeout Solutions for MadSpark System

## Overview

The MadSpark system can experience timeouts during complex idea generation workflows, especially when:
- Processing multiple candidates (3+ ideas)
- Using enhanced reasoning features
- Making multiple API calls to Google Gemini
- Running in environments with network latency

## Solutions Implemented

### 1. Configurable Timeout (CLI)

Added `--timeout` parameter to CLI for customizable request timeouts:

```bash
# Default timeout (10 minutes)
python cli.py "Your theme" "Your constraints"

# Custom timeout (20 minutes for complex workflows)
python cli.py "Your theme" "Your constraints" --timeout 1200

# Quick timeout (2 minutes for simple tests)
python cli.py "Your theme" "Your constraints" --timeout 120
```

**Timeout Limits:**
- Minimum: 60 seconds (1 minute)
- Default: 600 seconds (10 minutes)
- Maximum: 3600 seconds (1 hour)

### 2. Async Mode for Better Performance

Use `--async` flag to enable concurrent processing, which significantly reduces total processing time:

```bash
# Enable async mode for 1.5-2x speedup
python cli.py "Your theme" "Your constraints" --async

# Combine with custom timeout for best results
python cli.py "Your theme" "Your constraints" --async --timeout 300
```

### 3. Quick Test Script

For development and testing, use the `quick_test.py` script to avoid CLI timeouts:

```bash
# Basic quick test
python quick_test.py

# Custom test
python quick_test.py --theme "AI healthcare" --constraints "Rural areas" --candidates 2

# Direct Python usage (no shell timeout)
python -c "from quick_test import quick_test; quick_test('Your theme', 'Your constraints', 1)"
```

### 4. Web Interface Timeout

The web interface now supports configurable timeouts via API:

```javascript
// Frontend request with custom timeout
const response = await fetch('/api/generate-ideas', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    theme: 'Your theme',
    constraints: 'Your constraints',
    timeout: 900  // 15 minutes
  })
});
```

## Best Practices

### 1. Start Small
- Begin with 1-2 candidates to test your workflow
- Increase candidates only after confirming basic functionality

### 2. Use Async Mode
- Always use `--async` for workflows with 3+ candidates
- Async mode provides 1.5-2x performance improvement

### 3. Adjust Timeout Based on Complexity
- Simple ideas (1-2 candidates): 2-5 minutes
- Standard workflows (3-5 candidates): 10-15 minutes
- Complex workflows (5+ candidates, enhanced reasoning): 20-30 minutes

### 4. Monitor Progress
- Use `--verbose` flag to see detailed progress
- Check logs in `logs/` directory for debugging

### 5. Use Mock Mode for Development
- Set `GOOGLE_API_KEY` to empty string to use mock mode
- Mock mode returns instant results for testing

## Example Commands

```bash
# Quick test with short timeout
python cli.py "Test idea" "Simple" --num-candidates 1 --timeout 120

# Standard workflow with async
python cli.py "AI transportation" "Urban, under $50k" --async --timeout 600

# Complex workflow with all features
python cli.py "Sustainable cities" "Scalable" \
  --num-candidates 5 \
  --enhanced-reasoning \
  --logical-inference \
  --async \
  --timeout 1800 \
  --verbose

# Batch processing with custom timeout
python cli.py --batch ideas.csv --batch-concurrent 3 --async --timeout 900
```

## Troubleshooting

### If timeouts persist:

1. **Reduce Candidates**: Lower `--num-candidates` to 1 or 2
2. **Disable Features**: Remove `--enhanced-reasoning` or `--logical-inference`
3. **Check Network**: Ensure stable connection to Google APIs
4. **Use Mock Mode**: Test without API calls first
5. **Check Logs**: Review `logs/madspark_verbose_*.log` for errors

### For development:

1. Use `quick_test.py` instead of CLI
2. Import and call functions directly in Python
3. Use Jupyter notebooks for interactive testing
4. Set up proper async event loops for testing

## Technical Details

- Timeout implementation uses `asyncio.wait_for()` for async operations
- Synchronous operations rely on HTTP client timeouts
- All timeouts are gracefully handled with proper error messages
- Progress updates continue even during long operations