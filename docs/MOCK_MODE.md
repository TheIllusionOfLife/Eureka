# Mock Mode Documentation

MadSpark Multi-Agent System includes a comprehensive mock mode that allows you to use the system without API keys. This is perfect for development, testing, and trying out the system.

## How Mock Mode Works

### Automatic Detection
The system automatically runs in mock mode when:
1. No Google API key is configured in `.env`
2. The API key is invalid (doesn't start with "AIza")
3. The placeholder "YOUR_API_KEY_HERE" is still in `.env`

### Manual Override
You can force mock mode even with a valid API key:
```bash
MADSPARK_MODE=mock mad_spark "test topic" "test context"
```

Or force API mode (will fail if no valid key):
```bash
MADSPARK_MODE=api mad_spark "test topic" "test context"
```

## Mock Responses

In mock mode, the system returns intelligent mock responses that:
- Maintain the same structure as real API responses
- Include multi-language support detection
- Provide realistic scores and evaluations
- Allow full workflow testing

### Example Mock Response
```
Mock idea generated for topic 'consciousness' with context 'what is it?' at temperature 0.9
```

### Language Detection
Mock mode includes basic language detection:
- Japanese characters → Japanese mock response
- French accents → French mock response
- Spanish characters → Spanish mock response
- German umlauts → German mock response
- Default → English mock response

## Setup Experience

When running `./scripts/setup.sh`, you'll be prompted:
```
Would you like to:
  1) Enter your API key now
  2) Use mock mode (no API key required)
```

Choosing option 2 configures the system for mock mode automatically.

## Switching Modes

### From Mock to API Mode
1. Edit `src/madspark/.env`
2. Replace `YOUR_API_KEY_HERE` with your actual API key
3. Remove or comment out `MADSPARK_MODE="mock"` if present

### From API to Mock Mode
1. Edit `src/madspark/.env`
2. Add `MADSPARK_MODE="mock"`
3. Or simply remove/invalidate your API key

## Benefits of Mock Mode

1. **No API Costs**: Perfect for development and testing
2. **Faster Response**: No network latency
3. **Predictable Output**: Consistent responses for testing
4. **CI/CD Safe**: Tests run reliably without API dependencies
5. **Learning Tool**: Explore the system without commitment

## Use Cases

- **Development**: Build and test new features
- **CI/CD**: Run automated tests without API calls
- **Demos**: Show the system without API setup
- **Learning**: Understand the workflow before using real API
- **Debugging**: Isolate issues from API problems

## Technical Details

Mock mode is implemented in:
- `src/madspark/agents/genai_client.py`: Mode detection logic
- `src/madspark/agents/*.py`: Mock response generation
- `run.py`: Automatic mode detection and messaging

The system uses environment variables:
- `GOOGLE_API_KEY`: Your API key (if available)
- `MADSPARK_MODE`: Override mode (mock/api)
- `SUPPRESS_MODE_MESSAGE`: Hide startup messages