"""Agent Conversation Tracker for analyzing conversation flow."""

import datetime
import hashlib
from typing import Dict, List, Any, Optional


class AgentConversationTracker:
    """Tracks and analyzes agent conversation history."""
    
    def __init__(self):
        """Initialize conversation tracker."""
        self.history: List[Dict[str, Any]] = []
        self.agent_sequence: List[str] = []
        
    def add_interaction(self, interaction: Dict[str, Any]) -> str:
        """Add an interaction to the conversation history.
        
        Args:
            interaction: Dictionary containing interaction data
            
        Returns:
            Unique interaction ID
        """
        timestamp = interaction.get('timestamp', datetime.datetime.now().isoformat())
        agent = interaction.get('agent', 'unknown')
        
        # Generate ID
        content = f"{agent}_{timestamp}_{len(self.history)}"
        interaction_id = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]
        
        entry = {
            'id': interaction_id,
            'timestamp': timestamp,
            'agent': agent,
            'data': interaction
        }
        
        self.history.append(entry)
        self.agent_sequence.append(agent)
        
        return interaction_id
        
    def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Get interaction by ID.
        
        Args:
            interaction_id: Unique interaction identifier
            
        Returns:
            Interaction data or None if not found
        """
        for entry in self.history:
            if entry['id'] == interaction_id:
                return entry
        return None
        
    def analyze_conversation_flow(self) -> Dict[str, Any]:
        """Analyze the flow and patterns of the conversation.
        
        Returns:
            Dictionary containing flow analysis results
        """
        if not self.history:
            return {'status': 'empty', 'completeness': 0.0}
            
        analysis = {
            'total_interactions': len(self.history),
            'unique_agents': list(set(self.agent_sequence)),
            'sequence': self.agent_sequence,
            'duration': self._calculate_conversation_duration(),
            'patterns': self._identify_conversation_patterns(self.agent_sequence)
        }
        
        # Check for standard workflow completion
        # Standard flow: idea_generator -> critic -> advocate -> skeptic -> improver
        required_agents = {'idea_generator', 'critic', 'advocate', 'skeptic'}
        present_agents = set(self.agent_sequence)
        completeness = len(present_agents.intersection(required_agents)) / len(required_agents)
        
        analysis['workflow_completeness'] = completeness
        analysis['missing_agents'] = list(required_agents - present_agents)
        
        return analysis
        
    def extract_relevant_context(self, query: str, max_contexts: int = 5) -> List[Dict[str, Any]]:
        """Extract relevant context from conversation history.
        
        Args:
            query: Query string to find relevant context for
            max_contexts: Maximum number of contexts to return
            
        Returns:
            List of relevant interaction contexts
        """
        # Simple keyword matching for now
        query_words = set(query.lower().split())
        scored_contexts = []
        
        for entry in self.history:
            data = entry['data']
            content = f"{data.get('input', '')} {data.get('output', '')}".lower()
            content_words = set(content.split())
            
            # Jaccard similarity
            intersection = query_words.intersection(content_words)
            union = query_words.union(content_words)
            
            if union:
                score = len(intersection) / len(union)
                if score > 0.1:  # Threshold
                    scored_contexts.append((score, entry))
                    
        # Sort by score
        scored_contexts.sort(key=lambda x: x[0], reverse=True)
        
        return [ctx[1] for ctx in scored_contexts[:max_contexts]]
        
    def _identify_conversation_patterns(self, agent_sequence: List[str]) -> Dict[str, Any]:
        """Identify patterns in agent conversation sequence."""
        patterns = {
            'loops': self._find_agent_loops(agent_sequence),
            'interruptions': self._find_workflow_interruptions(agent_sequence),
            'sequential_adherence': self._check_sequential_workflow(agent_sequence)
        }
        return patterns
        
    def _check_sequential_workflow(self, agent_sequence: List[str]) -> float:
        """Check if agents follow expected sequential workflow."""
        expected_order = ['idea_generator', 'critic', 'advocate', 'skeptic', 'improver']
        score = 0.0
        
        # Check relative ordering
        last_idx = -1
        correct_transitions = 0
        total_transitions = 0
        
        for agent in expected_order:
            try:
                current_idx = agent_sequence.index(agent)
                if current_idx > last_idx:
                    correct_transitions += 1
                last_idx = current_idx
                total_transitions += 1
            except ValueError:
                continue
                
        return correct_transitions / total_transitions if total_transitions > 0 else 0.0
        
    def _find_agent_loops(self, agent_sequence: List[str]) -> List[Dict[str, Any]]:
        """Find loops where agents repeat in sequence."""
        loops = []
        seen = {}
        
        for i, agent in enumerate(agent_sequence):
            if agent in seen:
                prev_idx = seen[agent]
                if i - prev_idx < 4:  # Short loop
                    loops.append({
                        'agent': agent,
                        'start': prev_idx,
                        'end': i,
                        'length': i - prev_idx
                    })
            seen[agent] = i
            
        return loops
        
    def _find_workflow_interruptions(self, agent_sequence: List[str]) -> List[int]:
        """Find interruptions in expected workflow."""
        interruptions = []
        # Logic to detect unexpected agent transitions would go here
        return interruptions
        
    def _calculate_conversation_duration(self) -> float:
        """Calculate duration of conversation in seconds."""
        if len(self.history) < 2:
            return 0.0
            
        start = datetime.datetime.fromisoformat(self.history[0]['timestamp'])
        end = datetime.datetime.fromisoformat(self.history[-1]['timestamp'])
        
        return (end - start).total_seconds()
