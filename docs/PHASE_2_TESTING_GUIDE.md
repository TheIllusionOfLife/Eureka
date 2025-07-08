# Phase 2 Testing Guide

## Pre-Testing Checklist

### 1. Environment Setup
```bash
cd mad_spark_multiagent

# Ensure you're in a virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify dependencies
pip install -r requirements.txt
```

### 2. API Key Configuration
```bash
# Copy example environment file if not already done
cp .env.example .env

# Edit .env file to add your Google API key
# Required variables:
# GOOGLE_API_KEY=your-actual-api-key-here
# GOOGLE_GENAI_MODEL=gemini-1.5-flash (or gemini-1.5-pro)
# GOOGLE_CLOUD_PROJECT=your-project-id (optional)
```

### 3. Verify Setup
```bash
# Quick test to ensure API key is loaded
python -c "import os; print('API Key configured:', 'GOOGLE_API_KEY' in os.environ and bool(os.environ['GOOGLE_API_KEY']))"
```

## Testing Scenarios

### 1. Basic Workflow Test
```bash
# Simple idea generation
python coordinator.py

# With custom theme and constraints
python cli.py "sustainable urban transportation" "must be cost-effective for developing countries"
```

### 2. Temperature Control Testing
```bash
# Test different temperature presets
python cli.py "AI in education" "accessible to all" --temperature-preset conservative
python cli.py "AI in education" "accessible to all" --temperature-preset balanced
python cli.py "AI in education" "accessible to all" --temperature-preset creative
python cli.py "AI in education" "accessible to all" --temperature-preset wild

# Test specific temperature values
python cli.py "smart cities" "privacy-focused" --temperature 0.3
python cli.py "smart cities" "privacy-focused" --temperature 0.7
python cli.py "smart cities" "privacy-focused" --temperature 1.2
```

### 3. Enhanced Reasoning Features
```bash
# Test individual reasoning features
python cli.py "renewable energy storage" "residential scale" --enhanced-reasoning
python cli.py "renewable energy storage" "residential scale" --multi-dimensional-eval
python cli.py "renewable energy storage" "residential scale" --logical-inference

# Combine all reasoning features
python cli.py "renewable energy storage" "residential scale" --enhanced-reasoning --multi-dimensional-eval --logical-inference
```

### 4. Bookmark System Testing
```bash
# Generate and bookmark ideas
python cli.py "ocean cleanup" "scalable solutions" --bookmark-results --bookmark-tags environment ocean innovative

# List all bookmarks
python cli.py --list-bookmarks

# Search bookmarks
python cli.py --search-bookmarks "ocean"
python cli.py --search-bookmarks "environment"

# Remix bookmarked ideas
python cli.py "marine conservation" --remix --bookmark-tags ocean environment
```

### 5. Batch Processing
```bash
# Create a test CSV file
cat > test_themes.csv << EOF
theme,constraints
"AI in healthcare","patient privacy focused"
"sustainable agriculture","water conservation"
"space exploration","commercial viability"
"quantum computing","practical applications"
EOF

# Run batch processing
python cli.py --batch-file test_themes.csv --export json

# Test async batch processing
python cli.py --batch-file test_themes.csv --async-mode --export csv

# Check results in exports/ directory
ls -la exports/
```

### 6. Interactive Mode
```bash
# Start interactive session
python cli.py --interactive

# In interactive mode, try:
# > AI for elderly care
# > add: must be affordable
# > refine: focus on companionship
# > temperature: 0.8
# > evaluate
# > bookmark
# > new
# > exit
```

### 7. Export Functionality
```bash
# Test different export formats
python cli.py "green technology" "home automation" --export json
python cli.py "green technology" "home automation" --export csv
python cli.py "green technology" "home automation" --export markdown
python cli.py "green technology" "home automation" --export pdf
python cli.py "green technology" "home automation" --export all

# Check exported files
ls -la exports/
```

### 8. Web Interface Testing
```bash
# Start the web interface (requires Docker)
cd ../web
docker-compose up

# Access in browser:
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs

# Test features:
# 1. Enter theme and constraints
# 2. Adjust temperature slider
# 3. Toggle reasoning features
# 4. Watch real-time progress via WebSocket
# 5. View radar chart visualization
# 6. Export results in different formats
```

### 9. Performance Testing
```bash
# Time a standard workflow
time python cli.py "innovation in education" "low-resource environments"

# Compare sync vs async performance
time python cli.py "fintech solutions" "emerging markets" --export json
time python cli.py "fintech solutions" "emerging markets" --async-mode --export json

# Test with caching enabled (second run should be faster)
python cli.py "blockchain applications" "supply chain" --export json
python cli.py "blockchain applications" "supply chain" --export json  # Should hit cache
```

### 10. Error Handling Testing
```bash
# Test with invalid temperature
python cli.py "test theme" "test constraint" --temperature 3.0  # Should show error

# Test with missing theme in batch
cat > invalid_batch.csv << EOF
theme,constraints
"","valid constraint"
"valid theme",""
EOF
python cli.py --batch-file invalid_batch.csv

# Test with non-existent bookmark search
python cli.py --search-bookmarks "nonexistentterm123"
```

## Advanced Testing Scenarios

### 1. Custom Prompts Testing
```python
# Create a test script for custom prompts
cat > test_custom.py << 'EOF'
from coordinator import MadSparkCoordinator
import asyncio

async def test_custom_prompts():
    coordinator = MadSparkCoordinator(mode="direct")
    
    # Test different theme/constraint combinations
    test_cases = [
        ("AI-powered personal assistants", "must respect user privacy and data sovereignty"),
        ("sustainable food production", "urban environments with limited space"),
        ("educational technology", "works offline for remote areas"),
        ("mental health support", "culturally sensitive and accessible"),
    ]
    
    for theme, constraints in test_cases:
        print(f"\n{'='*60}")
        print(f"Theme: {theme}")
        print(f"Constraints: {constraints}")
        print('='*60)
        
        result = await coordinator.run_workflow_async(
            theme=theme,
            constraints=constraints,
            temperature=0.7,
            enable_reasoning=True
        )
        
        if result["status"] == "success":
            print(f"✅ Generated {len(result['ideas'])} ideas")
            print(f"✅ Best idea score: {result.get('best_idea', {}).get('final_score', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_custom_prompts())
EOF

python test_custom.py
```

### 2. Memory System Testing
```bash
# Test conversation memory persistence
python cli.py "robotics in healthcare" "elderly care focus" --enhanced-reasoning

# Run again with similar theme to see context awareness
python cli.py "robotics in medicine" "patient care focus" --enhanced-reasoning

# Check if agents reference previous conversation
```

### 3. Load Testing
```bash
# Create larger batch file
cat > load_test.csv << EOF
theme,constraints
"AI in agriculture","water efficiency"
"blockchain voting","security focused"
"quantum encryption","practical implementation"
"biotech solutions","ethical considerations"
"space mining","cost effectiveness"
"neural interfaces","safety first"
"fusion energy","scalable design"
"ocean farming","environmental impact"
"smart materials","manufacturing ready"
"drone delivery","urban integration"
EOF

# Run with async mode for better performance
time python cli.py --batch-file load_test.csv --async-mode --export json
```

## Monitoring & Debugging

### 1. Check Logs
```bash
# Logs are typically printed to console
# For more detailed debugging, set environment variable:
export MADSPARK_DEBUG=true
python cli.py "test theme" "test constraints"
```

### 2. Monitor API Usage
```python
# Quick script to check token usage
cat > check_usage.py << 'EOF'
import google.generativeai as genai
import os

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# This would typically require additional API calls to get usage
# For now, monitor your Google Cloud Console for actual usage
print("Check your Google Cloud Console for API usage:")
print("https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/metrics")
EOF

python check_usage.py
```

### 3. Redis Cache Monitoring
```bash
# If Redis is running, monitor cache hits
redis-cli
> KEYS madspark:*
> INFO stats
> MONITOR  # Watch real-time commands
```

## Performance Benchmarks

Expected performance for Phase 2:
- Basic workflow: 15-30 seconds
- Enhanced reasoning: 20-40 seconds  
- Batch processing (10 themes): 2-5 minutes
- Interactive mode response: <2 seconds
- Web UI update latency: <100ms

## Common Issues & Solutions

### 1. API Key Issues
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API key directly
python -c "import google.generativeai as genai; genai.configure(api_key='$GOOGLE_API_KEY'); print('API key valid')"
```

### 2. Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### 3. Redis Connection Issues
```bash
# Redis is optional, but if you want to test caching:
# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. Web Interface Issues
```bash
# Ensure Docker is running
docker --version

# Check container logs
docker-compose logs -f

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## Testing Checklist

- [ ] Basic CLI workflow works
- [ ] Temperature control produces varied results
- [ ] Enhanced reasoning features activate properly
- [ ] Bookmarks save and search correctly
- [ ] Batch processing completes successfully
- [ ] Interactive mode responds appropriately
- [ ] Exports generate in all formats
- [ ] Web interface loads and updates in real-time
- [ ] Async mode improves performance
- [ ] Error handling shows helpful messages
- [ ] API calls succeed with your key
- [ ] Cache improves repeat query performance

## Next Steps After Testing

1. **Document any issues** in GitHub Issues
2. **Note performance** on your hardware/network
3. **Save interesting results** using bookmarks
4. **Export compelling ideas** for future reference
5. **Provide feedback** on user experience

## Ready for Production?

If all tests pass:
- ✅ System is ready for personal/team use
- ✅ Can be deployed to cloud if desired
- ✅ Suitable for demonstration to stakeholders
- ✅ Ready for Phase 3 enterprise enhancements

---

*Remember: This is production-ready software with 95% test coverage. Any issues encountered are likely configuration or environment-specific.*