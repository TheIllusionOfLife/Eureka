#!/usr/bin/env python3
"""
MadSpark Demo - Mock Mode Experience
This demonstrates the full user experience without requiring API keys.
"""

import json
from datetime import datetime
from enhanced_reasoning import ReasoningEngine, MultiDimensionalEvaluator

def simulate_user_session():
    """Simulate a complete user session with mock data."""
    print("🚀 Welcome to MadSpark Multi-Agent System (Demo Mode)")
    print("=" * 60)
    
    # User inputs (simulating what a user would type)
    theme = input("Enter your theme (or press Enter for 'smart cities'): ").strip()
    if not theme:
        theme = "smart cities"
    
    constraints = input("Enter constraints (or press Enter for 'budget-friendly, scalable'): ").strip()
    if not constraints:
        constraints = "budget-friendly, scalable"
    
    temperature = input("Enter temperature 0.1-1.0 (or press Enter for 0.7): ").strip()
    if not temperature:
        temperature = 0.7
    else:
        try:
            temperature = float(temperature)
            temperature = max(0.1, min(1.0, temperature))
        except:
            temperature = 0.7
    
    print(f"\n🎯 Generating ideas for: '{theme}'")
    print(f"📋 Constraints: '{constraints}'")
    print(f"🌡️  Temperature: {temperature}")
    print("\n" + "="*60)
    
    # Simulate idea generation (what would come from the API)
    mock_ideas = [
        f"AI-powered traffic optimization system for {theme}",
        f"Solar-powered public transport network in {theme}",
        f"Smart waste management using IoT sensors for {theme}",
        f"Citizen engagement app for {theme} planning"
    ]
    
    print("💡 Generated Ideas:")
    for i, idea in enumerate(mock_ideas, 1):
        print(f"   {i}. {idea}")
    
    # Simulate critic evaluation
    print("\n🔍 Critic Agent Evaluating...")
    evaluations = [
        {"idea": mock_ideas[0], "score": 8, "critique": "Highly feasible with existing technology"},
        {"idea": mock_ideas[1], "score": 7, "critique": "Good environmental impact, moderate implementation cost"},
        {"idea": mock_ideas[2], "score": 9, "critique": "Cost-effective and immediate impact possible"},
        {"idea": mock_ideas[3], "score": 6, "critique": "Important for democracy, but adoption challenges"}
    ]
    
    # Sort by score and take top 2
    top_candidates = sorted(evaluations, key=lambda x: x['score'], reverse=True)[:2]
    
    print("\n📊 Top Candidates Selected:")
    for i, candidate in enumerate(top_candidates, 1):
        print(f"   {i}. {candidate['idea']} (Score: {candidate['score']}/10)")
        print(f"      Critique: {candidate['critique']}")
    
    # Enhanced Reasoning Demo
    print("\n🧠 Enhanced Reasoning Analysis:")
    reasoning_engine = ReasoningEngine()
    evaluator = MultiDimensionalEvaluator()
    
    for i, candidate in enumerate(top_candidates, 1):
        print(f"\n--- Candidate {i}: Enhanced Analysis ---")
        
        # Multi-dimensional evaluation
        evaluation = evaluator.evaluate_idea(candidate['idea'], {
            'budget': 'medium',
            'timeline': '12 months',
            'target_audience': 'city residents'
        })
        
        print(f"📊 Overall Score: {evaluation['overall_score']:.1f}/10")
        print(f"💰 Cost Effectiveness: {evaluation['dimension_scores']['cost_effectiveness']:.1f}/10")
        print(f"🚀 Innovation: {evaluation['dimension_scores']['innovation']:.1f}/10")
        print(f"📈 Impact: {evaluation['dimension_scores']['impact']:.1f}/10")
        print(f"⚡ Feasibility: {evaluation['dimension_scores']['feasibility']:.1f}/10")
        
        # Simulate advocacy
        print(f"\n✅ Advocate Agent says:")
        advocacy_points = [
            f"This solution directly addresses {theme} challenges",
            f"Aligns perfectly with '{constraints}' requirements", 
            f"Could benefit thousands of city residents",
            f"Leverages proven technology for rapid deployment"
        ]
        for point in advocacy_points[:2]:
            print(f"   • {point}")
        
        # Simulate skepticism
        print(f"\n⚠️  Skeptic Agent warns:")
        skeptic_points = [
            "Implementation complexity may be underestimated",
            "Requires significant stakeholder coordination",
            "Privacy concerns need careful consideration",
            "Maintenance costs could escalate over time"
        ]
        for point in skeptic_points[:2]:
            print(f"   • {point}")
    
    # Final recommendation
    best_candidate = top_candidates[0]
    print(f"\n🏆 FINAL RECOMMENDATION")
    print("=" * 40)
    print(f"💡 Idea: {best_candidate['idea']}")
    print(f"📊 Score: {best_candidate['score']}/10")
    print(f"🎯 Why: {best_candidate['critique']}")
    
    # User interaction options
    print(f"\n🎮 What would you like to do next?")
    print("1. Generate more ideas with different temperature")
    print("2. Analyze specific idea in detail") 
    print("3. Save results to bookmark")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        print("🌡️ Temperature Effects:")
        print("• Low (0.1-0.3): Conservative, proven ideas")
        print("• Medium (0.4-0.7): Balanced creativity and feasibility") 
        print("• High (0.8-1.0): Highly creative, experimental ideas")
        print("\nTry running the demo again with a different temperature!")
        
    elif choice == "2":
        selected_idea = best_candidate['idea']
        print(f"\n🔬 Deep Analysis: {selected_idea}")
        detailed_eval = evaluator.evaluate_idea(selected_idea, {
            'budget': 'limited',
            'timeline': '6 months', 
            'regulatory_requirements': 'city approval needed'
        })
        print(f"📊 Detailed Scores:")
        for dim, score in detailed_eval['dimension_scores'].items():
            print(f"   {dim.replace('_', ' ').title()}: {score:.1f}/10")
        print(f"\n💬 Summary: {detailed_eval['evaluation_summary']}")
        
    elif choice == "3":
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bookmark_data = {
            "timestamp": timestamp,
            "theme": theme,
            "constraints": constraints,
            "temperature": temperature,
            "top_idea": best_candidate['idea'],
            "score": best_candidate['score']
        }
        print(f"\n💾 Bookmark saved!")
        print(f"📝 You can save this to a file:")
        print(json.dumps(bookmark_data, indent=2))
        
    print(f"\n✨ Thank you for trying MadSpark Multi-Agent System!")
    print(f"🚀 This demo showed Phase 1 + Phase 2.1 enhanced reasoning capabilities")

if __name__ == "__main__":
    simulate_user_session()