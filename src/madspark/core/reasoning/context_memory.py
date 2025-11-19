"""Context Memory system for storing and retrieving agent context information."""

import datetime
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

from .types import ContextData

logger = logging.getLogger(__name__)


class ContextMemory:
    """Memory system for storing and retrieving agent context information."""
    
    def __init__(self, capacity: int = 1000):
        """Initialize context memory with specified capacity.
        
        Args:
            capacity: Maximum number of contexts to store
        """
        self.capacity = capacity
        self._contexts: Dict[str, ContextData] = {}
        self._agent_index: Dict[str, List[str]] = defaultdict(list)
        self._timestamp_index: List[tuple] = []  # (timestamp, context_id)
        
    def store_context(self, context_data: Dict[str, Any]) -> str:
        """Store context data and return unique context ID.
        
        Args:
            context_data: Dictionary containing context information
            
        Returns:
            Unique context ID for the stored data
        """
        # Create ContextData object
        timestamp = context_data.get('timestamp', datetime.datetime.now().isoformat())
        # Handle cases where 'agent' might not be present
        agent = context_data.get('agent', 'unknown')
        
        context = ContextData(
            agent=agent,
            timestamp=timestamp,
            input_data=context_data.get('input', context_data.get('content', '')),
            output_data=context_data.get('output', context_data.get('theme', '')),
            metadata=context_data.get('metadata', {})
        )
        
        # Check capacity and remove oldest if necessary
        if len(self._contexts) >= self.capacity:
            self._remove_oldest_context()
            
        # Store context
        self._contexts[context.context_id] = context
        self._agent_index[context.agent].append(context.context_id)
        self._timestamp_index.append((timestamp, context.context_id))
        self._timestamp_index.sort()  # Keep sorted by timestamp
        
        logger.debug(f"Stored context {context.context_id} for agent {context.agent}")
        return context.context_id
        
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve context by ID.
        
        Args:
            context_id: Unique context identifier
            
        Returns:
            Context data dictionary or None if not found
        """
        context = self._contexts.get(context_id)
        if context:
            return {
                'agent': context.agent,
                'timestamp': context.timestamp,
                'input': context.input_data,
                'output': context.output_data,
                'metadata': context.metadata
            }
        return None
        
    def get_all_contexts(self) -> List[Dict[str, Any]]:
        """Get all stored contexts.
        
        Returns:
            List of all context data dictionaries
        """
        return [self.get_context(ctx_id) for ctx_id in self._contexts.keys()]
        
    def search_by_agent(self, agent_name: str) -> List[Dict[str, Any]]:
        """Search contexts by agent name.
        
        Args:
            agent_name: Name of the agent to search for
            
        Returns:
            List of contexts from the specified agent
        """
        context_ids = self._agent_index.get(agent_name, [])
        return [self.get_context(ctx_id) for ctx_id in context_ids if ctx_id in self._contexts]
        
    def find_similar_contexts(self, query: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Find contexts similar to the query string.
        
        Args:
            query: Query string to search for
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar contexts above the threshold
        """
        query_words = set(query.lower().split())
        similar_contexts = []
        
        for context in self._contexts.values():
            # Combine input and output for similarity comparison
            content = f"{context.input_data} {context.output_data}".lower()
            content_words = set(content.split())
            
            # Calculate Jaccard similarity
            intersection = query_words.intersection(content_words)
            union = query_words.union(content_words)
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                if similarity >= threshold:
                    context_dict = self.get_context(context.context_id)
                    if context_dict:
                        context_dict['similarity_score'] = similarity
                        similar_contexts.append(context_dict)
                        
        # Sort by similarity score (highest first)
        similar_contexts.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_contexts
        
    def _remove_oldest_context(self):
        """Remove the oldest context to make room for new ones."""
        if self._timestamp_index:
            _, oldest_context_id = self._timestamp_index.pop(0)
            if oldest_context_id in self._contexts:
                context = self._contexts[oldest_context_id]
                del self._contexts[oldest_context_id]
                # Remove from agent index
                if context.agent in self._agent_index:
                    self._agent_index[context.agent] = [
                        ctx_id for ctx_id in self._agent_index[context.agent] 
                        if ctx_id != oldest_context_id
                    ]
