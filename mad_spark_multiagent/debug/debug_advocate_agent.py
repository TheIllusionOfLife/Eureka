#!/usr/bin/env python3
"""
Debug script to see how the Advocate Agent works in detail
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

from agent_defs.advocate import advocate_idea

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_advocate_agent():
    """Debug the Advocate Agent with sample evaluated ideas"""
    
    print("# 🔍 MadSpark Debug: Advocate Agent Analysis")
    print()
    
    # Sample evaluated idea (what Critic would produce)
    sample_evaluated_idea = {
        "idea": "Micro-Learning Platform Creator: Identify a niche skill and create a platform offering 5-15 minute focused lessons. Charge a subscription or per-lesson fee.",
        "score": 8,
        "critique": "Strong market demand for micro-learning, scalable business model, leverages expertise effectively."
    }
    
    theme = "earn money"
    constraints = "no illegal activities"
    temperature = 0.5  # Balanced temperature for persuasive advocacy
    
    print(f"**🎯 Theme:** {theme}")
    print(f"**📋 Constraints:** {constraints}")
    print(f"**🌡️ Temperature:** {temperature} (balanced persuasion)")
    print()
    
    print("## 📝 Sample Evaluated Idea for Advocacy")
    print(f"**Idea:** {sample_evaluated_idea['idea']}")
    print(f"**Score:** {sample_evaluated_idea['score']}/10")
    print(f"**Critique:** {sample_evaluated_idea['critique']}")
    print()
    
    try:
        # Call the advocate agent
        print("## 🤖 Calling Advocate Agent...")
        raw_advocacy = advocate_idea(
            idea=sample_evaluated_idea['idea'],
            evaluation=sample_evaluated_idea['critique'],
            context=f"Theme: {theme}, Constraints: {constraints}",
            temperature=temperature
        )
        
        print(f"**📝 Raw Response Length:** {len(raw_advocacy)} characters")
        print()
        
        # Parse the advocacy (like coordinator does)
        advocacy_lines = [line.strip() for line in raw_advocacy.split("\n") if line.strip()]
        
        print(f"**📊 Advocacy Lines Parsed:** {len(advocacy_lines)} lines")
        print()
        
        print("## 📋 All Advocacy Lines")
        for i, line in enumerate(advocacy_lines, 1):
            print(f"{i:2d}. {line}")
        
        print(f"\n## ✅ Debug Summary")
        print(f"- **Input idea score:** {sample_evaluated_idea['score']}/10")
        print(f"- **Advocacy lines:** {len(advocacy_lines)} lines")
        print(f"- **Temperature used:** {temperature} (balanced persuasion)")
        print(f"- **Advocacy purpose:** Build compelling case for the idea")
        
        # Show the COMPLETE raw response
        print(f"\n## 🔧 Complete Raw Advocate Response ({len(raw_advocacy)} characters)")
        print("```")
        print(raw_advocacy)
        print("```")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_advocate_agent()