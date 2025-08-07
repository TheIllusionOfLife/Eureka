"""Validation decorators for common agent input patterns.

This module provides decorators to standardize input validation across
all agent functions, reducing code duplication and ensuring consistency.
"""
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar
from types import SimpleNamespace

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def validate_agent_inputs(*required_fields: str, allow_empty: bool = False) -> Callable[[F], F]:
    """Decorator to validate common agent input parameters.
    
    Args:
        *required_fields: Names of required fields to validate
        allow_empty: Whether to allow empty values for required fields
        
    Returns:
        Decorated function with input validation
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function parameters
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate required fields
            for field in required_fields:
                if field not in bound_args.arguments:
                    raise ValueError(f"Missing required field: {field}")
                
                value = bound_args.arguments[field]
                
                # Check for None values
                if value is None:
                    raise ValueError(f"Field '{field}' cannot be None")
                
                # Check for empty values if not allowed
                if not allow_empty:
                    if isinstance(value, str) and not value.strip():
                        raise ValueError(f"Field '{field}' cannot be empty")
                    elif isinstance(value, (list, dict)) and len(value) == 0:
                        raise ValueError(f"Field '{field}' cannot be empty")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_topic_context(func: F) -> F:
    """Decorator to validate topic and context parameters.
    
    This is the most common validation pattern across agent functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Extract topic and context from args/kwargs
        import inspect
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Validate topic
        topic = bound_args.arguments.get('topic')
        if not topic or (isinstance(topic, str) and not topic.strip()):
            raise ValueError("Topic is required and cannot be empty")
        
        # Validate context
        context = bound_args.arguments.get('context')
        if not context or (isinstance(context, str) and not context.strip()):
            raise ValueError("Context is required and cannot be empty")
        
        return func(*args, **kwargs)
    
    return wrapper


def validate_ideas_list(func: F) -> F:
    """Decorator to validate ideas list parameter."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import inspect
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Check for ideas parameter
        ideas = bound_args.arguments.get('ideas')
        if ideas is None:
            raise ValueError("Ideas list is required")
        
        if not isinstance(ideas, list):
            raise ValueError("Ideas must be a list")
        
        if len(ideas) == 0:
            raise ValueError("Ideas list cannot be empty")
        
        # Validate each idea
        for i, idea in enumerate(ideas):
            if not idea or (isinstance(idea, str) and not idea.strip()):
                raise ValueError(f"Idea at index {i} cannot be empty")
        
        return func(*args, **kwargs)
    
    return wrapper


def provide_mock_response(response_type: str, language_context: Optional[str] = None) -> Callable[[F], F]:
    """Decorator to provide mock responses when in mock mode.
    
    Args:
        response_type: Type of response to generate ('ideas', 'evaluation', 'advocacy', 'skepticism')
        language_context: Language context for response generation
        
    Returns:
        Decorated function that returns mock data in mock mode
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Check if we should use mock mode
            try:
                from ..agents.genai_client import get_mode
                is_mock = get_mode() == "mock"
            except ImportError:
                # Fallback to environment check
                import os
                is_mock = os.getenv("MADSPARK_MODE", "").lower() == "mock"
            
            if is_mock:
                return generate_mock_response(response_type, language_context, *args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def generate_mock_response(response_type: str, language_context: Optional[str], *args, **kwargs) -> Any:
    """Generate mock response based on response type.
    
    Args:
        response_type: Type of response to generate
        language_context: Language context for response
        *args, **kwargs: Function arguments for context
        
    Returns:
        Mock response appropriate for the response type
    """
    # Get language from kwargs if available
    language = "English"  # Default
    if 'topic' in kwargs and kwargs['topic']:
        # Simple language detection based on characters
        topic_text = str(kwargs['topic'])
        if any('\u4e00' <= char <= '\u9fff' for char in topic_text):
            language = "Chinese"
        elif any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in topic_text):
            language = "Japanese"
    
    mock_responses = {
        'ideas': _generate_mock_ideas(language, kwargs.get('topic', 'general topic')),
        'evaluation': _generate_mock_evaluation(language),
        'advocacy': _generate_mock_advocacy(language),
        'skepticism': _generate_mock_skepticism(language),
        'improvement': _generate_mock_improvement(language, kwargs.get('ideas', [])),
        'batch_ideas': _generate_mock_batch_ideas(language, kwargs.get('ideas', [])),
        'batch_evaluation': _generate_mock_batch_evaluation(language, kwargs.get('ideas', [])),
    }
    
    response = mock_responses.get(response_type, f"Mock response for {response_type}")
    logger.debug(f"Generated mock {response_type} response in {language}")
    return response


def _generate_mock_ideas(language: str, topic: str) -> List[str]:
    """Generate mock ideas list."""
    if language == "Chinese":
        return [
            f"关于{topic}的创新想法1：利用人工智能优化流程",
            f"关于{topic}的创新想法2：建立可持续发展模式",
            f"关于{topic}的创新想法3：整合跨领域资源"
        ]
    elif language == "Japanese":
        return [
            f"{topic}に関する革新的なアイデア1：AIを活用したプロセス最適化",
            f"{topic}に関する革新的なアイデア2：持続可能な発展モデルの構築",
            f"{topic}に関する革新的なアイデア3：分野横断的リソースの統合"
        ]
    else:
        return [
            f"Innovative idea 1 for {topic}: Leverage AI to optimize processes",
            f"Innovative idea 2 for {topic}: Build sustainable development model",
            f"Innovative idea 3 for {topic}: Integrate cross-domain resources"
        ]


def _generate_mock_evaluation(language: str) -> Dict[str, Any]:
    """Generate mock evaluation response."""
    if language == "Chinese":
        return {
            "score": 7.5,
            "feedback": "这个想法具有很强的创新性和实用性，建议进一步完善实施细节。",
            "strengths": ["创新性强", "市场潜力大", "技术可行"],
            "weaknesses": ["成本较高", "实施复杂", "风险存在"]
        }
    elif language == "Japanese":
        return {
            "score": 7.5,
            "feedback": "このアイデアは革新性と実用性に優れており、実装の詳細をさらに完善することをお勧めします。",
            "strengths": ["革新性が高い", "市場ポテンシャルが大きい", "技術的に実現可能"],
            "weaknesses": ["コストが高い", "実装が複雑", "リスクが存在"]
        }
    else:
        return {
            "score": 7.5,
            "feedback": "This idea shows strong innovation and practicality. Recommend further refining implementation details.",
            "strengths": ["High innovation", "Large market potential", "Technically feasible"],
            "weaknesses": ["High cost", "Complex implementation", "Risks exist"]
        }


def _generate_mock_advocacy(language: str) -> str:
    """Generate mock advocacy response."""
    if language == "Chinese":
        return "这个想法的核心优势：\n• 解决实际问题的创新方案\n• 具有广泛的应用前景\n• 技术实现相对成熟"
    elif language == "Japanese":
        return "このアイデアの核心的な利点：\n• 実際の問題を解決する革新的なソリューション\n• 幅広い応用の見通し\n• 技術実装が比較的成熟"
    else:
        return "Core advantages of this idea:\n• Innovative solution addressing real problems\n• Wide application prospects\n• Relatively mature technology implementation"


def _generate_mock_skepticism(language: str) -> str:
    """Generate mock skepticism response."""
    if language == "Chinese":
        return "需要考虑的关键问题：\n• 实施成本可能过高\n• 市场接受度存在不确定性\n• 技术挑战需要进一步验证"
    elif language == "Japanese":
        return "考慮すべき重要な問題：\n• 実施コストが高すぎる可能性\n• 市場受容性に不確実性が存在\n• 技術的課題にはさらなる検証が必要"
    else:
        return "Key concerns to consider:\n• Implementation costs may be too high\n• Market acceptance uncertainty exists\n• Technical challenges need further validation"


def _generate_mock_improvement(language: str, ideas: List[str]) -> List[str]:
    """Generate mock idea improvements."""
    if not ideas:
        ideas = ["sample idea"]
    
    improved = []
    for i, idea in enumerate(ideas[:3]):  # Limit to 3 ideas
        if language == "Chinese":
            improved.append(f"改进版想法{i+1}：{idea[:20]}... 的优化方案，结合最新技术趋势")
        elif language == "Japanese":
            improved.append(f"改良版アイデア{i+1}：{idea[:20]}... の最適化案、最新技術トレンドと結合")
        else:
            improved.append(f"Improved idea {i+1}: Enhanced version of '{idea[:20]}...' incorporating latest technology trends")
    
    return improved


def _generate_mock_batch_ideas(language: str, ideas: List[str]) -> List[List[str]]:
    """Generate mock batch ideas response."""
    return [_generate_mock_ideas(language, f"batch topic {i}") for i in range(len(ideas) or 3)]


def _generate_mock_batch_evaluation(language: str, ideas: List[str]) -> List[Dict[str, Any]]:
    """Generate mock batch evaluation response."""
    return [_generate_mock_evaluation(language) for _ in range(len(ideas) or 3)]


# Common validation combinations
def validate_standard_agent_inputs(func: F) -> F:
    """Standard validation for most agent functions (topic + context)."""
    return validate_topic_context(func)


def validate_batch_agent_inputs(func: F) -> F:
    """Standard validation for batch agent functions (ideas list)."""
    return validate_ideas_list(func)


def with_mock_fallback(response_type: str):
    """Convenience decorator combining validation and mock response."""
    def decorator(func: F) -> F:
        return provide_mock_response(response_type)(validate_standard_agent_inputs(func))
    return decorator