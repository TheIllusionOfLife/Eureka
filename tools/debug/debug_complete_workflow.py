#!/usr/bin/env python3
"""
Debug script to see the complete MadSpark multi-agent workflow step by step
"""

import os
import logging
import re

# Load environment variables first
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
except ImportError:
    pass

from agent_defs.idea_generator import generate_ideas
from agent_defs.critic import evaluate_ideas
from agent_defs.advocate import advocate_idea
from agent_defs.skeptic import criticize_idea

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def debug_complete_workflow():
    """Debug the complete MadSpark workflow step by step"""
    
    print("# 🔍 MadSpark Complete Multi-Agent Workflow Debug")
    print()
    
    # Test inputs
    topic = "earn money"
    constraints = "no illegal activities"
    
    print(f"**🎯 Topic:** {topic}")
    print(f"**📋 Constraints:** {constraints}")
    print()
    
    print("## 🚀 Multi-Agent Workflow Steps")
    print()
    
    try:
        # STEP 1: Idea Generation
        print("### 1️⃣ Idea Generator Agent (Temperature: 0.9)")
        print("**Purpose:** Generate diverse, creative ideas")
        print()
        
        raw_ideas = generate_ideas(topic=topic, context=constraints, temperature=0.9)
        
        # Parse ideas properly
        numbered_ideas = re.findall(r'^\d+\.\s+.*', raw_ideas, re.MULTILINE)
        
        print(f"**Generated:** {len(numbered_ideas)} numbered ideas")
        print("**Sample Ideas:**")
        for i, idea in enumerate(numbered_ideas[:3], 1):
            print(f"  {i}. {idea[:100]}...")
        print(f"  ... and {len(numbered_ideas) - 3} more ideas")
        print()
        
        # STEP 2: Critic Evaluation
        print("### 2️⃣ Critic Agent (Temperature: 0.3)")
        print("**Purpose:** Evaluate feasibility and assign scores")
        print()
        
        # Take first 3 ideas for detailed analysis
        sample_ideas = [idea.split('. ', 1)[1] for idea in numbered_ideas[:3]]
        
        ideas_string = "\n".join(sample_ideas)
        raw_evaluation = evaluate_ideas(
            ideas=ideas_string, 
            criteria="feasibility, innovation, profitability, market demand", 
            context=f"Theme: {topic}, Constraints: {constraints}",
            temperature=0.3
        )
        
        print(f"**Evaluated:** {len(sample_ideas)} ideas")
        print(f"**Evaluation Length:** {len(raw_evaluation)} characters")
        print("**Sample Evaluation:**")
        print(f"```\n{raw_evaluation[:300]}...\n```")
        print()
        
        # STEP 3: Advocate Analysis (for top idea)
        print("### 3️⃣ Advocate Agent (Temperature: 0.5)")
        print("**Purpose:** Build compelling case for best ideas")
        print()
        
        top_idea = sample_ideas[0]
        sample_critique = "High potential, scalable business model, leverages existing skills"
        
        raw_advocacy = advocate_idea(
            idea=top_idea,
            evaluation=sample_critique,
            context=f"Theme: {topic}, Constraints: {constraints}",
            temperature=0.5
        )
        
        print(f"**Advocating for:** {top_idea[:60]}...")
        print(f"**Advocacy Length:** {len(raw_advocacy)} characters")
        print("**Sample Advocacy:**")
        print(f"```\n{raw_advocacy[:300]}...\n```")
        print()
        
        # STEP 4: Skeptic Analysis (for same idea)
        print("### 4️⃣ Skeptic Agent (Temperature: 0.5)")
        print("**Purpose:** Identify risks and challenges")
        print()
        
        raw_skepticism = criticize_idea(
            idea=top_idea,
            advocacy=sample_critique,
            context=f"Theme: {topic}, Constraints: {constraints}",
            temperature=0.5
        )
        
        print(f"**Skeptical analysis for:** {top_idea[:60]}...")
        print(f"**Skepticism Length:** {len(raw_skepticism)} characters")
        print("**Sample Skepticism:**")
        print(f"```\n{raw_skepticism[:300]}...\n```")
        print()
        
        # WORKFLOW SUMMARY
        print("## 📊 Complete Workflow Summary")
        print()
        print("| Agent | Temperature | Purpose | Output Length |")
        print("|-------|-------------|---------|---------------|")
        print(f"| 💡 Idea Generator | 0.9 | Creative brainstorming | {len(raw_ideas)} chars, {len(numbered_ideas)} ideas |")
        print(f"| 🔍 Critic | 0.3 | Analytical evaluation | {len(raw_evaluation)} chars |")
        print(f"| ✅ Advocate | 0.5 | Persuasive benefits | {len(raw_advocacy)} chars |")
        print(f"| ⚠️ Skeptic | 0.5 | Risk assessment | {len(raw_skepticism)} chars |")
        print()
        
        print("## 🎯 Agent Collaboration Flow")
        print()
        print("```")
        print("User Input → IdeaGenerator → [Ideas List]")
        print("                ↓")
        print("            Critic → [Scored Ideas]")
        print("                ↓")
        print("   ┌─── Advocate → [Benefits Analysis]")
        print("   │")
        print("   └─── Skeptic → [Risk Analysis]")
        print("                ↓")
        print("          [Final Output]")
        print("```")
        print()
        
        print("## ✅ Debug Complete")
        print(f"Successfully traced the complete multi-agent workflow with {len(numbered_ideas)} generated ideas!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_complete_workflow()