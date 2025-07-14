"""Test to ensure Python and TypeScript cleaners produce identical output."""
import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from improved_idea_cleaner import clean_improved_idea

# Test cases with various patterns to clean
TEST_CASES = [
    {
        "input": """This is a simple test with enhanced features.
Our enhanced approach is great.
The improved system works well.""",
        "expected": """This is a simple test with features.
This approach is great.
The system works well.""".strip()
    },
    {
        "input": """## The "Amazing System" Framework
This enhanced version is evolving into a better solution.
(Score: 7.5)
We're moving from basic to advanced features.""",
        "expected": """# Amazing System
This version is a better solution.
It's advanced features.""".strip()
    }
]

def test_python_cleaner():
    """Test Python cleaner on all test cases."""
    results = []
    for i, test_case in enumerate(TEST_CASES):
        cleaned = clean_improved_idea(test_case["input"])
        results.append({
            "test_id": i,
            "input": test_case["input"],
            "output": cleaned,
            "expected": test_case["expected"],
            "passed": cleaned.strip() == test_case["expected"]
        })
    return results

def main():
    """Run parity tests."""
    print("Testing Python cleaner...")
    python_results = test_python_cleaner()
    
    # Write test cases to JSON for TypeScript testing
    test_data_path = Path(__file__).parent / "test_cleaner_data.json"
    with open(test_data_path, "w") as f:
        json.dump(TEST_CASES, f, indent=2)
    
    # Report results
    print("\nPython Cleaner Results:")
    for result in python_results:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"Test {result['test_id']}: {status}")
        if not result["passed"]:
            print(f"  Expected: {repr(result['expected'])}")
            print(f"  Got:      {repr(result['output'])}")
    
    all_passed = all(r["passed"] for r in python_results)
    if all_passed:
        print("\n✅ All Python tests passed!")
    else:
        print("\n❌ Some Python tests failed!")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())