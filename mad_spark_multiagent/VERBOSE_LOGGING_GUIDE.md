# 🔍 MadSpark Verbose Logging Guide

## Overview

The MadSpark Multi-Agent System now includes comprehensive verbose logging that provides complete visibility into the production workflow. You can see exactly what each agent is doing, their raw inputs/outputs, timing information, and step-by-step processing.

## How to Use Verbose Logging

### Basic Verbose Mode
```bash
# Run with verbose logging (console output)
./venv/bin/python cli.py "your topic" "constraints" --verbose

# Example
./venv/bin/python cli.py "earn money" "no illegal activities" --verbose --num-candidates 2
```

### Save Verbose Logs to File
When using `--verbose`, logs are automatically saved to timestamped files:
- **Location**: `logs/madspark_verbose_YYYYMMDD_HHMMSS.log`
- **Contains**: All logging messages and structured data
- **Format**: Timestamped entries with file/line information

### Redirect All Output to File
```bash
# Save everything (console output + logs) to a single file
./venv/bin/python cli.py "topic" "constraints" --verbose > complete_run.log 2>&1
```

## What Verbose Mode Shows

### 🔍 Step-by-Step Agent Processing

#### STEP 1: Idea Generation Agent
- **Agent**: IdeaGenerator
- **Temperature**: 0.9 (high creativity)
- **Input**: Theme and constraints
- **Output**: Raw API response, parsed ideas count, sample ideas
- **Timing**: Execution duration

#### STEP 1.5: Novelty Filtering (if enabled)
- **Filter**: NoveltyFilter
- **Input**: All generated ideas
- **Output**: Novel ideas after duplicate removal
- **Statistics**: Number of duplicates removed
- **Timing**: Filter execution duration

#### STEP 2: Critic Agent Evaluation
- **Agent**: Critic
- **Temperature**: 0.3 (analytical mode)
- **Input**: All novel ideas
- **Output**: Raw evaluation response, parsed scores/critiques
- **Processing**: Shows evaluation for each idea
- **Timing**: Evaluation duration

#### STEP 3.X: Top Candidate Processing
For each top candidate:

**STEP 3.Xa: Advocate Agent**
- **Agent**: Advocate
- **Temperature**: 0.5 (balanced persuasion)
- **Input**: Selected idea + critique
- **Output**: Raw advocacy response
- **Timing**: Advocacy generation duration

**STEP 3.Xb: Skeptic Agent**
- **Agent**: Skeptic
- **Temperature**: 0.5 (balanced skepticism)
- **Input**: Selected idea + advocacy
- **Output**: Raw skeptical analysis
- **Timing**: Skeptical analysis duration

### 📊 Data Visibility

#### Raw API Responses
- **Complete responses** from each agent (truncated for readability)
- **Character counts** for response size tracking
- **Parsing results** showing how responses are processed

#### Intermediate Processing
- **Idea parsing**: How raw text becomes structured ideas
- **Score extraction**: How numeric scores are parsed
- **Candidate selection**: Which ideas advance to detailed analysis

#### Timing Information
- **Per-step timing**: Duration for each agent call
- **Total workflow timing**: Complete process duration
- **Performance insights**: Identify bottlenecks

### 🎯 Sample Verbose Output

```
============================================================
🔍 STEP 1: Idea Generation Agent
============================================================
💡 Agent: IdeaGenerator
🎯 Theme: earn money
📋 Constraints: no illegal activities
🌡️ Temperature: 0.9 (high creativity)

📊 Raw IdeaGenerator Response:
----------------------------------------
Here are 25 diverse and creative ideas for earning money...
[Full raw response shown here]
----------------------------------------

✅ Step 1 Complete: Generated 25 ideas in 3.45s
📝 Sample Ideas:
  1. Online tutoring platform for specialized skills...
  2. Digital product creation (courses, templates)...
  3. Micro-consulting services for businesses...
  ... and 22 more ideas

============================================================
🔍 STEP 2: Critic Agent Evaluation
============================================================
🔍 Agent: Critic
📊 Input: 25 ideas
🎯 Criteria: no illegal activities
📝 Context: earn money
🌡️ Temperature: 0.3 (analytical mode)

[Continues with detailed processing...]
```

## Log File Structure

### Console Output Format
- **Visual indicators**: Emojis and symbols for easy scanning
- **Section separators**: Clear step boundaries
- **Truncated content**: Long responses abbreviated for readability
- **Summary statistics**: Key metrics at each step

### Log File Format
```
YYYY-MM-DD HH:MM:SS - INFO - coordinator.py:XXX - VERBOSE_STEP: Step name
YYYY-MM-DD HH:MM:SS - INFO - coordinator.py:XXX - VERBOSE_DETAILS: Step details
YYYY-MM-DD HH:MM:SS - INFO - coordinator.py:XXX - VERBOSE_DATA: Data label (N characters)
YYYY-MM-DD HH:MM:SS - DEBUG - coordinator.py:XXX - VERBOSE_CONTENT: [truncated content]
```

## Use Cases

### 🐛 Debugging Issues
- **Agent failures**: See exact error points and context
- **Unexpected outputs**: Analyze raw responses
- **Performance problems**: Identify slow steps

### 📊 Understanding Behavior
- **Agent decision making**: See how scores are assigned
- **Temperature effects**: Compare outputs at different creativity levels
- **Workflow optimization**: Understand processing flow

### 🔬 Research & Analysis
- **Prompt engineering**: Analyze how different inputs affect outputs
- **Model comparison**: Compare different AI model responses
- **System optimization**: Identify improvement opportunities

## Tips for Effective Use

### Performance Considerations
- **API costs**: Verbose mode doesn't add API calls, just shows existing ones
- **File sizes**: Log files can be large for many candidates
- **Console output**: Use `head` or `tail` to manage long outputs

### Best Practices
```bash
# Quick test with minimal output
./venv/bin/python cli.py "test" --verbose --num-candidates 1

# Full production run with saved logs
./venv/bin/python cli.py "real topic" "constraints" --verbose --num-candidates 3 > analysis.log 2>&1

# Monitor real-time progress
./venv/bin/python cli.py "topic" "constraints" --verbose | tee live_output.log
```

### Log Analysis
```bash
# View just the workflow steps
grep "VERBOSE_STEP" logs/madspark_verbose_*.log

# Check timing patterns
grep "Complete:" analysis.log

# Extract raw responses
grep -A 10 "Raw.*Response" analysis.log
```

## Enhanced Features

✅ **Complete agent transparency**: See every input and output  
✅ **Timing analysis**: Performance monitoring for each step  
✅ **Auto-save logs**: Timestamped files for every verbose run  
✅ **Visual indicators**: Easy-to-scan console output  
✅ **Data flow tracking**: Understand how data moves between agents  
✅ **Error visibility**: Clear error reporting and context  

The enhanced verbose logging provides unprecedented visibility into the MadSpark multi-agent workflow, making it easy to understand, debug, and optimize the system's behavior.