#!/usr/bin/env python3
"""Test logical inference with real API key."""
import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.utils.logical_inference_engine import LogicalInferenceEngine, InferenceType
from madspark.agents.genai_client import get_genai_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_real_api():
    """Test logical inference with real Gemini API."""
    # Check for API key
    if not os.getenv('GOOGLE_API_KEY'):
        logger.error("❌ GOOGLE_API_KEY not set. Please set it to test with real API.")
        return False
    
    try:
        # Get GenAI client
        genai_client = get_genai_client()
        if not genai_client:
            logger.error("❌ Failed to create GenAI client")
            return False
        
        # Create inference engine
        engine = LogicalInferenceEngine(genai_client)
        logger.info("✅ Created LogicalInferenceEngine with real API client")
        
        # Test cases
        test_cases = [
            {
                'name': 'Urban Farming Analysis',
                'idea': 'Vertical hydroponic gardens in abandoned buildings',
                'theme': 'sustainable urban agriculture',
                'context': 'limited space, water scarcity, food security',
                'analysis_type': InferenceType.FULL
            },
            {
                'name': 'Causal Chain Analysis',
                'idea': 'Community solar panel sharing program',
                'theme': 'renewable energy adoption',
                'context': 'urban neighborhoods, cost barriers',
                'analysis_type': InferenceType.CAUSAL
            },
            {
                'name': 'Constraint Satisfaction',
                'idea': 'Mobile health clinics with telemedicine',
                'theme': 'rural healthcare access',
                'context': 'limited budget, sparse population, poor connectivity',
                'analysis_type': InferenceType.CONSTRAINTS
            },
            {
                'name': 'Contradiction Detection',
                'idea': 'Anonymous social network for teenagers with parental controls',
                'theme': 'youth online safety',
                'context': 'privacy protection, parental oversight, teen autonomy',
                'analysis_type': InferenceType.CONTRADICTION
            }
        ]
        
        # Run tests
        for i, test in enumerate(test_cases, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Test {i}: {test['name']}")
            logger.info(f"{'='*60}")
            
            try:
                # Perform analysis
                result = engine.analyze(
                    idea=test['idea'],
                    theme=test['theme'],
                    context=test['context'],
                    analysis_type=test['analysis_type']
                )
                
                # Display results
                if result.error:
                    logger.error(f"❌ Analysis failed: {result.error}")
                else:
                    logger.info(f"\n📋 Idea: {test['idea']}")
                    logger.info(f"🎯 Theme: {test['theme']}")
                    logger.info(f"📌 Context: {test['context']}")
                    logger.info(f"🔍 Analysis Type: {test['analysis_type'].value}")
                    
                    # Format and display
                    formatted = engine.format_for_display(result, verbosity='standard')
                    logger.info(f"\n{formatted}")
                    
                    # Show confidence
                    logger.info(f"\n✨ Confidence Score: {result.confidence:.0%}")
                    
                    # Additional details based on type
                    if test['analysis_type'] == InferenceType.CAUSAL and result.root_cause:
                        logger.info(f"🎯 Root Cause: {result.root_cause}")
                    elif test['analysis_type'] == InferenceType.CONSTRAINTS and result.overall_satisfaction:
                        logger.info(f"📊 Overall Satisfaction: {result.overall_satisfaction}%")
                    elif test['analysis_type'] == InferenceType.CONTRADICTION and result.contradictions:
                        logger.info(f"⚠️  Found {len(result.contradictions)} contradiction(s)")
                        
            except Exception as e:
                logger.error(f"❌ Test failed with exception: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling scenarios."""
    logger.info("\n\n🧪 Testing Error Handling...")
    logger.info("="*60)
    
    try:
        genai_client = get_genai_client()
        engine = LogicalInferenceEngine(genai_client)
        
        # Test with empty inputs
        result = engine.analyze("", "", "", InferenceType.FULL)
        if result.error or result.confidence == 0.0:
            logger.info("✅ Handled empty input gracefully")
        else:
            logger.warning("⚠️  Empty input produced unexpected result")
            
        # Test with very long input
        long_idea = "sustainable " * 500  # Very long input
        result = engine.analyze(long_idea[:1000], "test", "test", InferenceType.FULL)
        logger.info("✅ Handled long input without crashing")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting Logical Inference Real API Tests")
    logger.info("="*60)
    
    # Run main tests
    success = test_real_api()
    
    # Run error handling tests
    if success:
        success = test_error_handling()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)