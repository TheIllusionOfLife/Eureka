#!/usr/bin/env python3
"""
MadSpark User Experience Demo - Interactive Mode
Run this to experience the full MadSpark system capabilities
"""

from enhanced_reasoning import ReasoningEngine, MultiDimensionalEvaluator
import json

def demo_basic_experience():
    """Basic user experience demonstration."""
    print("🚀 MadSpark Multi-Agent System - User Demo")
    print("=" * 50)
    
    # User would normally input these
    theme = "sustainable urban living"
    constraints = "budget-friendly, community-focused"
    temperature = 0.7
    
    print(f"🎯 Theme: {theme}")
    print(f"📋 Constraints: {constraints}")
    print(f"🌡️  Temperature: {temperature} (creativity level)")
    print()
    
    # Simulate the full workflow
    print("🤖 AI Agents Working...")
    print("   💡 Idea Generator: Creating innovative solutions...")
    print("   🔍 Critic Agent: Evaluating feasibility and impact...")
    print("   ✅ Advocate Agent: Highlighting benefits...")
    print("   ⚠️  Skeptic Agent: Identifying risks...")
    print()
    
    # Mock generated ideas (what the API would return)
    ideas = [
        "Community-owned solar energy cooperatives",
        "Vertical farming in abandoned buildings", 
        "Bike-sharing with smart locks and routes",
        "Neighborhood composting networks"
    ]
    
    print("💡 Generated Ideas:")
    for i, idea in enumerate(ideas, 1):
        print(f"   {i}. {idea}")
    print()
    
    # Enhanced Reasoning Analysis
    print("🧠 Enhanced Reasoning Analysis (Phase 2.1):")
    evaluator = MultiDimensionalEvaluator()
    
    for i, idea in enumerate(ideas[:2], 1):  # Analyze top 2
        print(f"\n--- Idea {i}: {idea} ---")
        
        evaluation = evaluator.evaluate_idea(idea, {
            'budget': 'community-level',
            'timeline': '12 months',
            'target_audience': 'urban residents'
        })
        
        print(f"📊 Overall Score: {evaluation['overall_score']:.1f}/10")
        print(f"   💰 Cost Effectiveness: {evaluation['dimension_scores']['cost_effectiveness']:.1f}/10")
        print(f"   🚀 Innovation Level: {evaluation['dimension_scores']['innovation']:.1f}/10") 
        print(f"   📈 Expected Impact: {evaluation['dimension_scores']['impact']:.1f}/10")
        print(f"   ⚡ Feasibility: {evaluation['dimension_scores']['feasibility']:.1f}/10")
        print(f"   📈 Scalability: {evaluation['dimension_scores']['scalability']:.1f}/10")
    
    print(f"\n🏆 Recommendation: {ideas[0]}")
    print(f"✨ This demonstrates the full MadSpark experience!")

def demo_temperature_effects():
    """Demonstrate temperature effects on creativity."""
    print("\n🌡️ Temperature Effects Demo")
    print("=" * 40)
    
    idea = "Smart city transportation"
    evaluator = MultiDimensionalEvaluator()
    
    temperatures = [
        (0.2, "Conservative", "Proven, safe solutions"),
        (0.5, "Balanced", "Good mix of creativity and feasibility"),
        (0.9, "Creative", "Highly innovative, experimental ideas")
    ]
    
    for temp, label, description in temperatures:
        print(f"\n🌡️ Temperature {temp} ({label}):")
        print(f"   📝 Style: {description}")
        
        # Simulate different creative levels
        if temp <= 0.3:
            sample_ideas = ["Electric bus routes", "Bike lane expansion"]
        elif temp <= 0.6:
            sample_ideas = ["Smart traffic lights with AI", "App-based ride sharing"]
        else:
            sample_ideas = ["Flying car networks", "Teleportation hubs"]
        
        print(f"   💡 Sample ideas: {', '.join(sample_ideas)}")

def demo_enhanced_reasoning():
    """Demonstrate Phase 2.1 enhanced reasoning capabilities."""
    print("\n🧠 Enhanced Reasoning Demo (Phase 2.1)")
    print("=" * 45)
    
    engine = ReasoningEngine()
    
    # Simulate conversation history
    conversation_history = [
        {"agent": "idea_generator", "output": "Solar-powered community centers"},
        {"agent": "critic", "output": "Score: 8, excellent sustainability"}
    ]
    
    current_input = {
        "agent": "advocate",
        "idea": "Solar-powered community centers with EV charging",
        "context": "Urban sustainability project"
    }
    
    result = engine.process_with_context(current_input, conversation_history)
    
    print(f"📊 Context Awareness Score: {result['context_awareness_score']:.2f}")
    print(f"🔗 Relevant Past Context: {len(result['relevant_contexts'])} items found")
    print(f"🧠 Reasoning Quality: Enhanced analysis complete")
    print("✨ This shows how agents learn from conversation history!")

if __name__ == "__main__":
    demo_basic_experience()
    demo_temperature_effects() 
    demo_enhanced_reasoning()
    
    print(f"\n🎮 Try These User Experiences:")
    print("1. Run: python cli.py --help")
    print("2. Run: python cli.py 'your theme' 'your constraints' --temperature 0.8")
    print("3. Experiment with different temperature values (0.1 to 1.0)")
    print("4. Try bookmark features: --bookmark-results")
    print("5. Use different output formats: --output-format json")