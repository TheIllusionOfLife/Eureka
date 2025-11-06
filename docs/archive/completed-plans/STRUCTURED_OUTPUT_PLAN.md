# Structured Output Implementation Plan

Created: 2025-08-02
Status: Planning Phase

## Overview

This document outlines the comprehensive plan to fix display format issues in MadSpark CLI output by implementing Google Gemini's structured output feature, along with related documentation updates.

## Identified Issues

1. **Ill-formatted idea headers**: `Text: 3.  **"Pixel Palette Painter"**: A generative art` - redundant "Text:" and confusing numbering
2. **Unclear enhanced analysis**: Shows only good/bad metrics without actual enhancement details
3. **Poor markdown rendering**: Advocacy/Skepticism sections have formatting issues with bullets and line breaks
4. **Inconsistent spacing**: Missing line breaks between sections
5. **Confusing score delta**: Shows `+-3.2` instead of proper improvement indicator
6. **Risk Assessment confusion**: "lower is better" contradicts overall score calculation
7. **Hidden logical inference**: `--logical` option effects are not visible in output
8. **Output truncation**: Terminal shows `... [414 lines truncated] ...` for long outputs
9. **Missing section breaks**: Improved idea sections run together
10. **General formatting inconsistency**: Different agents produce different output formats

## Implementation Plan

### Part 1: Fix Display Format Issues Using Structured Output

#### 1.1 Create Structured Response Schemas
Create new file `src/madspark/agents/response_schemas.py`:

```python
# Example schema structure
IDEA_GENERATOR_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "idea_number": {"type": "INTEGER"},
            "title": {"type": "STRING"},
            "description": {"type": "STRING"},
            "key_features": {"type": "ARRAY", "items": {"type": "STRING"}},
            "category": {"type": "STRING"}
        },
        "required": ["idea_number", "title", "description"]
    }
}

EVALUATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "score": {"type": "NUMBER"},
        "critique": {"type": "STRING"},
        "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
        "weaknesses": {"type": "ARRAY", "items": {"type": "STRING"}}
    },
    "required": ["score", "critique"]
}

ADVOCACY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "strengths": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"}
                }
            }
        },
        "opportunities": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "description": {"type": "STRING"}
                }
            }
        },
        "addressing_concerns": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "concern": {"type": "STRING"},
                    "response": {"type": "STRING"}
                }
            }
        }
    }
}
```

#### 1.2 Update All Agent Prompts
Each agent needs to be updated to use structured output:

1. **idea_generator.py**:
   - Add `responseMimeType="application/json"`
   - Include `responseSchema=IDEA_GENERATOR_SCHEMA`
   - Remove any prompt instructions about formatting

2. **evaluator.py**:
   - Use structured JSON for consistent score/critique format
   - Ensure scores are always numeric

3. **advocate.py**:
   - Use structured sections for strengths/opportunities
   - Remove markdown formatting from prompts

4. **skeptic.py**:
   - Use structured sections for flaws/risks/assumptions
   - Ensure consistent bullet point handling

5. **improver.py**:
   - Use structured JSON for improved idea details
   - Include clear section markers

#### 1.3 Fix Specific Display Issues

1. **Remove "Text:" prefix**: Update CLI formatter to use structured data directly
2. **Enhanced Analysis clarity**: 
   - Show actual logical inference results
   - Display reasoning chains
   - Highlight multi-dimensional evaluation details
3. **Markdown to CLI conversion**: Create converter for bullets, bold text, etc.
4. **Proper spacing**: Add consistent line breaks between all sections
5. **Score delta fix**: Show `+3.2` or `-3.2` without confusing double signs
6. **Risk to Safety Score**: Invert risk score and rename to "Safety Score"
7. **Logical inference visibility**: Add dedicated section when `--logical` is used
8. **Smart truncation**: Implement with file save fallback

#### 1.4 Create Output Post-Processor
New file `src/madspark/utils/output_processor.py`:
- Convert markdown lists to CLI-friendly format
- Clean up agent-generated prefixes
- Ensure consistent spacing
- Handle terminal width detection
- Smart truncation with continuation indicators

### Part 2: Documentation Updates

#### 2.1 Update README.md
Add new section:
```markdown
## Running Long Operations

MadSpark operations with multiple ideas (--top-ideas > 2) can take several minutes to complete. 
Some terminal environments impose a 2-minute timeout on commands.

### Solution: Background Execution

Use the provided background script for long operations:

```bash
./madspark-background.sh "your topic" "your context" --top-ideas 5 --enhanced --logical
```

This will:
- Start MadSpark in the background
- Save output to `outputs/background/madspark_output_TIMESTAMP.txt`
- Show you the process ID for monitoring
- Allow you to tail the output file to watch progress

### Monitoring Progress

```bash
# Check if still running
ps -p <PID>

# Watch output in real-time
tail -f outputs/background/madspark_output_TIMESTAMP.txt
```
```

#### 2.2 Update CLI Help Text
Add to help output:
- Note about timeouts for multi-idea generation
- Reference to background script
- Example commands

#### 2.3 Create Output Directory Structure
```
outputs/
├── background/     # Background script outputs
├── exports/        # Export command outputs  
├── batch/          # Batch processing outputs
└── logs/           # Debug logs (if --verbose)
```

Update files:
- `.gitignore`: Add `outputs/` with exceptions for `.gitkeep`
- `madspark-background.sh`: Use `outputs/background/` directory
- Export functions: Use `outputs/exports/`
- Batch processor: Use `outputs/batch/`

### Part 3: Enhanced Feature Visibility

#### 3.1 Enhanced Reasoning Display
When `--enhanced` is used, show:
```
🧠 Enhanced Reasoning Analysis:
├─ Context Awareness: [Details from reasoning engine]
├─ Cross-Agent Insights: [Patterns detected across agents]
└─ Reasoning Chains: [Logical connections made]
```

#### 3.2 Logical Inference Display
When `--logical` is used, show:
```
🔍 Logical Inference Analysis:
├─ Causal Chains: [Cause-effect relationships]
├─ Constraints: [Satisfied/violated constraints]
├─ Contradictions: [Any detected contradictions]
└─ Implications: [Derived implications]
```

#### 3.3 Multi-dimensional Evaluation Clarity
Always show but make clearer:
```
📊 Multi-Dimensional Evaluation:
Overall Score: 8.3/10 (Excellent)
├─ ✅ Feasibility: 9.0 (Highest)
├─ ✅ Innovation: 8.5
├─ ✅ Impact: 7.0
├─ ✅ Cost-Effectiveness: 9.5
├─ ✅ Scalability: 8.0
├─ ✅ Safety Score: 8.5 (was Risk: 1.5)
└─ ✅ Timeline: 9.0
💡 Strongest aspect: Feasibility (9.0)
⚠️  Area for improvement: Impact (7.0)
```

### Part 4: Implementation Priority

1. **Phase 1: Core Schema Implementation** (2-3 hours)
   - Create response_schemas.py
   - Update idea_generator.py first
   - Test with single idea

2. **Phase 2: All Agents Update** (3-4 hours)
   - Update remaining 4 agents
   - Update CLI formatter
   - Test multi-idea generation

3. **Phase 3: Display Enhancements** (2-3 hours)
   - Implement output post-processor
   - Add enhanced/logical sections
   - Fix all formatting issues

4. **Phase 4: Documentation** (1-2 hours)
   - Update README.md
   - Update help text
   - Create output directories
   - Update scripts

5. **Phase 5: Testing & Polish** (1-2 hours)
   - Test all formats
   - Ensure compatibility
   - Add unit tests

### Technical Implementation Notes

#### Using Gemini Structured Output
```python
from google import genai

# Configure with schema
config = genai.types.GenerateContentConfig(
    temperature=0.7,
    response_mime_type="application/json",
    response_schema=IDEA_GENERATOR_SCHEMA,
    system_instruction=SYSTEM_INSTRUCTION
)

# Generate with structured output
response = genai_client.models.generate_content(
    model=model_name,
    contents=prompt,
    config=config
)

# Parse guaranteed JSON
ideas = json.loads(response.text)
```

#### Key Benefits
1. **Consistent Format**: No more parsing natural language
2. **Reliable Structure**: Schema enforces required fields
3. **Clean Output**: No embedded markdown or formatting
4. **Type Safety**: Proper types for scores, arrays, etc.
5. **Error Reduction**: No more regex parsing failures

### Success Criteria

1. All 10 identified issues are resolved
2. Output is consistently formatted across all modes
3. Enhanced features are clearly visible when enabled
4. Background script works reliably for long operations
5. Documentation is clear and helpful
6. No regression in existing functionality

### Future Enhancements

1. Interactive mode improvements
2. Real-time progress updates in CLI
3. Web UI integration with structured data
4. Export format improvements
5. Custom output templates

---

This plan will transform MadSpark's output quality and resolve all current formatting issues through proper use of Gemini's structured output capabilities.