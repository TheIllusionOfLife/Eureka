#!/usr/bin/env python3
"""
Debug script to see ALL generated ideas before filtering
"""

import os
import logging

# Load environment variables first
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
except ImportError:
    pass

from agent_defs.idea_generator import generate_ideas

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_idea_generation():
    """Generate ideas and show all raw output for debugging"""
    
    print("# 🔍 MadSpark Debug: All Generated Ideas")
    print()
    
    # Your test inputs
    topic = "earn money"
    constraints = "no illegal activities"
    temperature = 0.9
    
    print(f"**🎯 Topic:** {topic}")
    print(f"**📋 Constraints:** {constraints}")
    print(f"**🌡️ Temperature:** {temperature}")
    print()
    
    try:
        # Generate ideas directly (same as coordinator does)
        print("## 🤖 Calling IdeaGenerator Agent...")
        raw_ideas = generate_ideas(topic=topic, context=constraints, temperature=temperature)
        
        print(f"**📝 Raw Response Length:** {len(raw_ideas)} characters")
        print()
        
        # Parse ideas exactly like coordinator does (old method)
        old_parsed_ideas = [idea.strip() for idea in raw_ideas.split("\n") if idea.strip()]
        
        # Better parsing: count only numbered ideas (1. 2. 3. etc.)
        import re
        numbered_ideas = re.findall(r'^\d+\.\s+.*', raw_ideas, re.MULTILINE)
        
        print(f"**💡 Old Parsing Method:** {len(old_parsed_ideas)} items")
        print(f"**💡 Actual Numbered Ideas:** {len(numbered_ideas)} ideas")
        print()
        
        print("## 📋 All Parsed Items (Old Method)")
        for i, idea in enumerate(old_parsed_ideas, 1):
            print(f"{i:2d}. {idea}")
        
        print(f"\n## 🎯 Actual Numbered Ideas Only ({len(numbered_ideas)} ideas)")
        for i, idea in enumerate(numbered_ideas, 1):
            print(f"{i:2d}. {idea}")
        
        print(f"\n## ✅ Debug Summary")
        print(f"- **Old parsing found:** {len(old_parsed_ideas)} items")
        print(f"- **Actual numbered ideas:** {len(numbered_ideas)} ideas")
        print(f"- **Difference:** {len(old_parsed_ideas) - len(numbered_ideas)} non-idea items")
        
        # Show the COMPLETE raw response for debugging
        print(f"\n## 🔧 Complete Raw API Response ({len(raw_ideas)} characters)")
        print("```")
        print(raw_ideas)
        print("```")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_idea_generation()