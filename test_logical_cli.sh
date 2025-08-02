#!/bin/bash
# Test logical inference through CLI

echo "🧪 Testing Logical Inference through CLI"
echo "======================================="

# Test 1: Basic logical inference
echo -e "\n📋 Test 1: Basic logical inference"
PYTHONPATH=src python -m madspark.cli.cli \
    "sustainable urban farming" \
    "limited space, water conservation" \
    --logical \
    --num-candidates 1 \
    --output-format detailed

echo -e "\n======================================="

# Test 2: Combined with enhanced reasoning
echo -e "\n📋 Test 2: Combined with enhanced reasoning"
PYTHONPATH=src python -m madspark.cli.cli \
    "renewable energy for communities" \
    "low income neighborhoods" \
    --enhanced \
    --logical \
    --num-candidates 1 \
    --output-format detailed

echo -e "\n======================================="

# Test 3: Multiple ideas with logical inference
echo -e "\n📋 Test 3: Multiple ideas comparison"
PYTHONPATH=src python -m madspark.cli.cli \
    "education technology" \
    "rural schools, limited internet" \
    --logical \
    --num-candidates 2 \
    --temperature-preset creative \
    --output-format summary

echo -e "\n✅ CLI tests completed!"