#!/usr/bin/env python3
"""
Debug script to control the number of ideas generated
"""

import os
import logging

# Load environment variables first
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
except ImportError:
    pass

import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def generate_specific_number_of_ideas(topic: str, constraints: str, num_ideas: int = 10, temperature: float = 0.9):
    """Generate a specific number of ideas"""
    
    # Configure the API
    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GOOGLE_GENAI_MODEL", "gemini-2.0-flash")
    
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=(
            f"You are an expert idea generator. Generate exactly {num_ideas} diverse and creative ideas. "
            f"Present them as a numbered list with clear, actionable descriptions."
        )
    )
    
    # Custom prompt with specific number
    prompt = (
        f"Generate exactly {num_ideas} diverse and creative ideas on the topic of '{topic}'. "
        f"Constraints: {constraints}\n\n"
        f"Present your response as a numbered list (1. 2. 3. etc.) with exactly {num_ideas} items. "
        f"Each idea should be actionable and innovative.\n\nIdeas:"
    )
    
    generation_config = genai.types.GenerationConfig(temperature=temperature)
    response = model.generate_content(prompt, generation_config=generation_config)
    
    return response.text if response.text else ""

def debug_controlled_generation():
    """Test different numbers of ideas"""
    
    print("🎯 MadSpark Debug: Controlled Idea Generation")
    print("=" * 60)
    
    topic = "earn money"
    constraints = "no illegal activities"
    
    # Test different numbers
    for num_ideas in [5, 10, 20]:
        print(f"\n🔢 Requesting {num_ideas} ideas:")
        print("-" * 40)
        
        try:
            raw_response = generate_specific_number_of_ideas(
                topic=topic, 
                constraints=constraints, 
                num_ideas=num_ideas,
                temperature=0.9
            )
            
            # Parse the response
            parsed_ideas = [idea.strip() for idea in raw_response.split("\n") if idea.strip()]
            
            print(f"📊 Requested: {num_ideas}, Got: {len(parsed_ideas)} ideas")
            
            # Show first few ideas
            for i, idea in enumerate(parsed_ideas[:3], 1):
                print(f"   {i}. {idea[:80]}{'...' if len(idea) > 80 else ''}")
            
            if len(parsed_ideas) > 3:
                print(f"   ... and {len(parsed_ideas) - 3} more ideas")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_controlled_generation()