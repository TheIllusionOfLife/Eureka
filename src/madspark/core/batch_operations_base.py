"""Shared batch operations for all coordinators.

This module provides common batch processing functionality to eliminate
code duplication between async_coordinator.py and coordinator_batch.py.
"""
import asyncio
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

logger = logging.getLogger(__name__)

# Import batch functions registry
BATCH_FUNCTIONS = {}
try:
    from ..agents.advocate import advocate_ideas_batch
    from ..agents.skeptic import criticize_ideas_batch
    from ..agents.idea_generator import improve_ideas_batch
    
    BATCH_FUNCTIONS = {
        'advocate_ideas_batch': advocate_ideas_batch,
        'criticize_ideas_batch': criticize_ideas_batch,
        'improve_ideas_batch': improve_ideas_batch
    }
except ImportError as e:
    logger.error(f"Failed to import batch functions: {e}")
    BATCH_FUNCTIONS = {}


class BatchOperationsBase:
    """Base class providing common batch processing operations."""
    
    def __init__(self):
        """Initialize batch operations with thread pool executor."""
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def run_batch_with_timeout(
        self, 
        batch_func_name: str, 
        *args, 
        timeout: float = 60,
        is_async: bool = True
    ) -> Any:
        """Run a batch function with timeout protection.
        
        Args:
            batch_func_name: Name of the batch function
            *args: Arguments to pass to the batch function
            timeout: Timeout in seconds
            is_async: Whether to run async (True) or sync (False)
            
        Returns:
            Result from the batch function
            
        Raises:
            ValueError: If batch function is unknown
            asyncio.TimeoutError: If async operation times out
            concurrent.futures.TimeoutError: If sync operation times out
        """
        batch_func = BATCH_FUNCTIONS.get(batch_func_name)
        if not batch_func:
            raise ValueError(f"Unknown batch function: {batch_func_name}")
        
        if is_async:
            loop = asyncio.get_running_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, batch_func, *args),
                timeout=timeout
            )
        else:
            # Sync version for coordinator_batch.py
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(batch_func, *args)
                return future.result(timeout=timeout)
    
    def prepare_advocacy_input(self, candidates: List[Dict]) -> List[Dict]:
        """Prepare advocacy input from candidates.
        
        Args:
            candidates: List of candidate dictionaries with 'text' and 'critique' keys
            
        Returns:
            List of dictionaries formatted for advocacy batch processing
        """
        return [
            {"idea": c["text"], "evaluation": c["critique"]}
            for c in candidates
        ]
    
    def prepare_skepticism_input(self, candidates: List[Dict]) -> List[Dict]:
        """Prepare skepticism input from candidates.
        
        Args:
            candidates: List of candidate dictionaries with 'text' and optional 'advocacy' keys
            
        Returns:
            List of dictionaries formatted for skepticism batch processing
        """
        return [
            {
                "idea": c["text"], 
                "advocacy": c.get("advocacy", "N/A")
            }
            for c in candidates
        ]
    
    def prepare_improvement_input(self, candidates: List[Dict]) -> List[Dict]:
        """Prepare improvement input from candidates.
        
        Args:
            candidates: List of candidate dictionaries with required and optional keys
            
        Returns:
            List of dictionaries formatted for improvement batch processing
        """
        return [
            {
                "idea": c["text"], 
                "critique": c["critique"],
                "advocacy": c.get("advocacy", "N/A"), 
                "skepticism": c.get("skepticism", "N/A")
            }
            for c in candidates
        ]
    
    def update_candidates_with_batch_results(
        self, 
        candidates: List[Dict], 
        batch_results: List[str], 
        result_key: str
    ) -> List[Dict]:
        """Update candidates with batch processing results.
        
        Args:
            candidates: List of candidate dictionaries to update
            batch_results: List of string results from batch processing
            result_key: Key name to store results in candidates
            
        Returns:
            Updated candidates list (modifies in place)
        """
        for i, (candidate, result) in enumerate(zip(candidates, batch_results)):
            if result and result.strip():
                candidate[result_key] = result.strip()
            else:
                logger.warning(f"Empty {result_key} result for candidate {i+1}")
                candidate[result_key] = f"No {result_key} generated"
        return candidates
    
    def update_candidates_with_formatted_batch_results(
        self,
        candidates: List[Dict],
        batch_results: List[Dict],
        result_key: str
    ) -> List[Dict]:
        """Update candidates with formatted batch processing results.
        
        This handles the structured format returned by batch functions that includes
        'formatted' field and other metadata.
        
        Args:
            candidates: List of candidate dictionaries to update
            batch_results: List of dict results from batch processing (with 'formatted' field)
            result_key: Key name to store results in candidates
            
        Returns:
            Updated candidates list (modifies in place)
        """
        # Use enumerate to avoid data loss if API returns fewer results
        for i, candidate in enumerate(candidates):
            if i < len(batch_results):
                result = batch_results[i]
                if isinstance(result, dict) and "formatted" in result:
                    candidate[result_key] = result["formatted"]
                elif isinstance(result, str):
                    candidate[result_key] = result
                else:
                    logger.warning(f"Unexpected result format for candidate {i+1}: {type(result)}")
                    candidate[result_key] = "N/A (Unexpected format)"
            else:
                logger.warning(f"{result_key.title()} result missing for candidate {i+1}")
                candidate[result_key] = "N/A (No result from batch API)"
        return candidates
    
    def update_candidates_with_improvement_results(
        self,
        candidates: List[Dict],
        batch_results: List[Dict],
        result_key: str = "improved_idea"
    ) -> List[Dict]:
        """Update candidates with improvement batch processing results.
        
        This handles the specific format returned by improvement batch functions
        where the result key is 'improved_idea' and fallback is the original text.
        
        Args:
            candidates: List of candidate dictionaries to update
            batch_results: List of dict results from improvement batch processing
            result_key: Key name to store results in candidates (default: 'improved_idea')
            
        Returns:
            Updated candidates list (modifies in place)
        """
        # Use enumerate to avoid data loss if API returns fewer results
        for i, candidate in enumerate(candidates):
            if i < len(batch_results):
                result = batch_results[i]
                if isinstance(result, dict) and "improved_idea" in result:
                    candidate[result_key] = result["improved_idea"]
                elif isinstance(result, dict) and "formatted" in result:
                    candidate[result_key] = result["formatted"]
                elif isinstance(result, str):
                    candidate[result_key] = result
                else:
                    # Fallback to original text for improvement
                    candidate[result_key] = candidate["text"]
            else:
                logger.warning(f"Improvement result missing for candidate {i+1}")
                candidate[result_key] = candidate["text"]  # Fallback to original
        return candidates