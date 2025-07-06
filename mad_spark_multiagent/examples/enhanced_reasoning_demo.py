#!/usr/bin/env python3
"""Enhanced Reasoning Demo for MadSpark Multi-Agent System.

This demo showcases the Phase 2.1 enhanced reasoning capabilities including:
- Context-aware agents
- Multi-dimensional evaluation 
- Logical inference chains
- Agent memory and conversation tracking

Usage:
    python enhanced_reasoning_demo.py
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from coordinator import run_multistep_workflow
from enhanced_reasoning import ReasoningEngine
from temperature_control import TemperatureManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demo_basic_enhanced_reasoning():
    """Demonstrate basic enhanced reasoning capabilities."""
    print("="*80)
    print("🧠 ENHANCED REASONING DEMO: Basic Capabilities")
    print("="*80)
    
    # Initialize reasoning engine
    reasoning_engine = ReasoningEngine()
    
    # Create temperature manager for consistent creativity
    temp_manager = TemperatureManager.from_preset('balanced')
    
    # Run workflow with enhanced reasoning
    results = run_multistep_workflow(
        theme="Smart healthcare solutions",
        constraints="Cost-effective, accessible to rural areas",
        num_top_candidates=2,
        temperature_manager=temp_manager,
        enhanced_reasoning=True,
        reasoning_engine=reasoning_engine,
        verbose=True
    )
    
    print("\n🎯 RESULTS WITH ENHANCED REASONING:")
    for i, result in enumerate(results, 1):
        print(f"\n--- Idea {i} ---")
        print(f"Idea: {result['idea']}")
        print(f"Score: {result['initial_score']}")
        print(f"Enhanced Analysis: {result['initial_critique'][:200]}...")
    
    return results


def demo_multi_dimensional_evaluation():
    """Demonstrate multi-dimensional evaluation capabilities."""
    print("\n" + "="*80)
    print("📊 MULTI-DIMENSIONAL EVALUATION DEMO")
    print("="*80)
    
    # Initialize reasoning engine
    reasoning_engine = ReasoningEngine()
    
    # Create temperature manager for high creativity
    temp_manager = TemperatureManager.from_preset('creative')
    
    # Run workflow with multi-dimensional evaluation
    results = run_multistep_workflow(
        theme="Renewable energy innovations",
        constraints="Scalable, environmentally friendly",
        num_top_candidates=3,
        temperature_manager=temp_manager,
        enhanced_reasoning=True,
        multi_dimensional_eval=True,
        reasoning_engine=reasoning_engine,
        verbose=True
    )
    
    print("\n🎯 RESULTS WITH MULTI-DIMENSIONAL EVALUATION:")
    for i, result in enumerate(results, 1):
        print(f"\n--- Idea {i} (Multi-Dimensional Score: {result['initial_score']}) ---")
        print(f"Idea: {result['idea']}")
        print(f"Enhanced Analysis includes 7-dimension evaluation:")
        print(f"- Feasibility, Innovation, Impact, Cost-Effectiveness")
        print(f"- Scalability, Risk Assessment, Timeline")
        print(f"Analysis: {result['initial_critique'][:300]}...")
    
    return results


def demo_reasoning_comparison():
    """Compare standard vs enhanced reasoning results."""
    print("\n" + "="*80)
    print("⚖️  COMPARISON DEMO: Standard vs Enhanced Reasoning")
    print("="*80)
    
    theme = "Urban agriculture solutions"
    constraints = "Space-efficient, community-focused"
    temp_manager = TemperatureManager.from_preset('balanced')
    
    print("\n1️⃣ STANDARD REASONING:")
    standard_results = run_multistep_workflow(
        theme=theme,
        constraints=constraints,
        num_top_candidates=2,
        temperature_manager=temp_manager,
        enhanced_reasoning=False,
        verbose=False
    )
    
    print("\n2️⃣ ENHANCED REASONING WITH MULTI-DIMENSIONAL EVAL:")
    enhanced_results = run_multistep_workflow(
        theme=theme,
        constraints=constraints,
        num_top_candidates=2,
        temperature_manager=temp_manager,
        enhanced_reasoning=True,
        multi_dimensional_eval=True,
        verbose=False
    )
    
    print("\n📊 COMPARISON RESULTS:")
    print("\nSTANDARD REASONING:")
    for i, result in enumerate(standard_results, 1):
        print(f"  {i}. Score: {result['initial_score']} - {result['idea'][:60]}...")
    
    print("\nENHANCED REASONING:")
    for i, result in enumerate(enhanced_results, 1):
        print(f"  {i}. Score: {result['initial_score']} - {result['idea'][:60]}...")
        print(f"     Enhanced insights available in critique")
    
    return standard_results, enhanced_results


def demo_context_memory():
    """Demonstrate context memory and conversation tracking."""
    print("\n" + "="*80)
    print("🧠 CONTEXT MEMORY & CONVERSATION TRACKING DEMO")
    print("="*80)
    
    # Initialize reasoning engine
    reasoning_engine = ReasoningEngine()
    temp_manager = TemperatureManager.from_preset('balanced')
    
    # First conversation - establish context
    print("\n1️⃣ FIRST CONVERSATION: Establishing Context")
    first_results = run_multistep_workflow(
        theme="Educational technology",
        constraints="Interactive, accessible",
        num_top_candidates=2,
        temperature_manager=temp_manager,
        enhanced_reasoning=True,
        reasoning_engine=reasoning_engine,
        verbose=False
    )
    
    # Second conversation - should leverage context
    print("\n2️⃣ SECOND CONVERSATION: Leveraging Established Context")
    second_results = run_multistep_workflow(
        theme="EdTech for remote learning",
        constraints="Low bandwidth, mobile-friendly",
        num_top_candidates=2,
        temperature_manager=temp_manager,
        enhanced_reasoning=True,
        reasoning_engine=reasoning_engine,  # Same engine maintains context
        verbose=False
    )
    
    print("\n🧠 CONTEXT MEMORY DEMONSTRATION:")
    print("The reasoning engine maintains context between conversations.")
    print(f"Context memory capacity: {reasoning_engine.context_memory.capacity}")
    print(f"Stored contexts: {len(reasoning_engine.context_memory.contexts)}")
    
    return first_results, second_results


def main():
    """Run all enhanced reasoning demonstrations."""
    print("🚀 MADSPARK ENHANCED REASONING DEMONSTRATION SUITE")
    print("Phase 2.1 Capabilities Showcase")
    
    try:
        # Demo 1: Basic enhanced reasoning
        demo_basic_enhanced_reasoning()
        
        # Demo 2: Multi-dimensional evaluation
        demo_multi_dimensional_evaluation()
        
        # Demo 3: Comparison
        demo_reasoning_comparison()
        
        # Demo 4: Context memory
        demo_context_memory()
        
        print("\n" + "="*80)
        print("✅ ALL ENHANCED REASONING DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("🧠 Context-aware agent processing")
        print("📊 Multi-dimensional evaluation (7 dimensions)")
        print("🔗 Logical inference chains")
        print("💾 Agent memory and conversation tracking")
        print("⚖️  Enhanced vs standard reasoning comparison")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logging.error(f"Enhanced reasoning demo failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()