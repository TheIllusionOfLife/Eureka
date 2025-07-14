# Interactive Mode Guide

## Overview

Interactive Mode provides a conversational interface for idea generation, perfect for:
- Exploring ideas iteratively
- Refining concepts based on results
- Learning the system step-by-step
- Collaborative brainstorming sessions

## Getting Started

Launch interactive mode:
```bash
python cli.py --interactive
```

You'll see:
```
================================================================================
🚀 MadSpark Multi-Agent System - Interactive Mode
================================================================================
Welcome! I'll guide you through generating AI-powered ideas step by step.
```

## Workflow Steps

### Step 1: Define Your Topic

```
────────────────────────────────────────
📌 Step 1: Define Your Idea Generation Topic
────────────────────────────────────────

Enter your theme/topic: AI for elderly care
Enter any constraints or requirements [No specific constraints]: Affordable and accessible
```

### Step 2: Configure Settings

```
────────────────────────────────────────
📌 Step 2: Configure Generation Settings
────────────────────────────────────────

How many top ideas to process? (1-5) [2]: 3

Choose temperature preset:
1. Conservative (Focused, practical ideas)
2. Balanced (Mix of practical and creative)
3. Creative (More innovative ideas)
4. Wild (Highly experimental ideas)
5. Custom temperature
Select option (1-5) [2]: 3
```

### Step 3: Enable Features

```
────────────────────────────────────────
📌 Step 3: Enable Advanced Features (Optional)
────────────────────────────────────────

Enable enhanced reasoning? [y/N]: y
Enable multi-dimensional evaluation? [y/N]: y
Enable logical inference? [y/N]: n
```

### Step 4: Review & Generate

```
📋 Configuration Summary:
   Theme: AI for elderly care
   Constraints: Affordable and accessible
   Temperature: Creative
   Ideas to process: 3
   Enhanced Reasoning: ✓
   Multi-Dimensional Eval: ✓

Ready to generate ideas? [Y/n]: y
```

## Interactive Features

### 1. Refinement Loop

After seeing results, you can:
```
💡 What would you like to do next?
1. Refine with new constraints
2. Try different temperature
3. Generate more ideas
4. Start fresh with new topic
5. Export results
6. Exit

Your choice:
```

### 2. Constraint Refinement

```
Current constraints: Affordable and accessible
Add to constraints or replace? [add/replace]: add
Additional constraints: Must work offline
```

### 3. Progressive Enhancement

Start simple and add features:
```
# First run - basic
Temperature: Balanced
Features: None

# See results, then enhance
Enable enhanced reasoning? y
Enable logical inference? y

# Generate again with more analysis
```

## Commands & Shortcuts

### During Input
- `help` - Show contextual help
- `back` - Go to previous step
- `exit` - Exit interactive mode
- `[Enter]` - Accept default value

### During Results
- `1-6` - Select action from menu
- `s` - Save/export results
- `c` - Copy idea to clipboard
- `b` - Bookmark interesting ideas

## Best Practices

### 1. Start Broad, Then Narrow
```
Round 1: "Healthcare innovation"
Round 2: "Healthcare innovation" + "For rural areas"
Round 3: "Healthcare innovation" + "For rural areas" + "Using existing infrastructure"
```

### 2. Experiment with Temperature
- **Conservative**: When you need practical, implementable ideas
- **Balanced**: For general brainstorming
- **Creative**: When exploring new possibilities
- **Wild**: For breakthrough thinking

### 3. Use Refinement Effectively
```
Initial: "Education technology"
See results...
Refine: Add "For special needs students"
See results...
Refine: Add "Under $100 per student"
```

### 4. Combine Features Strategically
- Start with basic generation
- Add enhanced reasoning for deeper analysis
- Enable multi-dimensional eval for comprehensive scoring
- Use logical inference for complex problem-solving

## Example Sessions

### Product Innovation Session
```
Theme: Smart home devices
Constraints: For seniors
Temperature: Creative
Features: Enhanced reasoning + Multi-dimensional eval

After results...
Refine: Add "No app required"
Try temperature: Conservative (for practical variants)
```

### Research Brainstorming
```
Theme: Climate change solutions
Constraints: Local community level
Temperature: Wild
Features: All enabled

After results...
Select promising idea
Refine: Focus on that specific approach
Temperature: Balanced (for implementation ideas)
```

## Tips & Tricks

### Navigation
- Use defaults (press Enter) for quick setup
- Type `back` if you make a mistake
- Results stay in memory during session

### Exploration Strategies
1. **Divergent → Convergent**: Start wild, then constrain
2. **Domain Transfer**: Take ideas from one field to another
3. **Constraint Stacking**: Add one constraint at a time
4. **Temperature Ladder**: Try all temperatures on best ideas

### Session Management
- Export interesting results before major changes
- Bookmark ideas for later remix
- Use verbose mode for debugging
- Save session log: `python cli.py --interactive > session.log`

## Advanced Techniques

### 1. Idea Evolution
```
Round 1: Generate base ideas
Round 2: Pick best idea as new theme
Round 3: Add "improved version of [idea]"
Round 4: Combine top 2 ideas
```

### 2. Comparative Analysis
```
Same theme, different constraints:
- "Budget: unlimited" vs "Budget: $1000"
- "Timeline: 1 year" vs "Timeline: 1 month"
- "Users: experts" vs "Users: beginners"
```

### 3. Cross-Pollination
```
Theme 1: Get ideas for "Urban farming"
Theme 2: Get ideas for "IoT sensors"
Theme 3: Combine: "IoT sensors for urban farming"
```

## Troubleshooting

### Stuck in a Loop?
- Type `exit` to quit
- Type `back` to go back
- Press Ctrl+C for emergency exit

### Not Getting Good Ideas?
- Try different temperature
- Make constraints more specific
- Remove conflicting constraints
- Enable enhanced features

### Session Crashed?
- Results auto-save to `interactive_session_backup.json`
- Restart and load: `python cli.py --interactive --resume`