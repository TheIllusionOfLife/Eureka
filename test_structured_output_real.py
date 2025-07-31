#!/usr/bin/env python3
"""Test structured output with real API key."""
import os
import sys
sys.path.insert(0, 'src')

from madspark.agents.idea_generator import improve_idea

# Test data
original_idea = "Create a community solar panel sharing program where neighbors can share excess energy"
critique = "Score: 7/10. Good community focus but needs better tracking system and clearer cost-benefit model. Feasibility: 6/10 due to regulatory challenges."
advocacy_points = "• Strong community building potential\n• Reduces energy costs for participants\n• Promotes renewable energy adoption\n• Creates local green jobs"
skeptic_points = "• Complex regulatory hurdles\n• Initial setup costs are high\n• Requires sophisticated tracking software\n• Potential disputes over energy allocation"
theme = "sustainable urban living"

print("Testing structured output for idea improvement...")
print("=" * 60)

# Call improve_idea
result = improve_idea(
    original_idea=original_idea,
    critique=critique,
    advocacy_points=advocacy_points,
    skeptic_points=skeptic_points,
    theme=theme
)

print("IMPROVED IDEA:")
print("-" * 60)
print(result)
print("-" * 60)

# Check for meta-commentary
meta_phrases = [
    "improved version",
    "enhanced concept",
    "here's the",
    "based on feedback",
    "incorporating",
    "addressing concerns"
]

found_meta = []
for phrase in meta_phrases:
    if phrase in result.lower():
        found_meta.append(phrase)

if found_meta:
    print(f"\n⚠️  WARNING: Found meta-commentary phrases: {found_meta}")
else:
    print(f"\n✅ SUCCESS: No meta-commentary detected!")

print(f"\nCharacter count: {len(result)}")
print(f"First 50 chars: {result[:50]}...")