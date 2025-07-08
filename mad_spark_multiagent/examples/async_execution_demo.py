"""Demo of async agent execution (Phase 2.3)

This example demonstrates the performance benefits of async execution
by comparing synchronous vs asynchronous agent execution.
"""
import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from coordinator import run_multistep_workflow
from async_coordinator import run_async_workflow
from temperature_control import TemperatureManager


async def main():
    """Run demonstration of async vs sync execution."""
    theme = "Sustainable Transportation Solutions"
    constraints = "Budget-friendly, implementable within 2 years, suitable for mid-size cities"
    num_candidates = 3
    
    # Create temperature manager
    temp_manager = TemperatureManager.from_preset('balanced')
    
    print("=" * 60)
    print("ASYNC AGENT EXECUTION DEMO - Phase 2.3")
    print("=" * 60)
    print(f"\nTheme: {theme}")
    print(f"Constraints: {constraints}")
    print(f"Number of top candidates: {num_candidates}")
    print("\n" + "=" * 60)
    
    # Progress callback for async execution
    async def progress_callback(message: str, progress: float):
        print(f"[ASYNC {progress:3.0%}] {message}")
    
    # 1. Run SYNCHRONOUS workflow
    print("\n1. SYNCHRONOUS EXECUTION")
    print("-" * 40)
    sync_start = time.time()
    
    sync_results = run_multistep_workflow(
        theme=theme,
        constraints=constraints,
        num_top_candidates=num_candidates,
        temperature_manager=temp_manager,
        verbose=False
    )
    
    sync_duration = time.time() - sync_start
    print(f"✅ Synchronous execution completed in {sync_duration:.2f} seconds")
    print(f"   Generated {len(sync_results)} candidates")
    
    # 2. Run ASYNCHRONOUS workflow
    print("\n2. ASYNCHRONOUS EXECUTION")
    print("-" * 40)
    async_start = time.time()
    
    async_results = await run_async_workflow(
        theme=theme,
        constraints=constraints,
        num_top_candidates=num_candidates,
        temperature_manager=temp_manager,
        verbose=False,
        progress_callback=progress_callback,
        max_concurrent_agents=5  # Limit concurrency for demo
    )
    
    async_duration = time.time() - async_start
    print(f"✅ Asynchronous execution completed in {async_duration:.2f} seconds")
    print(f"   Generated {len(async_results)} candidates")
    
    # 3. Compare results
    print("\n3. PERFORMANCE COMPARISON")
    print("-" * 40)
    speedup = sync_duration / async_duration if async_duration > 0 else 0
    print(f"Synchronous time:  {sync_duration:.2f}s")
    print(f"Asynchronous time: {async_duration:.2f}s")
    print(f"Speedup factor:     {speedup:.2f}x")
    if sync_duration > 0:
        print(f"Time saved:         {sync_duration - async_duration:.2f}s ({(1 - async_duration/sync_duration)*100:.1f}%)")
    else:
        print(f"Time saved:         {sync_duration - async_duration:.2f}s")
    
    # 4. Display results
    print("\n4. TOP IDEAS GENERATED")
    print("-" * 40)
    for i, result in enumerate(async_results, 1):
        print(f"\n{i}. {result['idea']}")
        print(f"   Score: {result['initial_score']}/10")
        print(f"   Critique: {result['initial_critique'][:100]}...")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Benefits of Async Execution:")
    print("- ⚡ Parallel agent execution reduces overall runtime")
    print("- 📊 Real-time progress updates via callbacks")
    print("- 🔄 Better resource utilization")
    print("- 🚀 Scales better with multiple candidates")
    print("- ⏰ Significant time savings for larger workflows")


if __name__ == "__main__":
    # Run the async demo
    asyncio.run(main())