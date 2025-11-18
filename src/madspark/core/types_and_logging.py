"""Shared types and logging utilities for MadSpark coordinators.

This module contains shared TypedDict definitions and logging functions
used by both the main coordinator and batch coordinator to avoid circular imports.
"""
import logging
from typing import Dict, Any, Optional, TypedDict


# --- TypedDict Definitions ---
class EvaluatedIdea(TypedDict):
    """Structure for an idea after evaluation by the CriticAgent."""
    text: str       # The original idea text
    score: int      # Score assigned by the critic
    critique: str   # Textual critique from the critic
    multi_dimensional_evaluation: Optional[Dict[str, Any]]  # Initial multi-dimensional evaluation data
    improved_multi_dimensional_evaluation: Optional[Dict[str, Any]]  # Re-evaluated after improvement


class CandidateData(TypedDict):
    """Structure for the final data compiled for each candidate idea."""
    idea: str
    initial_score: float
    initial_critique: str
    advocacy: str
    skepticism: str
    multi_dimensional_evaluation: Optional[Dict[str, Any]]
    improved_idea: str
    improved_score: float
    improved_critique: str
    score_delta: float
    is_meaningful_improvement: bool
    similarity_score: float
    improved_multi_dimensional_evaluation: Optional[Dict[str, Any]]  # Re-evaluated after improvement
# --- End TypedDict Definitions ---


# --- Logging Functions ---
def log_verbose_step(step_name: str, details: str = "", verbose: bool = False):
    """Log verbose step information with visual indicators."""
    if verbose:
        msg = f"\n{'='*60}\n🔍 {step_name}\n{'='*60}"
        if details:
            msg += f"\n{details}"
        msg += "\n"
        print(msg)
        logging.info(f"VERBOSE_STEP: {step_name}")
        if details:
            logging.info(f"VERBOSE_DETAILS: {details}")


def log_verbose_data(label: str, data: str, verbose: bool = False, max_length: int = 500):
    """Log verbose data with truncation for readability."""
    if not verbose:
        return  # Early exit to avoid any string operations
    
    # Use list for efficient string building
    msg_parts = [f"\n📊 {label}:", "-" * 40]
    
    if len(data) > max_length:
        msg_parts.extend([
            data[:max_length] + "...",
            "",
            f"[Truncated - Total length: {len(data)} characters]"
        ])
        log_data = data[:max_length] + "..."
    else:
        msg_parts.append(data)
        log_data = data
    
    msg_parts.append("-" * 40)
    print("\n".join(msg_parts))
    
    logging.info(f"VERBOSE_DATA: {label} ({len(data)} characters)")
    # Log truncated version to file
    logging.debug(f"VERBOSE_CONTENT: {log_data}")


def log_verbose_completion(step_name: str, count: int, duration: float, verbose: bool = False, unit: str = "items"):
    """Log completion status with timing information."""
    if verbose:
        print(f"✅ {step_name} Complete: Generated {count} {unit} in {duration:.2f}s")


def log_verbose_sample_list(items: list, verbose: bool = False, max_display: int = 3, item_formatter=None):
    """Log a sample of items from a list."""
    if verbose and items:
        print("📝 Sample Items:")
        display_items = items[:max_display]
        for i, item in enumerate(display_items, 1):
            if item_formatter:
                formatted_item = item_formatter(item)
            else:
                formatted_item = str(item)[:80] + ("..." if len(str(item)) > 80 else "")
            print(f"  {i}. {formatted_item}")
        if len(items) > max_display:
            print(f"  ... and {len(items) - max_display} more items")


def log_agent_execution(step_name: str, agent_name: str, agent_emoji: str, description: str, 
                       temperature: float, verbose: bool = False):
    """Log the start of an agent execution with standardized format."""
    if verbose:
        details = f"{agent_emoji} Agent: {agent_name}\n🎯 {description}\n🌡️ Temperature: {temperature}"
        log_verbose_step(step_name, details, verbose)


def log_agent_completion(agent_name: str, response_data: str, step_number: str, 
                        duration: float, verbose: bool = False, max_length: int = 600):
    """Log the completion of an agent execution with response data."""
    if verbose:
        log_verbose_data(f"Raw {agent_name} Response for {step_number}", response_data, verbose, max_length)
        log_verbose_completion(f"{agent_name} Analysis", len(response_data), duration, verbose, "characters")
# --- End Logging Functions ---