#!/usr/bin/env python3
"""Test the web interface fixes with real API key."""
import requests
import json
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API endpoint
BASE_URL = "http://localhost:8000"

def test_web_interface():
    """Test the web interface with logical inference and enhanced reasoning."""
    print("=== Testing Web Interface Fixes ===\n")
    
    # Test data
    request_data = {
        "theme": "AI-powered education tools",
        "constraints": "Budget-friendly for schools",
        "num_top_candidates": 2,
        "temperature_preset": "balanced",
        "enhanced_reasoning": True,
        "multi_dimensional_eval": True,
        "logical_inference": True,  # This is the key test
        "verbose": True,
        "show_detailed_results": True,
        "structured_output": False
    }
    
    print("1. Sending request with logical_inference=True...")
    print(f"   Theme: {request_data['theme']}")
    print(f"   Constraints: {request_data['constraints']}")
    print(f"   Logical Inference: {request_data['logical_inference']}")
    print(f"   Enhanced Reasoning: {request_data['enhanced_reasoning']}")
    
    try:
        # Send request
        response = requests.post(
            f"{BASE_URL}/api/generate-ideas",
            json=request_data,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n2. Response received successfully!")
            print(f"   Status: {result.get('status')}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            
            # Check results
            results = result.get('results', [])
            print(f"\n3. Analyzing {len(results)} results:")
            
            for i, res in enumerate(results):
                print(f"\n   Result {i+1}:")
                print(f"   - Idea: {res.get('idea', '')[:60]}...")
                
                # Check float scores
                initial_score = res.get('initial_score', 0)
                improved_score = res.get('improved_score', 0)
                print(f"   - Initial Score: {initial_score} (type: {type(initial_score).__name__})")
                print(f"   - Improved Score: {improved_score} (type: {type(improved_score).__name__})")
                
                # Check for logical inference
                if 'logical_inference' in res:
                    li = res['logical_inference']
                    print(f"   - ✓ Logical Inference Present!")
                    print(f"     - Confidence: {li.get('confidence', 'N/A')}")
                    print(f"     - Has inference: {'inference' in li}")
                    print(f"     - Has chain: {'inference_chain' in li and len(li.get('inference_chain', [])) > 0}")
                    print(f"     - Has improvements: {'improvements' in li}")
                    
                    # Check confidence threshold
                    confidence = li.get('confidence', 0)
                    print(f"     - Confidence {confidence} >= 0.0: {confidence >= 0.0}")
                else:
                    print(f"   - ✗ No Logical Inference Found!")
                
                # Verify float scores are not 0.0
                if isinstance(initial_score, float) and initial_score > 0:
                    print(f"   - ✓ Float scores working correctly!")
                elif initial_score == 0.0:
                    print(f"   - ✗ Score is 0.0 - bug may still exist!")
            
            # Summary
            print("\n4. Summary:")
            float_scores_ok = all(
                res.get('initial_score', 0) > 0 and 
                isinstance(res.get('initial_score', 0), (int, float))
                for res in results
            )
            logical_inference_present = any('logical_inference' in res for res in results)
            
            print(f"   - Float scores working: {'✓' if float_scores_ok else '✗'}")
            print(f"   - Logical inference present: {'✓' if logical_inference_present else '✗'}")
            
            if float_scores_ok and logical_inference_present:
                print("\n✅ Both fixes verified working!")
            else:
                print("\n❌ Issues detected - check the output above")
                
        else:
            print(f"\n✗ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n✗ Request timed out after 300 seconds")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    test_web_interface()