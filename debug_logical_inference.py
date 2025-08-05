#!/usr/bin/env python3
"""Debug script to check logical inference initialization."""
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and test
from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.agents.genai_client import get_genai_client

print("=== Debugging Logical Inference Initialization ===\n")

# Test 1: Check if genai_client can be obtained
print("1. Testing get_genai_client():")
try:
    client = get_genai_client()
    print(f"   ✓ GenAI client obtained: {client is not None}")
    print(f"   Type: {type(client).__name__ if client else 'None'}")
except Exception as e:
    print(f"   ✗ Error getting client: {e}")
    client = None

# Test 2: Initialize ReasoningEngine without explicit client
print("\n2. Testing ReasoningEngine initialization (no explicit client):")
try:
    engine = ReasoningEngine()
    print(f"   ✓ ReasoningEngine created")
    print(f"   - logical_inference exists: {engine.logical_inference is not None}")
    print(f"   - logical_inference_engine exists: {engine.logical_inference_engine is not None}")
    
    if engine.logical_inference:
        print(f"   - logical_inference.genai_client: {engine.logical_inference.genai_client is not None}")
        print(f"   - logical_inference.inference_engine: {engine.logical_inference.inference_engine is not None}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Initialize ReasoningEngine with explicit client
print("\n3. Testing ReasoningEngine initialization (with explicit client):")
try:
    engine_with_client = ReasoningEngine(genai_client=client)
    print(f"   ✓ ReasoningEngine created with client")
    print(f"   - logical_inference_engine exists: {engine_with_client.logical_inference_engine is not None}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Check async coordinator logic
print("\n4. Testing async coordinator logic conditions:")
print(f"   - logical_inference=True: True")
print(f"   - engine exists: {engine is not None}")
print(f"   - engine.logical_inference_engine exists: {engine.logical_inference_engine is not None if engine else 'N/A'}")
print(f"   - Would run logical inference: {True and engine and engine.logical_inference_engine}")

print("\n=== Summary ===")
if client and engine and engine.logical_inference_engine:
    print("✅ Logical inference should work correctly!")
else:
    print("❌ Logical inference won't run due to missing components")
    if not client:
        print("   - No GenAI client available (check GOOGLE_API_KEY)")
    if engine and not engine.logical_inference_engine:
        print("   - Logical inference engine not created")