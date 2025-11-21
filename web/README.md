# MadSpark Web Interface Guide

This README provides essential information for using the MadSpark web interface effectively.

## 📌 Important: Two Setup Scripts

MadSpark has **two separate setup scripts** for different purposes:

| Script | Purpose | Usage |
|--------|---------|-------|
| **`~/Eureka/scripts/setup.sh`** | Main CLI application | Sets up `mad_spark`/`ms` commands for terminal use |
| **`~/Eureka/web/setup.sh`** | Web interface (this guide) | Sets up Docker containers for browser UI at http://localhost:3000 |

**Choose based on your needs:**
- Want to use `ms "topic" "context"` in terminal? → Use `scripts/setup.sh`
- Want to use the web browser interface? → Use `web/setup.sh`
- Want both? → Run both setup scripts!

This guide focuses on the **web interface** only.

## 🚀 Quick Start

### Automated Setup (Easiest)

**Note:** This is the web interface setup script. For the main CLI application (`mad_spark`/`ms` commands), use `~/Eureka/scripts/setup.sh` instead.

```bash
cd ~/Eureka/web
./setup.sh

# Follow the interactive prompts to choose:
# 1) Ollama (Free, Local) - Recommended
# 2) Gemini (Cloud, Requires API Key)
# 3) Mock (Testing only, no LLM calls)
```

### Starting with Ollama (Free Local Inference - Default)

```bash
cd ~/Eureka/web
docker compose up -d

# Defaults to Ollama-first mode (MADSPARK_MODE=api)
# First startup will automatically download Ollama models:
# - gemma3:4b-it-qat (4GB) - Fast tier
# - gemma3:12b-it-qat (8.9GB) - Balanced tier
# This may take 5-15 minutes depending on your internet speed

# Check model download progress:
docker compose logs -f ollama

# Verify models are ready:
docker exec web-ollama-1 ollama list
```

### Starting with Gemini API Key (Cloud Inference)

```bash
# Method 1: Using environment variables from root .env file
cd ~/Eureka
source .env  # Load your GOOGLE_API_KEY from root .env
cd web
MADSPARK_MODE=api GOOGLE_API_KEY=$GOOGLE_API_KEY docker compose up -d

# Method 2: Direct environment variables
cd ~/Eureka/web
MADSPARK_MODE=api GOOGLE_API_KEY="your-actual-api-key" docker compose up -d

# Method 3: Using the alias (if configured in ~/.zshrc or ~/.bashrc)
madspark-web
```

### Starting in Mock Mode (Testing Only)

```bash
cd ~/Eureka/web
MADSPARK_MODE=mock docker compose up -d

# Mock mode returns pre-generated responses without calling any LLM
# Useful for testing the UI without API costs or model downloads
```

### Accessing the Interface

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Health: http://localhost:8000/api/health
- API Docs: http://localhost:8000/docs
- Ollama API: http://localhost:11434

## 🤖 LLM Provider Architecture

MadSpark uses an **Ollama-first architecture** for cost-free local inference with automatic fallback to Gemini.

### Provider Selection (Auto Mode - Default)

When `MADSPARK_LLM_PROVIDER=auto` (default), the router uses:
1. **Ollama (Primary)**: Free local inference with gemma3 models
2. **Gemini (Fallback)**: Cloud API for PDFs, URLs, or when Ollama fails

### Available Providers

| Provider | Models | Cost | Use Case |
|----------|--------|------|----------|
| **Ollama** | gemma3:4b-it-qat (fast)<br>gemma3:12b-it-qat (balanced) | FREE | Text-only, images (local) |
| **Gemini** | gemini-2.5-flash | Paid | PDFs, URLs, fallback |

### Model Tiers

Configure via UI "Advanced LLM Settings" or `MADSPARK_MODEL_TIER`:

- **Fast** (default): gemma3:4b-it-qat - Quick responses (~10s)
- **Balanced**: gemma3:12b-it-qat - Better quality (~20s)
- **Quality**: gemini-2.5-flash - Best results (cloud, paid)

### LLM Usage Statistics

After generating ideas, scroll to the bottom to see:
- **Provider Usage**: "Ollama: X | Gemini: Y"
- **Total Cost**: Shows $0 when using Ollama
- **Cache Hit Rate**: Percentage of cached responses
- **Message**: "Using local Ollama inference saved you money!" when Ollama is used

### Ollama Setup

#### System Requirements

**Minimum for Ollama models:**
- **RAM**: 16GB minimum (models use ~13GB when loaded)
- **Disk**: 15GB free space (13GB for models + 2GB for Docker)
- **CPU**: Multi-core recommended (4+ cores for acceptable performance)
- **GPU**: Optional - NVIDIA GPU significantly improves inference speed

**Note**: Models are loaded into RAM during inference. System will swap to disk if insufficient RAM, causing severe performance degradation.

#### Automatic Setup (Recommended)

Models are automatically downloaded on first `docker compose up` (API mode is default):

```bash
cd ~/Eureka/web
docker compose up -d  # API mode is default, downloads Ollama models

# Monitor download progress (first time only):
docker compose logs -f ollama
# Expected output:
# - "pulling manifest..."
# - "pulling 1fb99eda86dc: XX% ..."
# - Total download: ~13GB for both models
```

#### Manual Model Management

```bash
# List installed models
docker exec web-ollama-1 ollama list

# Pull specific model manually
docker exec web-ollama-1 ollama pull gemma3:4b-it-qat

# Remove unused model
docker exec web-ollama-1 ollama rm model-name

# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "gemma3:4b-it-qat",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

#### Disable Auto-Download

If you want to manually control model downloads, comment out the entrypoint in `docker-compose.yml`:

```yaml
ollama:
  # entrypoint: ["/bin/sh", "-c", "ollama serve & ..."]  # Commented out
```

Then pull models manually as shown above.

### Mode Configuration

The system defaults to **API mode** (production-ready with Ollama):

**API Mode (Default):**
```bash
docker compose up -d  # Uses Ollama for free local inference
```

**Mock Mode (Testing):**
```bash
MADSPARK_MODE=mock docker compose up -d  # Pre-generated responses, no LLM calls
```

**Why API mode is default:** The docker-compose.yml is configured for Ollama-first architecture. Models are downloaded automatically on first startup, enabling free local inference without any API key configuration.

## 📝 Web Interface Field Names

**IMPORTANT**: The web interface uses user-friendly display names that differ from internal API field names:

| Display Name | Internal Name | Description |
|-------------|--------------|-------------|
| **Topic** | `topic` | The main subject for idea generation (required) |
| **Context** | `context` | Additional requirements or limitations (optional) |
| **Number of Top Ideas** | `num_top_candidates` | How many ideas to generate (1-5) |
| **Creativity Level** | `temperature_preset` or `temperature` | Controls randomness/creativity |
| **Enhanced Reasoning** | `enhanced_reasoning` | Enables advocate & skeptic agents |
| **Logical Inference** | `logical_inference` | Enables logical analysis |
| **Show Detailed Results** | `show_detailed_results` | Shows all analysis sections |

## 🎛️ Feature Checkboxes Explained

### Enhanced Features
- **Enhanced Reasoning**: Adds advocate & skeptic analysis
  - When checked: Runs additional analysis agents
  - When unchecked: No advocacy/skepticism sections appear
  
- **Logical Inference**: Adds logical analysis
  - When checked: Shows causal chains, constraints, implications
  - When unchecked: No logical inference section
  - **NOTE**: Requires real API key (not available in mock mode)

### Display Options
- **Show Detailed Results**: Controls what sections are visible
  - When checked: Shows all analysis sections (if data exists)
  - When unchecked: Shows only improved ideas and scores
  
### Other Options
- **Enable Novelty Filter**: Filters duplicate/similar ideas
- **Verbose Mode**: Shows detailed progress during generation

## 🔧 Checkbox Independence Rules

1. **Enhanced Reasoning OFF + Detailed Results ON**
   - No advocacy/skepticism sections shown (no data generated)

2. **Enhanced Reasoning ON + Detailed Results OFF**
   - Processing includes advocacy/skepticism
   - But sections are not displayed

3. **Both ON**
   - All sections display with full content

4. **Logical Inference** follows same rules as Enhanced Reasoning

## 🐳 Docker Commands

```bash
# View logs
docker compose logs -f backend

# Check backend environment
docker exec web-backend-1 env | grep GOOGLE

# Restart services
docker compose restart

# Stop services
docker compose down

# Rebuild after code changes
docker compose build backend
docker compose up -d
```

## 🔍 Troubleshooting

### API Key Not Working
1. Check if API key is set correctly:
   ```bash
   docker exec web-backend-1 env | grep GOOGLE_API_KEY
   ```
2. Should NOT show: `GOOGLE_API_KEY=test_api_key`
3. Should show your actual key or proper mock key

### Logical Inference Not Showing
1. Requires real API key (not available in mock mode)
2. Check backend logs for "ReasoningEngine initialized with genai_client"
3. Ensure both checkboxes are checked:
   - ✅ Logical Inference
   - ✅ Show Detailed Results

### Mock Mode Indicators
- Results appear very quickly (< 5 seconds)
- Scores are always round numbers (6.5, 7.0, 7.5)
- Ideas have generic content
- Backend logs show "Running in mock mode"

## 📊 API Response Structure

The web interface expects these fields in API responses:
```json
{
  "idea": "Original idea text",
  "improved_idea": "Enhanced idea text",
  "initial_score": 6.5,
  "improved_score": 8.2,
  "initial_critique": "...",
  "advocacy": "...",           // Only if enhanced_reasoning=true
  "skepticism": "...",         // Only if enhanced_reasoning=true
  "logical_inference": {...},  // Only if logical_inference=true
  "multi_dimensional_evaluation": {...}
}
```

## 🌐 Environment Variables

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MADSPARK_MODE` | `api` (production) or `mock` (testing) | `api` |
| `GOOGLE_API_KEY` | Your Gemini API key (optional with Ollama) | `test_api_key` |
| `GOOGLE_GENAI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |

### LLM Router Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MADSPARK_LLM_PROVIDER` | `auto`, `ollama`, or `gemini` | `auto` |
| `MADSPARK_MODEL_TIER` | `fast`, `balanced`, or `quality` | `fast` |
| `MADSPARK_CACHE_ENABLED` | Enable response caching | `true` |
| `MADSPARK_CACHE_DIR` | Cache directory path | `/cache/llm` |
| `OLLAMA_HOST` | Ollama server URL | `http://ollama:11434` |
| `OLLAMA_MODEL_FAST` | Fast tier model | `gemma3:4b-it-qat` |
| `OLLAMA_MODEL_BALANCED` | Balanced tier model | `gemma3:12b-it-qat` |

## 🧪 Testing Different Scenarios

### Test Japanese Input
```
Topic: 持続可能な都市農業
Context: 低コストで実現可能
```

### Test with All Features
1. Check: Enhanced Reasoning ✅
2. Check: Logical Inference ✅  
3. Check: Show Detailed Results ✅
4. Submit and verify all sections appear

### Test Checkbox Independence
1. Check only: Show Detailed Results ✅
2. Submit and verify NO advocacy/skepticism sections
3. Uncheck all, check only: Enhanced Reasoning ✅
4. Submit and verify processing completes but no extra sections shown