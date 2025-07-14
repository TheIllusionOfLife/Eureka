#!/usr/bin/env python3
"""
Performance Benchmarking Script for MadSpark Multi-Agent System

This script measures various performance metrics including:
- Response times for each agent
- Memory usage during workflow
- API call counts and patterns
- Cache hit rates (when Redis enabled)
"""
import time
import psutil
import json
import statistics
from datetime import datetime
from typing import Dict, List, Any
import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from coordinator import run_multistep_workflow
from async_coordinator import AsyncCoordinator
from cache_manager import CacheManager


class PerformanceBenchmark:
    """Benchmark performance of MadSpark system"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "scenarios": [],
            "summary": {}
        }
        self.process = psutil.Process()
        
    def measure_memory(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def benchmark_sync_workflow(self, theme: str, constraints: str, num_candidates: int = 2) -> Dict[str, Any]:
        """Benchmark synchronous workflow"""
        print(f"\n🔄 Benchmarking SYNC workflow: {theme}")
        
        start_time = time.time()
        start_memory = self.measure_memory()
        
        # Track API calls by monitoring logs
        api_calls = 0
        
        # Run workflow
        try:
            result = run_multistep_workflow(theme, constraints, num_candidates=num_candidates)
            success = True
            idea_count = len(result.get("results", []))
        except Exception as e:
            print(f"Error in sync workflow: {e}")
            success = False
            idea_count = 0
            result = {}
        
        end_time = time.time()
        end_memory = self.measure_memory()
        
        metrics = {
            "type": "sync",
            "theme": theme,
            "success": success,
            "total_time": end_time - start_time,
            "memory_delta": end_memory - start_memory,
            "idea_count": idea_count,
            "time_per_idea": (end_time - start_time) / idea_count if idea_count > 0 else None
        }
        
        print(f"  ✅ Total time: {metrics['total_time']:.2f}s")
        print(f"  💾 Memory delta: {metrics['memory_delta']:.2f}MB")
        print(f"  📝 Ideas generated: {idea_count}")
        
        return metrics
    
    async def benchmark_async_workflow(self, theme: str, constraints: str, num_candidates: int = 2) -> Dict[str, Any]:
        """Benchmark asynchronous workflow"""
        print(f"\n⚡ Benchmarking ASYNC workflow: {theme}")
        
        start_time = time.time()
        start_memory = self.measure_memory()
        
        # Run async workflow
        try:
            coordinator = AsyncCoordinator()
            result = await coordinator.run_workflow(
                theme=theme,
                constraints=constraints,
                num_candidates=num_candidates,
                timeout=120
            )
            success = True
            idea_count = len(result.get("results", []))
        except Exception as e:
            print(f"Error in async workflow: {e}")
            success = False
            idea_count = 0
            result = {}
        
        end_time = time.time()
        end_memory = self.measure_memory()
        
        metrics = {
            "type": "async",
            "theme": theme,
            "success": success,
            "total_time": end_time - start_time,
            "memory_delta": end_memory - start_memory,
            "idea_count": idea_count,
            "time_per_idea": (end_time - start_time) / idea_count if idea_count > 0 else None
        }
        
        print(f"  ✅ Total time: {metrics['total_time']:.2f}s")
        print(f"  💾 Memory delta: {metrics['memory_delta']:.2f}MB")
        print(f"  📝 Ideas generated: {idea_count}")
        
        return metrics
    
    def benchmark_cache_performance(self) -> Dict[str, Any]:
        """Benchmark cache performance if Redis is available"""
        print(f"\n💾 Testing cache performance...")
        
        try:
            cache_manager = CacheManager(enabled=True)
            
            # Test cache operations
            test_key = "benchmark_test_key"
            test_data = {"ideas": ["test1", "test2"], "timestamp": time.time()}
            
            # Write performance
            write_start = time.time()
            cache_manager.set(test_key, test_data)
            write_time = time.time() - write_start
            
            # Read performance
            read_start = time.time()
            cached_data = cache_manager.get(test_key)
            read_time = time.time() - read_start
            
            # Cache hit test
            hits = 0
            misses = 0
            for i in range(10):
                if cache_manager.get(f"{test_key}_{i}"):
                    hits += 1
                else:
                    misses += 1
            
            metrics = {
                "available": True,
                "write_time": write_time,
                "read_time": read_time,
                "hit_rate": hits / (hits + misses)
            }
            
            print(f"  ✅ Cache available")
            print(f"  📝 Write time: {write_time*1000:.2f}ms")
            print(f"  📖 Read time: {read_time*1000:.2f}ms")
            
        except Exception as e:
            print(f"  ❌ Cache not available: {e}")
            metrics = {"available": False}
        
        return metrics
    
    async def run_benchmarks(self):
        """Run all benchmarks"""
        print("🚀 Starting MadSpark Performance Benchmarks")
        print("=" * 50)
        
        # Test scenarios
        scenarios = [
            ("Simple idea", "Quick implementation", 1),
            ("Complex system", "Scalable and secure", 2),
            ("AI innovation", "Budget-friendly", 3)
        ]
        
        # Run sync benchmarks
        sync_times = []
        for theme, constraints, num_candidates in scenarios:
            metrics = self.benchmark_sync_workflow(theme, constraints, num_candidates)
            self.results["scenarios"].append(metrics)
            if metrics["success"] and metrics["total_time"]:
                sync_times.append(metrics["total_time"])
        
        # Run async benchmarks
        async_times = []
        for theme, constraints, num_candidates in scenarios:
            metrics = await self.benchmark_async_workflow(theme, constraints, num_candidates)
            self.results["scenarios"].append(metrics)
            if metrics["success"] and metrics["total_time"]:
                async_times.append(metrics["total_time"])
        
        # Test cache
        cache_metrics = self.benchmark_cache_performance()
        self.results["cache"] = cache_metrics
        
        # Calculate summary statistics
        if sync_times and async_times:
            speedup = statistics.mean(sync_times) / statistics.mean(async_times)
            self.results["summary"]["avg_sync_time"] = statistics.mean(sync_times)
            self.results["summary"]["avg_async_time"] = statistics.mean(async_times)
            self.results["summary"]["async_speedup"] = speedup
            
            print(f"\n📊 PERFORMANCE SUMMARY")
            print("=" * 50)
            print(f"Average sync time: {self.results['summary']['avg_sync_time']:.2f}s")
            print(f"Average async time: {self.results['summary']['avg_async_time']:.2f}s")
            print(f"Async speedup: {speedup:.2f}x")
        
        # Save results
        with open("benchmark_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to benchmark_results.json")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate a markdown report"""
        report = f"""# MadSpark Performance Benchmark Report

Generated: {self.results['timestamp']}

## Summary

- **Average Sync Time**: {self.results['summary'].get('avg_sync_time', 'N/A'):.2f}s
- **Average Async Time**: {self.results['summary'].get('avg_async_time', 'N/A'):.2f}s
- **Async Speedup**: {self.results['summary'].get('async_speedup', 'N/A'):.2f}x

## Cache Performance

- **Available**: {self.results['cache'].get('available', False)}
"""
        if self.results['cache'].get('available'):
            report += f"""- **Write Time**: {self.results['cache']['write_time']*1000:.2f}ms
- **Read Time**: {self.results['cache']['read_time']*1000:.2f}ms
"""

        report += "\n## Detailed Results\n\n"
        report += "| Type | Theme | Time (s) | Memory (MB) | Ideas | Time/Idea |\n"
        report += "|------|-------|----------|-------------|-------|----------|\n"
        
        for scenario in self.results['scenarios']:
            if scenario['success']:
                report += f"| {scenario['type']} | {scenario['theme'][:20]}... | "
                report += f"{scenario['total_time']:.2f} | "
                report += f"{scenario['memory_delta']:.2f} | "
                report += f"{scenario['idea_count']} | "
                report += f"{scenario['time_per_idea']:.2f} |\n" if scenario['time_per_idea'] else "N/A |\n"
        
        with open("benchmark_report.md", "w") as f:
            f.write(report)
        
        print(f"📄 Report saved to benchmark_report.md")


async def main():
    """Main entry point"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_benchmarks()


if __name__ == "__main__":
    # Note: This is a simplified benchmark focusing on basic metrics
    # In production, you'd want more comprehensive testing
    print("⚠️  This benchmark will make real API calls and may incur costs")
    print("⚠️  Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n❌ Benchmark cancelled")
        sys.exit(0)
    
    asyncio.run(main())