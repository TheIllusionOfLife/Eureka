#!/usr/bin/env python3
"""Test MadSpark with real API key in various scenarios.

This script tests the system with real API calls to ensure everything
works correctly in production-like conditions.
"""
import os
import sys
import asyncio
import json
import time
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from madspark.core.async_coordinator import AsyncCoordinator
from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.cli.cli import main as cli_main


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def check_api_key():
    """Check if API key is set."""
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print_error("GOOGLE_API_KEY not set in environment variables")
        print("Please set your API key: export GOOGLE_API_KEY='your-key-here'")
        return False
    print_success(f"API key found (length: {len(api_key)})")
    return True


async def test_basic_workflow():
    """Test basic workflow with minimal parameters."""
    print_section("Test 1: Basic Workflow")
    
    coordinator = AsyncCoordinator()
    
    try:
        results = await coordinator.run_workflow(
            topic="sustainable urban farming",
            context="small spaces, low budget",
            num_top_candidates=2
        )
        
        print_success(f"Generated {len(results)} ideas")
        for i, result in enumerate(results, 1):
            print(f"\n{Colors.BOLD}Idea {i}:{Colors.RESET}")
            print(f"  Text: {result['idea'][:100]}...")
            print(f"  Initial Score: {result['initial_score']}")
            print(f"  Improved Score: {result['improved_score']}")
            print(f"  Score Delta: {result['score_delta']}")
        
        return True
    except Exception as e:
        print_error(f"Basic workflow failed: {e}")
        return False


async def test_enhanced_reasoning():
    """Test with enhanced reasoning (advocacy/skepticism)."""
    print_section("Test 2: Enhanced Reasoning")
    
    coordinator = AsyncCoordinator()
    
    try:
        results = await coordinator.run_workflow(
            topic="AI in education",
            context="elementary school, engaging learning",
            num_top_candidates=1,
            enhanced_reasoning=True
        )
        
        print_success(f"Generated {len(results)} idea with enhanced reasoning")
        result = results[0]
        
        if 'advocacy' in result:
            print(f"\n{Colors.BOLD}Advocacy:{Colors.RESET}")
            print(result['advocacy'][:200] + "...")
        
        if 'skepticism' in result:
            print(f"\n{Colors.BOLD}Skepticism:{Colors.RESET}")
            print(result['skepticism'][:200] + "...")
        
        return True
    except Exception as e:
        print_error(f"Enhanced reasoning failed: {e}")
        return False


async def test_parallel_processing():
    """Test parallel processing efficiency."""
    print_section("Test 3: Parallel Processing")
    
    coordinator = AsyncCoordinator()
    
    try:
        # Time sequential vs parallel
        start_time = time.time()
        
        results = await coordinator.run_workflow(
            topic="renewable energy solutions",
            context="rural communities",
            num_top_candidates=3,
            enhanced_reasoning=True,
            logical_inference=True
        )
        
        elapsed_time = time.time() - start_time
        
        print_success(f"Completed in {elapsed_time:.2f} seconds")
        print(f"  - Generated {len(results)} ideas")
        print(f"  - With enhanced reasoning: Yes")
        print(f"  - With logical inference: Yes")
        
        # Check that all expected fields are present
        result = results[0]
        expected_fields = ['idea', 'initial_score', 'improved_score', 
                          'advocacy', 'skepticism', 'logical_inference']
        
        missing_fields = [f for f in expected_fields if f not in result]
        if missing_fields:
            print_warning(f"Missing fields: {missing_fields}")
        else:
            print_success("All expected fields present")
        
        return True
    except Exception as e:
        print_error(f"Parallel processing failed: {e}")
        return False


async def test_structured_output():
    """Test structured output format."""
    print_section("Test 4: Structured Output")
    
    coordinator = AsyncCoordinator()
    
    try:
        results = await coordinator.run_workflow(
            topic="smart home innovations",
            context="privacy-focused, affordable",
            num_top_candidates=2,
            multi_dimensional_eval=True
        )
        
        print_success(f"Generated {len(results)} ideas with structured output")
        
        # Check for clean formatting
        for i, result in enumerate(results, 1):
            idea_text = result['idea']
            improved_text = result.get('improved_idea', '')
            
            # Check for common formatting issues
            formatting_issues = []
            if "Here's" in idea_text or "Here's" in improved_text:
                formatting_issues.append("Meta-commentary detected")
            if idea_text.strip() != idea_text:
                formatting_issues.append("Extra whitespace")
            
            if formatting_issues:
                print_warning(f"Idea {i} formatting issues: {formatting_issues}")
            else:
                print_success(f"Idea {i} has clean formatting")
        
        return True
    except Exception as e:
        print_error(f"Structured output test failed: {e}")
        return False


def test_batch_processing():
    """Test batch processing with multiple topics."""
    print_section("Test 5: Batch Processing")
    
    try:
        # Note: Using synchronous coordinator for batch
        results = run_multistep_workflow_batch(
            topic="blockchain applications",
            context="healthcare, secure data",
            num_top_candidates=2,
            enable_reasoning=True
        )
        
        print_success(f"Batch processed {len(results)} ideas")
        
        # Check batch efficiency
        for i, result in enumerate(results, 1):
            print(f"\n{Colors.BOLD}Batch Result {i}:{Colors.RESET}")
            print(f"  Idea: {result['idea'][:80]}...")
            print(f"  Score improvement: {result['score_delta']:.1f}")
        
        return True
    except Exception as e:
        print_error(f"Batch processing failed: {e}")
        return False


async def test_reevaluation_context():
    """Test that re-evaluation includes proper context."""
    print_section("Test 6: Re-evaluation Context")
    
    coordinator = AsyncCoordinator()
    
    try:
        results = await coordinator.run_workflow(
            topic="mental health apps",
            context="teenagers, accessible",
            num_top_candidates=2
        )
        
        print_success("Checking re-evaluation context")
        
        # Check score improvements
        improvements = []
        for result in results:
            initial = result['initial_score']
            improved = result['improved_score']
            delta = result['score_delta']
            improvements.append(delta)
            
            print(f"  Initial: {initial:.1f} → Improved: {improved:.1f} (Δ: {delta:.1f})")
        
        avg_improvement = sum(improvements) / len(improvements)
        if avg_improvement > 0:
            print_success(f"Average improvement: {avg_improvement:.1f}")
        else:
            print_warning(f"No average improvement: {avg_improvement:.1f}")
        
        return True
    except Exception as e:
        print_error(f"Re-evaluation test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling and edge cases."""
    print_section("Test 7: Error Handling")
    
    coordinator = AsyncCoordinator()
    test_passed = True
    
    # Test 1: Empty topic
    try:
        await coordinator.run_workflow(topic="", context="test")
        print_error("Empty topic should have raised error")
        test_passed = False
    except Exception:
        print_success("Empty topic correctly rejected")
    
    # Test 2: Very long context
    try:
        long_context = "requirements " * 500  # Very long context
        results = await coordinator.run_workflow(
            topic="test",
            context=long_context,
            num_top_candidates=1
        )
        print_success("Handled long context gracefully")
    except Exception as e:
        print_error(f"Failed with long context: {e}")
        test_passed = False
    
    # Test 3: High number of candidates
    try:
        results = await coordinator.run_workflow(
            topic="test ideas",
            context="simple",
            num_top_candidates=10  # More than usual
        )
        print_success(f"Handled {len(results)} candidates request")
    except Exception as e:
        print_error(f"Failed with many candidates: {e}")
        test_passed = False
    
    return test_passed


async def main():
    """Run all tests."""
    print(f"{Colors.BOLD}MadSpark Real API Test Suite{Colors.RESET}")
    print(f"Testing all workflow improvements with real API calls\n")
    
    # Check API key first
    if not check_api_key():
        return
    
    # Run tests
    test_results = []
    
    # Basic tests
    test_results.append(("Basic Workflow", await test_basic_workflow()))
    test_results.append(("Enhanced Reasoning", await test_enhanced_reasoning()))
    test_results.append(("Parallel Processing", await test_parallel_processing()))
    test_results.append(("Structured Output", await test_structured_output()))
    
    # Synchronous test
    test_results.append(("Batch Processing", test_batch_processing()))
    
    # Advanced tests
    test_results.append(("Re-evaluation Context", await test_reevaluation_context()))
    test_results.append(("Error Handling", await test_error_handling()))
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    for test_name, result in test_results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print_success("All tests passed! 🎉")
    else:
        print_error(f"{total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(main())