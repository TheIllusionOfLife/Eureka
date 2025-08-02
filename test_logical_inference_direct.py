#!/usr/bin/env python3
"""Direct test of logical inference functionality."""
import sys
sys.path.insert(0, 'src')

from madspark.core.enhanced_reasoning import ReasoningEngine
from madspark.agents.genai_client import get_genai_client
from madspark.utils.logical_inference_engine import InferenceType

def test_logical_inference():
    """Test logical inference directly."""
    print("Testing logical inference...")
    
    # Create ReasoningEngine with GenAI client
    try:
        genai_client = get_genai_client()
        print(f"✓ GenAI client created: {genai_client is not None}")
        
        config = {"use_logical_inference": True}
        engine = ReasoningEngine(config=config, genai_client=genai_client)
        print(f"✓ ReasoningEngine created")
        print(f"✓ Has logical_inference_engine: {engine.logical_inference_engine is not None}")
        
        # Test the logical inference engine directly
        if engine.logical_inference_engine:
            idea = "Solar-powered water purification systems for rural communities"
            theme = "renewable energy"
            context = "affordable solutions"
            
            print(f"\nTesting analysis on idea: {idea[:50]}...")
            result = engine.logical_inference_engine.analyze(
                idea=idea,
                theme=theme,
                context=context,
                analysis_type=InferenceType.FULL
            )
            
            print(f"✓ Analysis complete")
            print(f"  Result type: {type(result)}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
            
            # Check each attribute safely
            causal_chain = getattr(result, 'causal_chain', None)
            print(f"  Causal chain: {type(causal_chain)} - {causal_chain}")
            
            constraint_analysis = getattr(result, 'constraint_analysis', None)
            print(f"  Constraint analysis: {type(constraint_analysis)} - {constraint_analysis}")
            
            contradictions = getattr(result, 'contradictions', None) 
            print(f"  Contradictions: {type(contradictions)} - {contradictions}")
            
            implications = getattr(result, 'implications', None)
            print(f"  Implications: {type(implications)} - {implications}")
            
            # Check to_dict method
            result_dict = result.to_dict()
            print(f"\n  Result as dict keys: {list(result_dict.keys())}")
            
            # Test formatting
            formatted = engine.logical_inference_engine.format_for_display(
                result, 
                verbosity='standard'
            )
            print(f"\nFormatted output preview:")
            print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logical_inference()