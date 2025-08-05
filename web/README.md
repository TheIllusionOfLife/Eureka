# MadSpark Web Interface Guide

This README provides essential information for using the MadSpark web interface effectively.

## 🚀 Quick Start

### Starting with Real API Key (Production Mode)

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

### Starting in Mock Mode (Development/Testing)

```bash
cd ~/Eureka/web
docker compose up -d  # Defaults to mock mode
```

### Accessing the Interface

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Health: http://localhost:8000/api/health
- API Docs: http://localhost:8000/docs

## 📝 Web Interface Field Names

**IMPORTANT**: The web interface uses user-friendly display names that differ from internal API field names:

| Display Name | Internal Name | Description |
|-------------|--------------|-------------|
| **Topic** | `theme` | The main subject for idea generation (required) |
| **Context** | `constraints` | Additional requirements or limitations (optional) |
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

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Your Gemini API key | `test_api_key` |
| `GOOGLE_GENAI_MODEL` | Model to use | `gemini-2.5-flash` |
| `MADSPARK_MODE` | `api` or `mock` | `mock` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |

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