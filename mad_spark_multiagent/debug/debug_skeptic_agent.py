#!/usr/bin/env python3
"""
Debug script to see how the Skeptic Agent works in detail
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

from agent_defs.skeptic import criticize_idea

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_skeptic_agent():
    """Debug the Skeptic Agent with sample evaluated ideas"""
    
    print("# 🔍 MadSpark Debug: Skeptic Agent Analysis")
    print()
    
    # Sample evaluated idea (what Critic would produce)
    sample_evaluated_idea = {
        "idea": "Micro-Learning Platform Creator: Identify a niche skill and create a platform offering 5-15 minute focused lessons. Charge a subscription or per-lesson fee.",
        "score": 8,
        "critique": "Strong market demand for micro-learning, scalable business model, leverages expertise effectively."
    }
    
    theme = "earn money"
    constraints = "no illegal activities"
    temperature = 0.5  # Balanced temperature for realistic skepticism
    
    print(f"**🎯 Theme:** {theme}")
    print(f"**📋 Constraints:** {constraints}")
    print(f"**🌡️ Temperature:** {temperature} (balanced skepticism)")
    print()
    
    print("## 📝 Sample Evaluated Idea for Skeptical Analysis")
    print(f"**Idea:** {sample_evaluated_idea['idea']}")
    print(f"**Score:** {sample_evaluated_idea['score']}/10")
    print(f"**Critique:** {sample_evaluated_idea['critique']}")
    print()
    
    try:
        # Call the skeptic agent
        print("## 🤖 Calling Skeptic Agent...")
        # Note: Skeptic takes 'advocacy' as input, but we'll use the critique as a placeholder
        raw_skepticism = criticize_idea(
            idea=sample_evaluated_idea['idea'],
            advocacy=sample_evaluated_idea['critique'],
            context=f"Theme: {theme}, Constraints: {constraints}",
            temperature=temperature
        )
        
        print(f"**📝 Raw Response Length:** {len(raw_skepticism)} characters")
        print()
        
        # Parse the skepticism (like coordinator does)
        skepticism_lines = [line.strip() for line in raw_skepticism.split("\n") if line.strip()]
        
        print(f"**📊 Skepticism Lines Parsed:** {len(skepticism_lines)} lines")
        print()
        
        print("## 📋 All Skepticism Lines")
        for i, line in enumerate(skepticism_lines, 1):
            print(f"{i:2d}. {line}")
        
        print(f"\n## ✅ Debug Summary")
        print(f"- **Input idea score:** {sample_evaluated_idea['score']}/10")
        print(f"- **Skepticism lines:** {len(skepticism_lines)} lines")
        print(f"- **Temperature used:** {temperature} (balanced skepticism)")
        print(f"- **Skepticism purpose:** Identify risks and challenges")
        
        # Show the COMPLETE raw response
        print(f"\n## 🔧 Complete Raw Skeptic Response ({len(raw_skepticism)} characters)")
        print("```")
        print(raw_skepticism)
        print("```")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_skeptic_agent()