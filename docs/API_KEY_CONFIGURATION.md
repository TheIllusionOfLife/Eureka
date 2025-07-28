# API Key Configuration Guide

This guide explains how to configure your Google Gemini API key for MadSpark.

## Quick Configuration

The easiest way to configure your API key is using the interactive config command:

```bash
mad_spark config
```

This will show you:
1. Current configuration status
2. Interactive menu to set up your API key
3. Option to switch between API and mock modes

## Non-Interactive Environments

If you're in a non-interactive environment (like CI/CD or automated scripts), you can:

### View Current Configuration
```bash
mad_spark config --status
```

### Configure API Key Programmatically
```bash
# Set environment variable before running
export GOOGLE_API_KEY="AIzaSy..."
mad_spark "your topic"

# Or override mode explicitly
MADSPARK_MODE=api GOOGLE_API_KEY="AIzaSy..." mad_spark "your topic"
```

## Understanding Modes

### Mock Mode (Default)
- No API key required
- Returns simulated responses
- Perfect for development and testing
- Automatically selected when no valid API key is found

### API Mode
- Requires valid Google Gemini API key
- Generates real AI responses
- Automatically selected when valid API key is configured

## Getting an API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Run `mad_spark config` and choose option 1
5. Enter your API key when prompted

## Troubleshooting

### "Non-interactive mode detected"
This message appears when running in environments without a terminal (like automated scripts). Use `mad_spark config --status` to view configuration or set environment variables directly.

### API Key Not Working
- Ensure your key starts with "AIza"
- Check that it's at least 30 characters long
- Verify you have API access enabled in Google Cloud Console

### Switching Back to Mock Mode
Run `mad_spark config` and choose option 2, or manually set:
```bash
export MADSPARK_MODE=mock
```