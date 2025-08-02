"""Output processing utilities for converting structured data to CLI-friendly format."""
import re
import shutil
from typing import Dict, Any, List, Optional


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
    # First handle nested bullets (must come first to catch indented ones)
    text = re.sub(r'^(\s+)\* ', lambda m: m.group(1) + '◦ ', text, flags=re.MULTILINE)
    # Then handle top-level bullets
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
    
    # Causal chains
    if "causal_chains" in inference_results and inference_results["causal_chains"]:
        lines.append("├─ Causal Chains:")
        for chain in inference_results["causal_chains"]:
            lines.append(f"│  • {chain}")
    
    # Constraints
    if "constraints" in inference_results and inference_results["constraints"]:
        lines.append("├─ Constraints:")
        for constraint, status in inference_results["constraints"].items():
            icon = "✓" if status == "satisfied" else "✗"
            lines.append(f"│  {icon} {constraint}: {status}")
    
    # Contradictions
    if "contradictions" in inference_results:
        contradictions = inference_results["contradictions"]
        if contradictions:
            lines.append("├─ Contradictions Detected:")
            for contradiction in contradictions:
                lines.append(f"│  ⚠️ {contradiction}")
        else:
            lines.append("├─ Contradictions: None detected ✓")
    
    # Implications
    if "implications" in inference_results and inference_results["implications"]:
        lines.append("└─ Implications:")
        for implication in inference_results["implications"]:
            lines.append(f"   • {implication}")
    
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
        strengths = advocacy_data["strengths"][:5]  # Show top 5
        for strength in strengths:
            if isinstance(strength, dict):
                lines.append(f"• {strength['title']}: {strength['description']}")
            else:
                # Handle string format
                lines.append(f"• {strength}")
        if len(advocacy_data["strengths"]) > 5:
            lines.append(f"  ... and {len(advocacy_data["strengths"]) - 5} more strengths")
        lines.append("")
    
    # Opportunities
    if "opportunities" in advocacy_data and advocacy_data["opportunities"]:
        lines.append("OPPORTUNITIES:")
        opps = advocacy_data["opportunities"][:5]  # Show top 5
        for opp in opps:
            if isinstance(opp, dict):
                lines.append(f"• {opp['title']}: {opp['description']}")
            else:
                # Handle string format
                lines.append(f"• {opp}")
        if len(advocacy_data["opportunities"]) > 5:
            lines.append(f"  ... and {len(advocacy_data["opportunities"]) - 5} more opportunities")
        lines.append("")
    
    # Addressing concerns
    if "addressing_concerns" in advocacy_data and advocacy_data["addressing_concerns"]:
        lines.append("ADDRESSING CONCERNS:")
        concerns = advocacy_data["addressing_concerns"][:5]  # Show top 5
        for concern_item in concerns:
            if isinstance(concern_item, dict):
                lines.append(f"• {concern_item['concern']} → {concern_item['response']}")
            else:
                # Handle string format
                lines.append(f"• {concern_item}")
        if len(advocacy_data["addressing_concerns"]) > 5:
            lines.append(f"  ... and {len(advocacy_data["addressing_concerns"]) - 5} more addressed")
    
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
        flaws = skepticism_data["critical_flaws"][:5]  # Show top 5
        for flaw in flaws:
            if isinstance(flaw, dict):
                lines.append(f"• {flaw['title']}: {flaw['description']}")
            else:
                # Handle string format
                lines.append(f"• {flaw}")
        if len(skepticism_data["critical_flaws"]) > 5:
            lines.append(f"  ... and {len(skepticism_data["critical_flaws"]) - 5} more flaws")
        lines.append("")
    
    # Risks and challenges
    if "risks_and_challenges" in skepticism_data and skepticism_data["risks_and_challenges"]:
        lines.append("RISKS & CHALLENGES:")
        risks = skepticism_data["risks_and_challenges"][:5]  # Show top 5
        for risk in risks:
            if isinstance(risk, dict):
                lines.append(f"• {risk['title']}: {risk['description']}")
            else:
                # Handle string format
                lines.append(f"• {risk}")
        if len(skepticism_data["risks_and_challenges"]) > 5:
            lines.append(f"  ... and {len(skepticism_data["risks_and_challenges"]) - 5} more risks")
        lines.append("")
    
    # Questionable assumptions
    if "questionable_assumptions" in skepticism_data and skepticism_data["questionable_assumptions"]:
        lines.append("QUESTIONABLE ASSUMPTIONS:")
        assumptions = skepticism_data["questionable_assumptions"][:5]  # Show top 5
        for assumption in assumptions:
            if isinstance(assumption, dict):
                lines.append(f"• {assumption['assumption']} — {assumption['concern']}")
            else:
                # Handle string format
                lines.append(f"• {assumption}")
        if len(skepticism_data["questionable_assumptions"]) > 5:
            lines.append(f"  ... and {len(skepticism_data["questionable_assumptions"]) - 5} more assumptions")
        lines.append("")
    
    # Missing considerations
    if "missing_considerations" in skepticism_data and skepticism_data["missing_considerations"]:
        lines.append("MISSING CONSIDERATIONS:")
        considerations = skepticism_data["missing_considerations"][:5]  # Show top 5
        for missing in considerations:
            if isinstance(missing, dict):
                lines.append(f"• {missing['aspect']}: {missing['importance']}")
            else:
                # Handle string format
                lines.append(f"• {missing}")
        if len(skepticism_data["missing_considerations"]) > 5:
            lines.append(f"  ... and {len(skepticism_data["missing_considerations"]) - 5} more considerations")
    
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
    except:
        terminal_lines = 24
        terminal_cols = 80
    
    # Use provided max_lines or calculate from terminal
    if max_lines is None:
        # Reserve lines for prompt and UI
        max_lines = terminal_lines - 10
    
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
    truncate_at = max_lines - 3  # Reserve lines for continuation message
    
    # Look for section boundary near truncation point
    for i in range(truncate_at, max(0, truncate_at - 10), -1):
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