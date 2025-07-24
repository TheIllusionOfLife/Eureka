# Testing Context Handover

## Current System State (Phase 2 Complete)

### What You're Testing

The **MadSpark Multi-Agent System** is a sophisticated AI-powered idea generation and evaluation platform that has just completed Phase 2 development. The system uses Google's Gemini API to coordinate multiple specialized agents.

### Core Components

1. **Four Specialized Agents**:
   - **IdeaGenerator**: Creates innovative ideas based on themes/constraints
   - **Critic**: Evaluates feasibility and identifies potential issues
   - **Advocate**: Champions ideas and highlights benefits
   - **Skeptic**: Provides constructive skepticism and improvement suggestions

2. **Reasoning Engine** (Phase 2 Addition):
   - Context-aware conversations with memory
   - Logical inference chains with formal reasoning
   - Multi-dimensional evaluation across 7 criteria
   - Confidence scoring and consistency analysis

3. **User Interfaces**:
   - **CLI**: Full-featured command-line interface
   - **Interactive Mode**: Real-time conversational interface
   - **Web UI**: React frontend with WebSocket updates
   - **Batch Processing**: CSV/JSON input for multiple themes

### Key Features to Test

#### 1. Temperature Control
- Affects creativity vs. consistency trade-off
- Presets: conservative (0.3), balanced (0.5), creative (0.7), wild (1.0)
- Stage-specific temperatures for each agent

#### 2. Enhanced Reasoning
- `--enhanced-reasoning`: Enables context-aware agent responses
- `--multi-dimensional-eval`: 7-dimension scoring system
- `--logical-inference`: Formal reasoning chains

#### 3. Bookmark System
- Persistent storage of interesting ideas
- Tag-based organization
- Remix functionality to combine bookmarked concepts

#### 4. Export Formats
- JSON: Complete structured data
- CSV: Tabular format for analysis
- Markdown: Human-readable documentation
- PDF: Professional reports (requires reportlab)

### Testing Your Custom Prompts

The system excels at:
1. **Complex Constraint Satisfaction**: Balancing multiple requirements
2. **Domain-Specific Innovation**: Adapting to specialized fields
3. **Practical Feasibility**: Grounding creative ideas in reality
4. **Cultural Sensitivity**: Considering diverse perspectives

Example custom prompt patterns:
```bash
# Technology + Social Impact
python cli.py "AI for social good" "must benefit underserved communities"

# Sustainability + Economics  
python cli.py "circular economy solutions" "profitable within 2 years"

# Innovation + Regulation
python cli.py "fintech innovation" "compliant with banking regulations"

# Local + Global
python cli.py "local food systems" "scalable to global markets"
```

### What Makes Good Test Cases

1. **Tension Between Requirements**: Constraints that create interesting trade-offs
2. **Specific Domains**: The more specific, the better the results
3. **Clear Success Criteria**: Measurable outcomes in constraints
4. **Open-Ended Possibilities**: Room for creative solutions

### Performance Expectations

With actual Gemini API:
- **Response Time**: 15-40 seconds per workflow
- **Token Usage**: ~10,000-30,000 tokens per workflow
- **Idea Quality**: Significantly better than mock mode
- **Reasoning Depth**: Detailed analysis with citations

### Advanced Testing Tips

1. **Compare Temperatures**: Run same prompt with different temperatures
2. **Test Edge Cases**: Contradictory constraints, highly technical domains
3. **Bookmark Patterns**: Save ideas that surprise or impress you
4. **Remix Experiments**: Combine disparate bookmarked ideas
5. **Batch Variations**: Create CSV with variations of similar themes

### System Behavior Notes

- **Conversation Memory**: Agents remember context within a session
- **Consistency Checking**: Logical inference identifies contradictions
- **Cultural Adaptation**: Agents consider Japanese cultural context
- **Failure Modes**: Gracefully handles API errors with retries

### Redis Caching (Optional)

If Redis is running:
- Second runs of identical queries return instantly
- Workflow results cached for 24 hours
- Cache key includes theme, constraints, and temperature

### Monitoring Your Testing

1. **Console Output**: Detailed progress for each agent
2. **Export Files**: Check `exports/` directory
3. **Bookmarks**: Stored in `.bookmarks/bookmarks.json`
4. **Web UI**: Real-time progress at http://localhost:3000

### Quick Health Check

```bash
# Verify everything is working
cd mad_spark_multiagent
python -c "
import sys
import os
print('Python:', sys.version)
print('API Key Set:', bool(os.environ.get('GOOGLE_API_KEY')))
print('Working Dir:', os.getcwd())
print('✅ Ready to test!' if os.path.exists('coordinator.py') else '❌ Wrong directory')
"
```

### Interesting Test Scenarios

1. **Paradoxical Constraints**:
   ```bash
   python cli.py "privacy-preserving social media" "completely transparent"
   ```

2. **Future Technology**:
   ```bash
   python cli.py "quantum computing applications" "usable by non-physicists"
   ```

3. **Social Innovation**:
   ```bash
   python cli.py "reducing loneliness in cities" "without technology"
   ```

4. **Environmental Challenge**:
   ```bash
   python cli.py "carbon capture" "profitable without subsidies"
   ```

### What to Look For

- **Idea Originality**: Are the ideas surprising or predictable?
- **Reasoning Quality**: Is the logic sound and well-explained?
- **Constraint Satisfaction**: Do ideas meet all requirements?
- **Practical Viability**: Could these ideas actually work?
- **Agent Collaboration**: Do agents build on each other's insights?

### After Testing

Your feedback is valuable for Phase 3 planning:
- Which features were most useful?
- What workflows felt natural?
- Where did the system surprise you?
- What additional capabilities would help?

---

*The system is production-ready and should handle your custom prompts well. Enjoy exploring what MadSpark can create with your ideas!*