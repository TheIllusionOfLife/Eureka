"""Data structures for the reasoning engine."""

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Any, TypedDict


class ReasoningConfig(TypedDict):
    """Configuration for the enhanced reasoning system."""
    memory_capacity: int
    inference_depth: int
    context_weight: float
    evaluation_dimensions: Dict[str, Dict[str, Any]]


@dataclass
class ContextData:
    """Structure for storing context information."""
    agent: str
    timestamp: str
    input_data: str
    output_data: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default="")
    
    def __post_init__(self):
        if not self.context_id:
            # Generate unique context ID based on content and timestamp
            content = f"{self.agent}_{self.input_data}_{self.output_data}_{self.timestamp}"
            self.context_id = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:12]


@dataclass
class InferenceStep:
    """Structure for a single step in logical inference."""
    premise: str
    conclusion: str
    confidence: float
    reasoning: str


@dataclass
class LogicalChain:
    """Structure for a complete logical inference chain."""
    steps: List[InferenceStep]
    overall_conclusion: str
    confidence_score: float
    validity_score: float
