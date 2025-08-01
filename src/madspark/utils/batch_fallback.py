"""Fallback mechanisms for batch API calls when they fail.

This module provides fallback strategies when batch API calls fail,
ensuring the system continues to work even if batching is not available.
"""
import logging
from typing import List, Dict, Any, Callable

from madspark.utils.batch_monitor import get_batch_monitor


def batch_with_fallback(
    batch_func: Callable,
    fallback_func: Callable,
    items: List[Any],
    batch_type: str,
    *args,
    **kwargs
) -> List[Dict[str, Any]]:
    """Execute a batch function with fallback to individual processing.
    
    Args:
        batch_func: Function to call for batch processing
        fallback_func: Function to call for individual items if batch fails
        items: List of items to process
        batch_type: Type of batch operation for monitoring
        *args, **kwargs: Arguments to pass to both functions
        
    Returns:
        List of results from batch or fallback processing
    """
    monitor = get_batch_monitor()
    
    # Try batch processing first
    context = monitor.start_batch_call(batch_type, len(items))
    
    try:
        results = batch_func(items, *args, **kwargs)
        
        # Validate batch results
        if not isinstance(results, list) or len(results) != len(items):
            raise ValueError(f"Batch function returned invalid results: expected {len(items)} items, got {len(results) if isinstance(results, list) else 'non-list'}")
        
        # Record successful batch call
        monitor.end_batch_call(context, success=True)
        logging.info(f"Batch {batch_type}: Successfully processed {len(items)} items")
        return results
        
    except Exception as batch_error:
        logging.warning(f"[DEGRADED MODE] Batch {batch_type} failed: {batch_error}. Falling back to individual processing.")
        
        # Record failed batch call with fallback
        monitor.end_batch_call(
            context, 
            success=False, 
            error_message=str(batch_error),
            fallback_used=True
        )
        
        # Fallback to individual processing
        fallback_results = []
        
        # Start monitoring fallback calls
        fallback_context = monitor.start_batch_call(f"{batch_type}_fallback", len(items))
        
        try:
            for i, item in enumerate(items):
                try:
                    result = fallback_func(item, *args, **kwargs)
                    fallback_results.append({
                        "idea_index": i,
                        **result  # Merge result fields
                    })
                except Exception as item_error:
                    logging.error(f"Fallback {batch_type} failed for item {i}: {item_error}")
                    # Add placeholder result to maintain list alignment
                    fallback_results.append({
                        "idea_index": i,
                        "error": str(item_error),
                        "formatted": f"N/A ({batch_type} failed)"
                    })
            
            # Record successful fallback
            monitor.end_batch_call(fallback_context, success=True)
            logging.info(f"[DEGRADED MODE] Fallback {batch_type}: Processed {len(fallback_results)} items individually")
            return fallback_results
            
        except Exception as fallback_error:
            # Record failed fallback
            monitor.end_batch_call(
                fallback_context,
                success=False,
                error_message=str(fallback_error)
            )
            
            logging.error(f"[DEGRADED MODE] Both batch and fallback {batch_type} failed: {fallback_error}")
            
            # Return placeholder results to maintain system stability
            return [
                {
                    "idea_index": i,
                    "error": "[DEGRADED MODE] Both batch and fallback failed",
                    "formatted": f"[DEGRADED MODE] N/A ({batch_type} failed)"
                }
                for i in range(len(items))
            ]


def advocate_fallback(item: Dict[str, str], theme: str, temperature: float) -> Dict[str, Any]:
    """Fallback for individual advocate processing. [DEGRADED MODE]"""
    logging.warning("[DEGRADED MODE] Using individual advocate calls instead of batch processing")
    try:
        from madspark.agents.advocate import advocate_idea
        result = advocate_idea(
            idea=item["idea"],
            evaluation=item["evaluation"],
            context=theme,
            temperature=temperature
        )
        return {"formatted": result}
    except ImportError:
        logging.error("[DEGRADED MODE] advocate_idea import failed, using placeholder response")
        # If advocate_for_idea doesn't exist, create a basic response
        return {"formatted": f"[DEGRADED MODE]\nSTRENGTHS:\n• Addresses the theme: {theme}\n• Has potential for development"}


def skeptic_fallback(item: Dict[str, str], theme: str, temperature: float) -> Dict[str, Any]:
    """Fallback for individual skeptic processing. [DEGRADED MODE]"""
    logging.warning("[DEGRADED MODE] Using individual skeptic calls instead of batch processing")
    try:
        from madspark.agents.skeptic import criticize_idea
        result = criticize_idea(
            idea=item["idea"],
            advocacy=item["advocacy"],
            context=theme,
            temperature=temperature
        )
        return {"formatted": result}
    except ImportError:
        logging.error("[DEGRADED MODE] criticize_idea import failed, using placeholder response")
        # If criticize_idea doesn't exist, create a basic response
        return {"formatted": "[DEGRADED MODE]\nCRITICAL FLAWS:\n• Implementation challenges\n• Resource requirements need evaluation"}


def improve_fallback(item: Dict[str, str], theme: str, temperature: float) -> Dict[str, Any]:
    """Fallback for individual idea improvement. [DEGRADED MODE]"""
    logging.warning("[DEGRADED MODE] Using individual improve calls instead of batch processing")
    try:
        from madspark.agents.idea_generator import improve_idea
        result = improve_idea(
            original_idea=item["idea"],
            critique=item["critique"],
            advocacy_points=item["advocacy"],
            skeptic_points=item["skepticism"],
            theme=theme,
            temperature=temperature
        )
        return {"improved_idea": result}
    except Exception as e:
        logging.error(f"[DEGRADED MODE] Improve fallback failed: {e}, using placeholder response")
        # Return enhanced version of original idea
        return {"improved_idea": f"[DEGRADED MODE] Enhanced version: {item['idea']} (with improvements based on feedback)"}


def multi_dimensional_fallback(idea: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback for individual multi-dimensional evaluation. [DEGRADED MODE]"""
    logging.warning("[DEGRADED MODE] Using placeholder multi-dimensional evaluation instead of AI-powered evaluation")
    # Return basic evaluation scores
    return {
        "idea_index": 0,  # Will be overwritten by batch_with_fallback
        "feasibility": 6,
        "innovation": 7,
        "impact": 6,
        "cost_effectiveness": 5,
        "scalability": 6,
        "risk_assessment": 6,
        "timeline": 5,
        "overall_score": 6.0,
        "evaluation_summary": "[DEGRADED MODE] Fallback evaluation - basic scoring applied"
    }