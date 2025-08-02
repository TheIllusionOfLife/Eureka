# MadSpark Output Directory

This directory contains structured outputs from MadSpark Multi-Agent System runs.

## Directory Structure

### `/structured/`
Contains results from the new structured output enhancement:

- **`json/`** - Raw JSON responses from Google Gemini structured output
- **`markdown/`** - Formatted markdown files for documentation and sharing  
- **`reports/`** - Analysis reports and session summaries

### Output Formats

#### JSON Structure (for API integration)
```json
{
  "timestamp": "2025-08-02T21:20:00Z",
  "theme": "User topic",
  "constraints": "User constraints", 
  "results": [
    {
      "idea": "Generated idea text",
      "initial_score": 8.5,
      "initial_critique": "Detailed evaluation...",
      "advocacy": "Structured advocacy points...",
      "skepticism": "Structured concerns...",
      "improved_idea": "Enhanced version...",
      "improved_score": 9.2,
      "score_delta": 0.7
    }
  ]
}
```

#### Markdown Format (for documentation)
- Clean formatting without "Text:" prefixes
- Consistent bullet points (•)
- Proper section headers (STRENGTHS, OPPORTUNITIES, etc.)
- Fixed score delta display
- Reliable logical inference integration

### Usage

Results are automatically saved here when using:
- `--output-dir output/structured/` flag
- `--save-format json` or `--save-format markdown` 
- Background processing scripts

### Benefits of Structured Output

1. **Consistent Formatting**: No more parsing errors or format inconsistencies
2. **API Integration**: Clean JSON for programmatic access
3. **Professional Display**: Enhanced markdown for presentations
4. **Debugging Support**: Structured data easier to analyze