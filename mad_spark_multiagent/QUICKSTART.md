# MadSpark Quick Start Guide

## 🚀 Getting Started in 30 Seconds

### Option 1: Using the MadSpark Command (Easiest)

The `madspark` command is now available globally in your terminal:

```bash
madspark "Your theme" "Your constraints" --async --timeout 300
```

Example:
```bash
madspark "How to draw better" "Within a week" --async --timeout 300
```

Note: If the command isn't found, you may need to open a new terminal or run `source ~/.zshrc`.

### Option 2: Using the Script Directly

```bash
./run_madspark.sh "Your theme" "Your constraints" --async --timeout 300
```

### Option 3: Manual Command

```bash
source venv/bin/activate && set -a && source .env && set +a && python cli.py "Your theme" "Your constraints" --async --timeout 300
```

## 🎯 Common Use Cases

### Quick Test (1 idea, 2 minutes)
```bash
madspark "Test idea" "Simple" --num-candidates 1 --timeout 120
```

### Standard Generation (2 ideas, 5 minutes)
```bash
madspark "Your theme" "Your constraints" --async --timeout 300
```

### Comprehensive Analysis (5 ideas, 10 minutes)
```bash
madspark "Your theme" "Your constraints" --num-candidates 5 --async --timeout 600
```

### With Enhanced Features
```bash
madspark "Your theme" "Your constraints" --enhanced-reasoning --logical-inference --async
```

## ⚡ Performance Tips

1. **Always use `--async`** for faster execution (1.5-2x speedup)
2. **Start with fewer candidates** (1-2) to test your theme
3. **Adjust timeout** based on complexity:
   - Simple: 120-180 seconds
   - Standard: 300-600 seconds  
   - Complex: 900-1800 seconds

## 🔧 Troubleshooting

### "GOOGLE_API_KEY is not set"

This happens when environment variables aren't loaded. Solutions:

1. **Use the alias**: `madspark` (recommended)
2. **Use the script**: `./run_madspark.sh`
3. **Never run commands separately** - they must be in one line

### Timeouts

If you get timeout errors:
- Reduce `--num-candidates` (e.g., to 1 or 2)
- Increase `--timeout` value
- Remove `--enhanced-reasoning` or `--logical-inference`

### Command Not Found

If `madspark` command isn't found:
```bash
source ~/.zshrc  # Reload your shell configuration
```

## 📋 Available Options

```bash
madspark --help  # Show all available options
```

Key options:
- `--num-candidates N`: Number of ideas to generate (default: 2)
- `--timeout N`: Timeout in seconds (default: 600)
- `--async`: Enable faster parallel processing
- `--enhanced-reasoning`: Advanced context-aware analysis
- `--logical-inference`: Formal reasoning chains
- `--output-format {json,text,summary}`: Output format
- `--temperature-preset {conservative,balanced,creative,wild}`: Creativity level

## 🎨 Example Commands

### Drawing Skills Improvement
```bash
madspark "How to improve drawing skills" "Within one week, beginner level" --async
```

### Business Ideas
```bash
madspark "AI-powered business ideas" "Under $10K budget, B2B focus" --num-candidates 3 --async
```

### Technical Solutions
```bash
madspark "Optimize database performance" "PostgreSQL, high traffic" --enhanced-reasoning --async
```

### Creative Writing
```bash
madspark "Science fiction story concepts" "Post-apocalyptic, hopeful tone" --temperature-preset creative --async
```

## 🔗 Next Steps

- Read the full documentation: `mad_spark_multiagent/README.md`
- Explore advanced features: `mad_spark_multiagent/docs/USER_GUIDE.md`
- View examples: `mad_spark_multiagent/examples/`

---

**Pro Tip**: The `madspark` alias automatically handles all environment setup for you!