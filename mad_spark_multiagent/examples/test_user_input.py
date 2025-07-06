#!/usr/bin/env python3
"""
Test script to demonstrate MadSpark functionality with user input
"""

def mock_workflow_demo():
    """Demo the system with mock responses"""
    print("🚀 MadSpark Multi-Agent System - Test Mode")
    print("=" * 50)
    
    # Your input
    theme = "earn money"
    constraints = "no illegal activities"
    
    print(f"🎯 Theme: {theme}")
    print(f"📋 Constraints: {constraints}")
    print()
    
    # Mock responses that would come from the API
    mock_ideas = [
        {
            "idea": "Online tutoring platform for specialized skills",
            "feasibility": "High - leverages existing skills and remote work trends",
            "benefits": "Scalable, flexible schedule, helps others learn",
            "risks": "Market saturation, need for marketing"
        },
        {
            "idea": "Digital product creation (courses, templates, tools)",
            "feasibility": "Medium - requires upfront work but passive income potential",
            "benefits": "Scalable, automation possible, recurring revenue",
            "risks": "Time investment, market validation needed"
        }
    ]
    
    print("💡 Generated Ideas:")
    for i, idea in enumerate(mock_ideas, 1):
        print(f"\n{i}. {idea['idea']}")
        print(f"   ✅ Feasibility: {idea['feasibility']}")
        print(f"   🎯 Benefits: {idea['benefits']}")
        print(f"   ⚠️  Risks: {idea['risks']}")
    
    print(f"\n🎉 Generated {len(mock_ideas)} money-making ideas within legal constraints!")
    print("💡 To use with real API: Set your GOOGLE_API_KEY in .env file")

if __name__ == "__main__":
    mock_workflow_demo()