#!/usr/bin/env python3
"""Quick test script to avoid CLI timeouts in testing.

This script demonstrates how to use the MadSpark system programmatically
to avoid command-line timeout issues.
"""
import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coordinator import run_multistep_workflow
from temperature_control import TemperatureManager
from enhanced_reasoning import ReasoningEngine


def quick_test(theme="AI innovation", constraints="Simple test", num_candidates=1):
    """Run a quick test of the MadSpark system."""
    print(f"\n🚀 Running MadSpark Quick Test at {datetime.now()}")
    print(f"Theme: {theme}")
    print(f"Constraints: {constraints}")
    print(f"Candidates: {num_candidates}\n")
    
    # Initialize temperature manager
    temp_manager = TemperatureManager.from_preset("balanced")
    
    # Initialize reasoning engine
    reasoning_engine = ReasoningEngine()
    
    try:
        # Run the workflow
        results = run_multistep_workflow(
            theme=theme,
            constraints=constraints,
            num_top_candidates=num_candidates,
            enable_novelty_filter=True,
            novelty_threshold=0.8,
            temperature_manager=temp_manager,
            verbose=True,
            enhanced_reasoning=True,
            multi_dimensional_eval=True,
            logical_inference=False,
            reasoning_engine=reasoning_engine
        )
        
        # Display results
        print(f"\n✅ Generated {len(results)} ideas successfully!\n")
        
        for i, result in enumerate(results, 1):
            print(f"Idea {i}:")
            print(f"  Title: {result.get('idea', 'N/A')[:100]}...")
            print(f"  Score: {result.get('initial_score', 0)}")
            if result.get('improved_idea'):
                print(f"  Improved: Yes")
                print(f"  New Score: {result.get('improved_score', 0)}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Allow command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick test for MadSpark system")
    parser.add_argument("--theme", default="AI innovation", help="Theme for idea generation")
    parser.add_argument("--constraints", default="Simple test", help="Constraints")
    parser.add_argument("--candidates", type=int, default=1, help="Number of candidates")
    
    args = parser.parse_args()
    
    exit_code = quick_test(
        theme=args.theme,
        constraints=args.constraints,
        num_candidates=args.candidates
    )
    
    sys.exit(exit_code)