"""Output processing utilities for converting structured data to CLI-friendly format."""
import re
import shutil
from typing import Dict, Any, Optional

# Terminal output constants
TERMINAL_UI_RESERVE_LINES = 10
CONTINUATION_MESSAGE_LINES = 3
DEFAULT_TERMINAL_LINES = 24
DEFAULT_TERMINAL_COLS = 80
SECTION_BOUNDARY_SEARCH_LINES = 10


def convert_markdown_to_cli(text: str) -> str:
    """Convert markdown formatting to CLI-friendly format.
    
    Args:
        text: Markdown-formatted text
        
    Returns:
        CLI-friendly formatted text
    """
    if not text:
        return text
    
    # Convert markdown bullets to CLI bullets
    # First handle nested bullets (spaces or tabs, but not newlines)
    text = re.sub(r'^([ \t]+)\* ', lambda m: m.group(1) + '◦ ', text, flags=re.MULTILINE)
    # Then handle top-level bullets (no indentation)
    text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)
    
    # Convert markdown bold to uppercase (for terminal emphasis)
    text = re.sub(r'\*\*([^*]+)\*\*', lambda m: m.group(1).upper(), text)
    
    # Remove any remaining markdown syntax
    text = re.sub(r'#+\s*', '', text)  # Headers
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code
    
    # Clean up excessive whitespace
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()


def format_multi_dimensional_scores(dimension_scores: Dict[str, float], 
                                  overall_score: float) -> str:
    """Format multi-dimensional evaluation scores for CLI display.
    
    Args:
        dimension_scores: Dictionary of dimension names to scores
        overall_score: Overall weighted score
        
    Returns:
        Formatted string for CLI display
    """
    lines = []
    lines.append("📊 Multi-Dimensional Evaluation:")
    
    # Determine rating
    if overall_score >= 8.5:
        rating = "Excellent"
    elif overall_score >= 7.0:
        rating = "Good"
    elif overall_score >= 5.0:
        rating = "Fair"
    else:
        rating = "Poor"
    
    lines.append(f"Overall Score: {overall_score:.1f}/10 ({rating})")
    
    # Find best and worst dimensions
    sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
    best_dim = sorted_dims[0]
    worst_dim = sorted_dims[-1]
    
    # Format individual dimensions
    for dim_name, score in dimension_scores.items():
        # Format dimension name
        display_name = dim_name.replace('_', ' ').title()
        
        # Use checkmark for all positive scores
        icon = "✅" if score >= 5.0 else "⚠️"
        
        # Add indicator for best/worst
        suffix = ""
        if dim_name == best_dim[0] and len(sorted_dims) > 1:
            suffix = " (Highest)"
        elif dim_name == worst_dim[0] and len(sorted_dims) > 1:
            suffix = " (Needs Improvement)"
        
        lines.append(f"├─ {icon} {display_name}: {score:.1f}{suffix}")
    
    # Replace the last ├─ with └─
    if lines:
        last_line = lines[-1]
        lines[-1] = last_line.replace('├─', '└─')
    
    # Add summary
    lines.append(f"💡 Strongest aspect: {best_dim[0].replace('_', ' ').title()} ({best_dim[1]:.1f})")
    if worst_dim[1] < 7.0:  # Only show improvement area if it's actually low
        lines.append(f"⚠️  Area for improvement: {worst_dim[0].replace('_', ' ').title()} ({worst_dim[1]:.1f})")
    
    return '\n'.join(lines)


def format_logical_inference_results(inference_results: Dict[str, Any]) -> str:
    """Format logical inference results for CLI display.
    
    Args:
        inference_results: Dictionary containing inference analysis
        
    Returns:
        Formatted string for CLI display
    """
    if not inference_results:
        return ""
    
    lines = []
    lines.append("🔍 Logical Inference Analysis:")
    
    # Handle both old format (causal_chains) and new format (inference_chain)
    if "causal_chains" in inference_results and inference_results["causal_chains"]:
        lines.append("├─ Causal Chains:")
        for chain in inference_results["causal_chains"]:
            lines.append(f"│  • {chain}")
    elif "inference_chain" in inference_results and inference_results["inference_chain"]:
        lines.append("├─ Logical Steps:")
        for i, step in enumerate(inference_results["inference_chain"], 1):
            lines.append(f"│  {i}. {step}")
    
    # Handle constraints (old format)
    if "constraints" in inference_results and inference_results["constraints"]:
        lines.append("├─ Constraints:")
        for constraint, status in inference_results["constraints"].items():
            if status == "satisfied":
                lines.append(f"│  ✓ {constraint}: {status}")
            else:
                lines.append(f"│  ✗ {constraint}: {status}")
    
    # Handle contradictions (old format)
    if "contradictions" in inference_results and inference_results["contradictions"]:
        lines.append("├─ Contradictions Detected:")
        for contradiction in inference_results["contradictions"]:
            lines.append(f"│  ⚠️ {contradiction}")
    
    # Handle implications (old format) or improvements (new format)
    if "implications" in inference_results and inference_results["implications"]:
        lines.append("└─ Implications:")
        for implication in inference_results["implications"]:
            lines.append(f"   • {implication}")
    elif "improvements" in inference_results and inference_results["improvements"]:
        lines.append("└─ Recommendations:")
        for improvement in inference_results["improvements"]:
            lines.append(f"   • {improvement}")
    
    # Handle conclusion (new format)
    elif "conclusion" in inference_results and inference_results["conclusion"]:
        lines.append("└─ Conclusion:")
        lines.append(f"   {inference_results['conclusion']}")
    
    return '\n'.join(lines)


def format_advocacy_section(advocacy_data: Dict[str, Any]) -> str:
    """Format advocacy data for CLI display.
    
    Args:
        advocacy_data: Structured advocacy data
        
    Returns:
        Formatted string for CLI display
    """
    lines = []
    lines.append("🔷 Advocacy:")
    lines.append("")  # Add line break after header
    
    # Strengths
    if "strengths" in advocacy_data and advocacy_data["strengths"]:
        lines.append("STRENGTHS:")
        # Show all strengths for detailed mode
        for strength in advocacy_data["strengths"]:
            if isinstance(strength, dict):
                lines.append(f"• {strength['title']}: {strength['description']}")
            else:
                # Handle string format
                lines.append(f"• {strength}")
        lines.append("")
    
    # Opportunities
    if "opportunities" in advocacy_data and advocacy_data["opportunities"]:
        lines.append("OPPORTUNITIES:")
        # Show all opportunities for detailed mode
        for opp in advocacy_data["opportunities"]:
            if isinstance(opp, dict):
                lines.append(f"• {opp['title']}: {opp['description']}")
            else:
                # Handle string format
                lines.append(f"• {opp}")
        lines.append("")
    
    # Addressing concerns
    if "addressing_concerns" in advocacy_data and advocacy_data["addressing_concerns"]:
        lines.append("ADDRESSING CONCERNS:")
        # Show all concerns for detailed mode
        for concern_item in advocacy_data["addressing_concerns"]:
            if isinstance(concern_item, dict):
                lines.append(f"• {concern_item['concern']} → {concern_item['response']}")
            else:
                # Handle string format
                lines.append(f"• {concern_item}")
    
    return '\n'.join(lines)


def format_skepticism_section(skepticism_data: Dict[str, Any]) -> str:
    """Format skepticism data for CLI display.
    
    Args:
        skepticism_data: Structured skepticism data
        
    Returns:
        Formatted string for CLI display
    """
    lines = []
    lines.append("🔶 Skepticism:")
    lines.append("")  # Add line break after header
    
    # Critical flaws
    if "critical_flaws" in skepticism_data and skepticism_data["critical_flaws"]:
        lines.append("CRITICAL FLAWS:")
        # Show all flaws for detailed mode
        for flaw in skepticism_data["critical_flaws"]:
            if isinstance(flaw, dict):
                lines.append(f"• {flaw['title']}: {flaw['description']}")
            else:
                # Handle string format
                lines.append(f"• {flaw}")
        lines.append("")
    
    # Risks and challenges
    if "risks_and_challenges" in skepticism_data and skepticism_data["risks_and_challenges"]:
        lines.append("RISKS & CHALLENGES:")
        # Show all risks for detailed mode
        for risk in skepticism_data["risks_and_challenges"]:
            if isinstance(risk, dict):
                lines.append(f"• {risk['title']}: {risk['description']}")
            else:
                # Handle string format
                lines.append(f"• {risk}")
        lines.append("")
    
    # Questionable assumptions
    if "questionable_assumptions" in skepticism_data and skepticism_data["questionable_assumptions"]:
        lines.append("QUESTIONABLE ASSUMPTIONS:")
        # Show all assumptions for detailed mode
        for assumption in skepticism_data["questionable_assumptions"]:
            if isinstance(assumption, dict):
                lines.append(f"• {assumption['assumption']} — {assumption['concern']}")
            else:
                # Handle string format
                lines.append(f"• {assumption}")
        lines.append("")
    
    # Missing considerations
    if "missing_considerations" in skepticism_data and skepticism_data["missing_considerations"]:
        lines.append("MISSING CONSIDERATIONS:")
        # Show all considerations for detailed mode
        for missing in skepticism_data["missing_considerations"]:
            if isinstance(missing, dict):
                lines.append(f"• {missing['aspect']}: {missing['importance']}")
            else:
                # Handle string format
                lines.append(f"• {missing}")
    
    return '\n'.join(lines)


def format_improved_idea_section(improved_data: Dict[str, Any]) -> str:
    """Format improved idea data for CLI display.
    
    Args:
        improved_data: Structured improved idea data
        
    Returns:
        Formatted string for CLI display
    """
    lines = []
    lines.append("✨ Improved Idea:")
    lines.append("")  # Add line break after header
    
    # Title and description
    lines.append(f"{improved_data['improved_title']}")
    lines.append("")
    lines.append(improved_data['improved_description'])
    lines.append("")
    
    # Key improvements
    if "key_improvements" in improved_data and improved_data["key_improvements"]:
        lines.append("Key Improvements:")
        for improvement in improved_data["key_improvements"]:
            lines.append(f"• {improvement}")
        lines.append("")
    
    # Implementation steps
    if "implementation_steps" in improved_data and improved_data["implementation_steps"]:
        lines.append("Implementation Steps:")
        for i, step in enumerate(improved_data["implementation_steps"], 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    
    # Differentiators
    if "differentiators" in improved_data and improved_data["differentiators"]:
        lines.append("Key Differentiators:")
        for diff in improved_data["differentiators"]:
            lines.append(f"• {diff}")
    
    return '\n'.join(lines)


def smart_truncate_text(text: str, max_lines: Optional[int] = None) -> str:
    """Intelligently truncate text to fit terminal constraints.
    
    Args:
        text: Text to potentially truncate
        max_lines: Maximum number of lines (auto-detect if None)
        
    Returns:
        Truncated text with continuation indicator if needed
    """
    if not text:
        return text
    
    # Get terminal size
    try:
        terminal_size = shutil.get_terminal_size()
        terminal_lines = terminal_size.lines
        terminal_cols = terminal_size.columns
    except (AttributeError, OSError, ValueError):
        # Handle specific terminal size detection failures
        terminal_lines = DEFAULT_TERMINAL_LINES
        terminal_cols = DEFAULT_TERMINAL_COLS
    
    # Use provided max_lines or calculate from terminal
    if max_lines is None:
        # Reserve lines for prompt and UI
        max_lines = terminal_lines - TERMINAL_UI_RESERVE_LINES
    
    # Split into lines and wrap long lines
    lines = []
    for line in text.split('\n'):
        if len(line) > terminal_cols:
            # Simple word wrapping
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= terminal_cols:
                    current_line += " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
        else:
            lines.append(line)
    
    # Check if truncation is needed
    if len(lines) <= max_lines:
        return text
    
    # Find a good truncation point (prefer section boundaries)
    truncate_at = max_lines - CONTINUATION_MESSAGE_LINES  # Reserve lines for continuation message
    
    # Look for section boundary near truncation point
    for i in range(truncate_at, max(0, truncate_at - SECTION_BOUNDARY_SEARCH_LINES), -1):
        if lines[i].startswith(('---', '###', '##', '#', '═', '─')):
            truncate_at = i
            break
    
    # Truncate and add continuation message
    truncated_lines = lines[:truncate_at]
    truncated_lines.append("")
    truncated_lines.append("... [Output truncated - {} more lines]".format(len(lines) - truncate_at))
    truncated_lines.append("(Full output saved to file - use --output-file to specify location)")
    
    return '\n'.join(truncated_lines)


def format_enhanced_reasoning_section(reasoning_data: Dict[str, Any]) -> str:
    """Format enhanced reasoning analysis for CLI display.
    
    Args:
        reasoning_data: Enhanced reasoning analysis data
        
    Returns:
        Formatted string for CLI display
    """
    lines = []
    lines.append("🧠 Enhanced Reasoning Analysis:")
    
    if "context_awareness" in reasoning_data:
        lines.append(f"├─ Context Awareness: {reasoning_data['context_awareness']}")
    
    if "cross_agent_insights" in reasoning_data:
        lines.append("├─ Cross-Agent Insights:")
        for insight in reasoning_data["cross_agent_insights"]:
            lines.append(f"│  • {insight}")
    
    if "reasoning_chains" in reasoning_data:
        lines.append("└─ Reasoning Chains:")
        for chain in reasoning_data["reasoning_chains"]:
            lines.append(f"   • {chain}")
    
    return '\n'.join(lines)