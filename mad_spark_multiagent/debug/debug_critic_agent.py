#!/usr/bin/env python3
"""
Debug script to see how the Critic Agent works in detail
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

from agent_defs.critic import evaluate_ideas

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_critic_agent():
    """Debug the Critic Agent with sample ideas"""
    
    print("# 🔍 MadSpark Debug: Critic Agent Analysis")
    print()
    
    # Sample ideas to evaluate (from idea generator output)
    sample_ideas = [
        "Micro-Learning Platform Creator: Identify a niche skill and create a platform offering 5-15 minute focused lessons. Charge a subscription or per-lesson fee.",
        "Personalized AI Prompt Engineer: Help individuals and businesses craft effective prompts for AI tools like ChatGPT or Midjourney.",
        "Digital Decluttering Service: Help people organize and delete unnecessary files, emails, and photos from their computers and devices.",
        "Ethical AI Art Creation Service: Offer AI-generated art services, ensuring that the AI models used are trained on ethically sourced data."
    ]
    
    theme = "earn money"
    constraints = "no illegal activities"
    temperature = 0.3  # Low temperature for analytical evaluation
    
    print(f"**🎯 Theme:** {theme}")
    print(f"**📋 Constraints:** {constraints}")
    print(f"**🌡️ Temperature:** {temperature} (analytical mode)")
    print(f"**📊 Ideas to Evaluate:** {len(sample_ideas)} ideas")
    print()
    
    print("## 📝 Sample Ideas Being Evaluated")
    for i, idea in enumerate(sample_ideas, 1):
        print(f"{i}. {idea}")
    print()
    
    try:
        # Call the critic agent
        print("## 🤖 Calling Critic Agent...")
        ideas_string = "\n".join(sample_ideas)
        raw_evaluation = evaluate_ideas(
            ideas=ideas_string, 
            criteria="feasibility, innovation, profitability, market demand", 
            context=f"Theme: {theme}, Constraints: {constraints}",
            temperature=temperature
        )
        
        print(f"**📝 Raw Response Length:** {len(raw_evaluation)} characters")
        print()
        
        # Parse the evaluation (like coordinator does)
        evaluation_lines = [line.strip() for line in raw_evaluation.split("\n") if line.strip()]
        
        print(f"**📊 Evaluation Lines Parsed:** {len(evaluation_lines)} lines")
        print()
        
        print("## 📋 All Evaluation Lines")
        for i, line in enumerate(evaluation_lines, 1):
            print(f"{i:2d}. {line}")
        
        print(f"\n## ✅ Debug Summary")
        print(f"- **Input ideas:** {len(sample_ideas)} ideas")
        print(f"- **Evaluation lines:** {len(evaluation_lines)} lines")
        print(f"- **Temperature used:** {temperature} (analytical)")
        
        # Show the COMPLETE raw response
        print(f"\n## 🔧 Complete Raw Critic Response ({len(raw_evaluation)} characters)")
        print("```")
        print(raw_evaluation)
        print("```")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_critic_agent()