"""Content safety utilities for MadSpark agents."""

import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..config.execution_constants import RetryConfig

logger = logging.getLogger(__name__)


@dataclass
class SafetyResult:
    """Result from content safety check."""
    is_safe: bool
    filtered_content: str
    safety_issues: List[str]
    confidence: float


class ContentSafetyFilter:
    """Content safety filter for AI-generated content."""
    
    def __init__(self):
        """Initialize content safety filter."""
        self.aggressive_patterns = [
            # Patterns that commonly trigger aggressive filtering
            r'\b(critical|severe|harsh|aggressive|attack|destroy|eliminate)\b',
            r'\b(dangerous|harmful|toxic|malicious|threatening)\b',
            r'\b(failure|disaster|catastrophe|crisis|emergency)\b',
        ]
        
        self.safe_replacements = {
            'critical': 'important',
            'severe': 'significant',
            'harsh': 'direct',
            'aggressive': 'assertive',
            'attack': 'challenge',
            'destroy': 'replace',
            'eliminate': 'remove',
            'dangerous': 'risky',
            'harmful': 'concerning',
            'toxic': 'problematic',
            'malicious': 'questionable',
            'threatening': 'challenging',
            'failure': 'setback',
            'disaster': 'challenge',
            'catastrophe': 'major issue',
            'crisis': 'situation',
            'emergency': 'urgent matter',
        }
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.aggressive_patterns]
    
    def sanitize_content(self, content: str) -> SafetyResult:
        """Sanitize content to reduce filtering triggers."""
        if not content:
            return SafetyResult(True, "", [], 1.0)
        
        filtered_content = content
        safety_issues = []
        
        # Replace aggressive language with gentler alternatives
        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            for match in matches:
                lower_match = match.lower()
                if lower_match in self.safe_replacements:
                    replacement = self.safe_replacements[lower_match]
                    filtered_content = re.sub(
                        rf'\b{re.escape(match)}\b',
                        replacement,
                        filtered_content,
                        flags=re.IGNORECASE
                    )
                    safety_issues.append(f"Replaced '{match}' with '{replacement}'")
        
        # Check if content is likely to be safe
        is_safe = len(safety_issues) == 0
        confidence = 1.0 - (len(safety_issues) * 0.1)
        
        return SafetyResult(
            is_safe=is_safe,
            filtered_content=filtered_content,
            safety_issues=safety_issues,
            confidence=max(0.0, confidence)
        )
    
    def create_safe_prompt(self, prompt: str) -> str:
        """Create a safety-optimized prompt."""
        # Add safety instructions
        safety_prefix = """Please provide constructive, professional feedback. Focus on opportunities for improvement rather than criticism. Use positive language and helpful suggestions."""
        
        # Sanitize the prompt
        safety_result = self.sanitize_content(prompt)
        
        # Combine safety prefix with sanitized prompt
        safe_prompt = f"{safety_prefix}\n\n{safety_result.filtered_content}"
        
        return safe_prompt


class GeminiSafetyHandler:
    """Specialized safety handler for Gemini 2.5-flash."""
    
    def __init__(self):
        """Initialize Gemini safety handler."""
        self.content_filter = ContentSafetyFilter()
        self.max_retries = RetryConfig.CONTENT_SAFETY_MAX_RETRIES
    
    def get_safety_settings(self):
        """Get optimized safety settings for Gemini 2.5-flash."""
        try:
            from google.genai import types
            return [
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_ONLY_HIGH"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_ONLY_HIGH"
                )
            ]
        except ImportError:
            logger.warning("Google GenAI types not available, using empty safety settings")
            return []
    
    def handle_generation_with_safety(self, client, model_name: str, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Handle content generation with safety retry logic."""
        safety_settings = self.get_safety_settings()
        
        for attempt in range(self.max_retries):
            try:
                # Sanitize prompt on each attempt
                safe_prompt = self.content_filter.create_safe_prompt(prompt)
                
                # Add safety settings to config
                generation_config = config.copy()
                if safety_settings:
                    generation_config['safety_settings'] = safety_settings
                
                # Attempt generation
                response = client.models.generate_content(
                    model=model_name,
                    contents=safe_prompt,
                    config=generation_config
                )
                
                if response and response.text:
                    logger.debug(f"Content generation successful on attempt {attempt + 1}")
                    return response.text
                else:
                    logger.warning(f"Empty response on attempt {attempt + 1}")
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                if "content" in error_msg and "filter" in error_msg:
                    logger.warning(f"Content filtering detected on attempt {attempt + 1}: {e}")
                    
                    # Try with even more conservative prompt
                    if attempt < self.max_retries - 1:
                        prompt = self._make_prompt_more_conservative(prompt)
                        logger.info(f"Retrying with more conservative prompt (attempt {attempt + 2})")
                        continue
                else:
                    logger.error(f"Generation error on attempt {attempt + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        raise
        
        logger.error(f"Content generation failed after {self.max_retries} attempts")
        return None
    
    def _make_prompt_more_conservative(self, prompt: str) -> str:
        """Make prompt more conservative to avoid filtering."""
        # Add more conservative language
        conservative_prefix = """Please provide gentle, constructive suggestions focusing on positive aspects and growth opportunities. Use diplomatic language and avoid any strong criticism."""
        
        # Remove potentially triggering words
        safety_result = self.content_filter.sanitize_content(prompt)
        
        # Combine with conservative instructions
        conservative_prompt = f"{conservative_prefix}\n\n{safety_result.filtered_content}"
        
        return conservative_prompt
    
    def test_content_filtering(self, client, model_name: str) -> Dict[str, Any]:
        """Test content filtering with various prompt types."""
        test_cases = [
            "Generate creative ideas for productivity improvement",
            "Provide critical analysis of market opportunities",
            "Suggest innovative solutions for challenging problems",
            "Evaluate potential risks and benefits of new technologies",
            "Create constructive feedback for business strategies"
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                result = self.handle_generation_with_safety(
                    client, model_name, test_case, {"temperature": 0.7}
                )
                results[test_case] = {
                    "success": result is not None,
                    "response_length": len(result) if result else 0,
                    "filtered": result is None
                }
            except Exception as e:
                results[test_case] = {
                    "success": False,
                    "error": str(e),
                    "filtered": "content" in str(e).lower()
                }
        
        return results


# Global safety handler instance
safety_handler = GeminiSafetyHandler()
content_filter = ContentSafetyFilter()


def safe_generate_content(client, model_name: str, prompt: str, config: Dict[str, Any]) -> Optional[str]:
    """Safely generate content with filtering protection."""
    return safety_handler.handle_generation_with_safety(client, model_name, prompt, config)


def sanitize_for_ai(content: str) -> str:
    """Sanitize content for AI processing."""
    result = content_filter.sanitize_content(content)
    return result.filtered_content