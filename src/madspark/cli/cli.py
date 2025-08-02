"""Command Line Interface for MadSpark Multi-Agent System.

This module provides a comprehensive CLI for running the MadSpark workflow
with all Phase 1 features including temperature control, novelty filtering,
and bookmark management.
"""
import argparse
import asyncio
import json
import sys
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

# Import idea cleaner (removed unused import)

# Import MadSpark components with fallback for local development
try:
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.core.async_coordinator import AsyncCoordinator
    from madspark.utils.temperature_control import (
        TemperatureManager, 
        add_temperature_arguments,
        create_temperature_manager_from_args
    )
    from madspark.utils.constants import (
        MIN_TIMEOUT_FOR_MULTIPLE_IDEAS_SECONDS
    )
    from madspark.utils.bookmark_system import (
        BookmarkManager,
        list_bookmarks_cli,
        remix_with_bookmarks
    )
    from madspark.utils.export_utils import ExportManager, create_metadata_from_args
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.utils.errors import ValidationError
except ImportError:
    # Fallback for local development/testing
    from coordinator import run_multistep_workflow
    from async_coordinator import AsyncCoordinator
    from temperature_control import (
        TemperatureManager, 
        add_temperature_arguments,
        create_temperature_manager_from_args
    )
    from constants import (
        MIN_TIMEOUT_FOR_MULTIPLE_IDEAS_SECONDS
    )
    from bookmark_system import (
        BookmarkManager,
        list_bookmarks_cli,
        remix_with_bookmarks
    )
    from export_utils import ExportManager, create_metadata_from_args
    from cache_manager import CacheManager, CacheConfig
    from errors import ValidationError

# Import interactive mode after the try/except blocks
try:
    from madspark.cli.interactive_mode import run_interactive_mode
    from madspark.utils.batch_processor import BatchProcessor, create_sample_batch_file
except ImportError:
    from interactive_mode import run_interactive_mode
    from batch_processor import BatchProcessor, create_sample_batch_file

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Clear any existing handlers to ensure our configuration takes effect
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create logs directory if verbose mode is enabled
    if verbose:
        try:
            os.makedirs("logs", exist_ok=True)
        except PermissionError:
            print("⚠️ Warning: Cannot create logs directory due to permissions. Logs will only go to console.")
            # Fall back to console-only logging
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True
            )
            return
        except OSError as e:
            print(f"⚠️ Warning: Cannot create logs directory: {e}. Logs will only go to console.")
            # Fall back to console-only logging
            logging.basicConfig(
                level=level,
                format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                force=True
            )
            return
        
        # Create timestamped log file for verbose mode
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/madspark_verbose_{timestamp}.log"
        
        # Configure logging with both file and console output
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ],
            force=True  # Force reconfiguration even if basicConfig was called before
        )
        
        print(f"📁 Verbose logs will be saved to: {log_file}")
    else:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Force reconfiguration even if basicConfig was called before
        )


class BetterHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that improves help output readability."""
    
    def _format_usage(self, usage, actions, groups, prefix):
        """Format usage with better line breaks."""
        if prefix is None:
            prefix = 'usage: '
        
        # Get the program name - use 'ms' as default for better UX
        # Check various ways the script might be invoked
        if any(cmd in sys.argv[0] for cmd in ['mad_spark', 'madspark', 'ms', 'run.py']):
            prog = 'ms'
        elif self._prog in ['cli', 'cli.py', '__main__.py']:
            prog = 'ms'
        else:
            prog = self._prog
        
        # Build a cleaner usage string
        usage_parts = [prog]
        
        # Add main arguments
        usage_parts.append('[options]')
        usage_parts.append('topic')
        usage_parts.append('[context]')
        
        # Join with proper spacing
        usage = '%s%s\n' % (prefix, ' '.join(usage_parts))
        
        # Add a note about common operations
        usage += '\n'
        usage += 'Common operations:\n'
        usage += '  %s "your topic"                    # Generate idea with default context\n' % prog
        usage += '  %s "your topic" "your context"     # Generate idea with specific context\n' % prog
        usage += '  %s --list-bookmarks                # List saved ideas\n' % prog
        usage += '  %s --help                          # Show this help\n' % prog
        usage += '  python -m madspark.cli.batch_metrics  # View API usage metrics\n'
        
        return usage


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description='MadSpark Multi-Agent Idea Generation System - Now with Google Gemini structured output for cleaner formatting and 50% fewer API calls through intelligent batch processing',
        formatter_class=BetterHelpFormatter,
        epilog="""
Examples:
  # Basic usage with topic and context
  ms "Future transportation" "Budget-friendly, eco-friendly"
  
  # Questions (how to solve problems)
  ms "How to reduce carbon footprint?" "small business"
  
  # Requests (come up with ideas)
  ms "Come up with innovative ways to teach math" "elementary school"
  
  # General phrases (I want to...)
  ms "I want to start a sustainable business. Support me." "zero initial capital"
  
  # Save results with custom tags (bookmarking is automatic)
  ms "Smart cities" "Scalable solutions" --bookmark-tags smart urban tech
  
  # Enhanced reasoning with multi-dimensional evaluation
  ms "AI healthcare" "Rural deployment" --enhanced-reasoning --multi-dimensional-eval
  
  # Generate ideas based on bookmarks (remix)
  ms "Green energy" --remix --bookmark-tags renewable
  
  # Verbose mode with enhanced reasoning for detailed analysis
  ms "Sustainable agriculture" "Low-cost" --verbose --enhanced-reasoning
  
  # List saved bookmarks
  ms --list-bookmarks
  
  # Show temperature presets
  ms --list-presets
  
  # Batch processing
  ms --create-sample-batch csv
  ms --batch sample_batch.csv --batch-concurrent 5
  
  # Interactive mode
  ms --interactive
        """
    )
    
    # Positional arguments for basic workflow
    # Note: Keeping argument names as 'theme' and 'constraints' for backward compatibility
    # but using 'topic' and 'context' in help text for consistency with codebase
    parser.add_argument(
        'theme',
        nargs='?',
        help='Topic for idea generation (can be a phrase, question, or request)'
    )
    
    parser.add_argument(
        'constraints',
        nargs='?',
        help='Context and criteria for idea generation (optional additional information)'
    )
    
    # Interactive mode
    parser.add_argument(
        '--version',
        action='version',
        version='MadSpark Multi-Agent System v2.2',
        help='Show version information and exit'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode with step-by-step guidance'
    )
    
    # Batch processing
    batch_group = parser.add_argument_group('batch processing')
    
    batch_group.add_argument(
        '--batch',
        metavar='FILE',
        help='Process multiple themes from CSV or JSON file'
    )
    
    batch_group.add_argument(
        '--batch-concurrent',
        type=int,
        default=3,
        metavar='N',
        help='Maximum concurrent batch items (default: 3)'
    )
    
    batch_group.add_argument(
        '--batch-export-dir',
        default='batch_exports',
        help='Directory for batch export results (default: batch_exports)'
    )
    
    batch_group.add_argument(
        '--create-sample-batch',
        choices=['csv', 'json'],
        help='Create a sample batch file and exit'
    )
    
    # Workflow options
    workflow_group = parser.add_argument_group('workflow options')
    
    # Note: --num-candidates is deprecated but kept for backward compatibility
    workflow_group.add_argument(
        '--num-candidates', '-n',
        type=int,
        default=None,  # Changed to None to detect if explicitly set
        help='(Deprecated: use --top-ideas instead) Number of top candidates to fully process'
    )
    
    workflow_group.add_argument(
        '--top-ideas',
        dest='top_ideas',
        type=int,
        choices=range(1, 6),
        default=None,  # Changed to None to detect if explicitly set
        help='Number of top ideas to generate (1-5, default: 1 for faster execution). Multiple ideas may take up to 5 minutes to process.'
    )
    
    workflow_group.add_argument(
        '--similarity',
        dest='similarity_threshold',
        type=float,
        choices=[round(x * 0.1, 1) for x in range(11)],  # 0.0, 0.1, ..., 1.0
        help='Similarity threshold for novelty filter (0.0-1.0)'
    )
    
    workflow_group.add_argument(
        '--disable-novelty-filter',
        action='store_true',
        help='Disable the novelty filter for duplicate detection'
    )
    
    workflow_group.add_argument(
        '--novelty-threshold',
        type=float,
        default=0.8,
        help='Threshold for novelty filter similarity detection (0.0-1.0, default: 0.8)'
    )
    
    workflow_group.add_argument(
        '--async',
        action='store_true',
        help='Use async execution for better performance (Phase 2.3)'
    )
    
    workflow_group.add_argument(
        '--enable-cache',
        action='store_true',
        help='Enable Redis caching for faster repeated queries (requires Redis)'
    )
    
    workflow_group.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Request timeout in seconds (default: 600, i.e., 10 minutes)'
    )
    
    # Temperature control
    add_temperature_arguments(parser)
    
    # Bookmark management (automatic by default)
    bookmark_group = parser.add_argument_group('bookmark management', 
                                              'All generated ideas are automatically bookmarked for future reference')
    
    bookmark_group.add_argument(
        '--no-bookmark',
        action='store_true',
        help='Disable automatic bookmarking of generated ideas'
    )
    
    bookmark_group.add_argument(
        '--bookmark-tags',
        nargs='*',
        help='Tags to apply when bookmarking results'
    )
    
    bookmark_group.add_argument(
        '--bookmark-file',
        default='examples/data/bookmarks.json',
        help='File to store bookmarks (default: examples/data/bookmarks.json)'
    )
    
    bookmark_group.add_argument(
        '--list-bookmarks',
        action='store_true',
        help='List all saved bookmarks and exit'
    )
    
    bookmark_group.add_argument(
        '--search-bookmarks',
        metavar='QUERY',
        help='Search bookmarks by text content'
    )
    
    bookmark_group.add_argument(
        '--remove-bookmark',
        metavar='IDS',
        help='Remove bookmarks by ID (comma-separated for multiple)'
    )
    
    bookmark_group.add_argument(
        '--remix-bookmarks',
        metavar='IDS',
        help='Remix ideas using specific bookmark IDs (comma-separated)'
    )
    
    # Remix functionality
    remix_group = parser.add_argument_group('remix functionality')
    
    remix_group.add_argument(
        '--remix',
        action='store_true',
        help='Generate ideas based on bookmarked ideas (remix mode)'
    )
    
    remix_group.add_argument(
        '--remix-ids',
        nargs='*',
        help='Specific bookmark IDs to use for remix (default: use all)'
    )
    
    # Enhanced reasoning (Phase 2.1)
    reasoning_group = parser.add_argument_group('enhanced reasoning (Phase 2.1)')
    
    reasoning_group.add_argument(
        '--enhanced-reasoning', '--enhanced',
        action='store_true',
        help='Add advocate & skeptic agents for balanced analysis (strengths/opportunities vs risks/flaws)'
    )
    
    # Multi-dimensional evaluation is now always enabled
    # Keeping the argument for backward compatibility but it has no effect
    reasoning_group.add_argument(
        '--multi-dimensional-eval',
        action='store_true',
        help='(DEPRECATED: Always enabled) Multi-dimensional evaluation across 7 dimensions is now a core feature'
    )
    
    reasoning_group.add_argument(
        '--logical-inference', '--logical',
        action='store_true',
        help='Add logical inference analysis (causal chains, constraints, contradictions, implications)'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    
    # Create mutually exclusive group for output modes
    output_mode_group = output_group.add_mutually_exclusive_group()
    
    output_mode_group.add_argument(
        '--simple',
        action='store_const',
        dest='output_mode',
        const='simple',
        help='Simple, clean output format'
    )
    
    output_mode_group.add_argument(
        '--brief', '-b',
        action='store_const',
        dest='output_mode', 
        const='brief',
        help='Brief output showing only final results (default)'
    )
    
    output_mode_group.add_argument(
        '--detailed', '-d',
        action='store_const',
        dest='output_mode',
        const='detailed', 
        help='Detailed output with all agent interactions'
    )
    
    # Set default output mode
    parser.set_defaults(output_mode='brief')
    
    output_group.add_argument(
        '--output-format',
        choices=['json', 'text', 'summary', 'simple', 'brief', 'detailed'],
        help='Output format (overrides --simple/--brief/--detailed)'
    )
    
    output_group.add_argument(
        '--output-file',
        help='Save results to file instead of stdout'
    )
    
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging and show timestamps'
    )
    
    output_group.add_argument(
        '--no-logs',
        action='store_true',
        help='Suppress all log output for clean results'
    )
    
    # Export options (Phase 2.2)
    export_group = parser.add_argument_group('export options (Phase 2.2)')
    
    export_group.add_argument(
        '--export',
        choices=['json', 'csv', 'markdown', 'pdf', 'all'],
        help='Export results to specified format'
    )
    
    export_group.add_argument(
        '--export-dir',
        default='exports',
        help='Directory for exported files (default: exports)'
    )
    
    export_group.add_argument(
        '--export-filename',
        help='Base filename for exports (timestamp will be added if not specified)'
    )
    
    return parser


def truncate_text_intelligently(text: str, max_length: int = 300) -> str:
    """Truncate text at a sensible boundary (sentence or word).
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    # Find a good breaking point (end of sentence or word)
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    last_space = truncated.rfind(' ')
    
    # Prefer to break at sentence end, otherwise at word boundary
    if last_period > max_length - 50:  # If period is near the end
        truncated = truncated[:last_period + 1]
    elif last_space > 0:
        truncated = truncated[:last_space]
    
    return f"{truncated}..."


def list_bookmarks_command(args: argparse.Namespace):
    """Handle the list bookmarks command."""
    bookmarks = list_bookmarks_cli(args.bookmark_file)
    
    if not bookmarks:
        print("No bookmarks found.")
        return
    
    print(f"Found {len(bookmarks)} bookmarks:\n")
    
    for bookmark in bookmarks:
        print(f"ID: {bookmark['id']}")
        print(f"Text: {truncate_text_intelligently(bookmark['text'])}")
        print(f"Theme: {bookmark['theme']}")
        print(f"Score: {bookmark['score']}")
        print(f"Bookmarked: {bookmark['bookmarked_at']}")
        if bookmark['tags']:
            print(f"Tags: {', '.join(bookmark['tags'])}")
        print("-" * 60)


def search_bookmarks_command(args: argparse.Namespace):
    """Handle the search bookmarks command."""
    manager = BookmarkManager(args.bookmark_file)
    matches = manager.search_bookmarks(args.search_bookmarks)
    
    if not matches:
        print(f"No bookmarks found matching '{args.search_bookmarks}'")
        return
    
    print(f"Found {len(matches)} matching bookmarks:\n")
    
    for bookmark in matches:
        print(f"ID: {bookmark.id}")
        print(f"Text: {truncate_text_intelligently(bookmark.text)}")
        print(f"Theme: {bookmark.theme}")
        print(f"Score: {bookmark.score}")
        print("-" * 60)


def remove_bookmark_command(args: argparse.Namespace):
    """Handle the remove bookmark command."""
    manager = BookmarkManager(args.bookmark_file)
    
    # Parse comma-separated IDs
    bookmark_ids = [id.strip() for id in args.remove_bookmark.split(',')]
    
    removed_count = 0
    failed_count = 0
    
    for bookmark_id in bookmark_ids:
        if manager.remove_bookmark(bookmark_id):
            print(f"✅ Removed bookmark: {bookmark_id}")
            removed_count += 1
        else:
            print(f"❌ Failed to remove bookmark: {bookmark_id} (not found)")
            failed_count += 1
    
    # Summary
    print(f"\n📊 Summary: {removed_count} removed, {failed_count} failed")
    
    if removed_count > 0:
        print(f"💾 Bookmarks file updated: {args.bookmark_file}")


def _parse_structured_agent_data(agent_data: str, agent_type: str) -> Dict[str, Any]:
    """Parse structured JSON agent data or fallback to text parsing.
    
    Args:
        agent_data: Raw agent response (JSON or text)
        agent_type: Type of agent ('advocacy', 'skepticism', 'evaluation')
        
    Returns:
        Dictionary with parsed and formatted data
    """
    if not agent_data or not agent_data.strip():
        return {"formatted": f"No {agent_type} available", "structured": {}}
    
    try:
        # Try to parse as JSON first
        structured_data = json.loads(agent_data)
        
        if agent_type == 'advocacy':
            from madspark.utils.output_processor import format_advocacy_section
            formatted = format_advocacy_section(structured_data)
            return {"formatted": formatted, "structured": structured_data}
            
        elif agent_type == 'skepticism':
            from madspark.utils.output_processor import format_skepticism_section
            formatted = format_skepticism_section(structured_data)
            return {"formatted": formatted, "structured": structured_data}
            
        elif agent_type == 'evaluation':
            # Evaluation is handled differently - already parsed in coordinator
            return {"formatted": agent_data, "structured": structured_data}
            
    except (json.JSONDecodeError, TypeError, ImportError):
        # Fall back to text format for backward compatibility
        return {"formatted": agent_data, "structured": {}}
    
    return {"formatted": agent_data, "structured": {}}


def format_results(results: List[Dict[str, Any]], format_type: str) -> str:
    """Format results according to specified format."""
    # Apply cleaning to all results before formatting (consistent across all formats)
    try:
        from madspark.utils.improved_idea_cleaner import clean_improved_ideas_in_results
    except ImportError:
        from ..utils.improved_idea_cleaner import clean_improved_ideas_in_results
    cleaned_results = clean_improved_ideas_in_results(results)
    
    if format_type == 'json':
        return json.dumps(cleaned_results, indent=2, ensure_ascii=False)
    
    elif format_type == 'brief':
        """Brief mode: Solution-focused output with markdown headers."""
        lines = []
        for i, result in enumerate(cleaned_results, 1):
            # Add markdown header
            if len(cleaned_results) > 1:
                lines.append(f"## Idea {i}")
            else:
                lines.append("## Solution")
            
            # Show improved idea if available, otherwise original
            final_idea = result.get('improved_idea', result.get('idea', 'No idea available'))
            final_score = result.get('improved_score', result.get('initial_score', 'N/A'))
            
            # Focus on the solution first - clean presentation
            lines.append(f"{final_idea}")
            lines.append("")
            
            # Add score information after the solution
            if final_score != 'N/A':
                lines.append(f"**Score:** {final_score}/10")
            
            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas
        
        return "\n".join(lines)
    
    elif format_type == 'simple':
        """Simple mode: Clean, user-friendly output without debug info."""
        lines = []
        for i, result in enumerate(cleaned_results, 1):
            if len(cleaned_results) > 1:
                lines.append(f"━━━ Idea {i} ━━━")
            
            # Original idea
            original_idea = result.get('idea', 'No idea available')
            initial_score = result.get('initial_score', 'N/A')
            
            lines.append(f"💭 Original: {original_idea}")
            lines.append(f"📊 Initial Score: {initial_score}")
            
            # Show improvement if available and meaningful
            if 'improved_idea' in result:
                improved_idea = result['improved_idea']
                improved_score = result.get('improved_score', 'N/A')
                score_delta = result.get('score_delta', 0)
                
                # Check if improvement is meaningful (determined by coordinator)
                is_meaningful_improvement = result.get('is_meaningful_improvement', True)
                
                if is_meaningful_improvement:
                    lines.append(f"✨ Improved: {improved_idea}")
                    lines.append(f"📈 Final Score: {improved_score}")
                    if score_delta > 0:
                        lines.append(f"⬆️  Improvement: +{score_delta:.1f}")
                else:
                    # Show only final score, indicate no meaningful improvement
                    lines.append(f"📈 Final Score: {improved_score}")
                    lines.append("✅ Already well-developed - no significant improvements needed")
            
            # Add evaluation summary if available (clean format)
            if 'multi_dimensional_evaluation' in result:
                eval_data = result['multi_dimensional_evaluation']
                if eval_data and 'evaluation_summary' in eval_data:
                    summary = eval_data['evaluation_summary']
                    # Remove the "🧠 Enhanced Analysis:" prefix if present
                    summary = summary.replace('🧠 Enhanced Analysis:\n', '').replace('🧠 Enhanced Analysis:', '')
                    lines.append(f"📋 Analysis: {summary.strip()}")
            
            if i < len(cleaned_results):
                lines.append("")  # Empty line between ideas
        
        return "\n".join(lines)
    
    elif format_type == 'detailed':
        """Detailed mode: Show all agent interactions and analysis."""
        lines = ["=" * 80]
        lines.append("MADSPARK MULTI-AGENT IDEA GENERATION RESULTS")
        lines.append("=" * 80)
        
        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"\n--- IDEA {i} ---")
            # Strip leading number from idea text if present
            idea_text = result.get('idea', 'No idea available')
            # Remove pattern like "3. " or "10. " from the beginning
            import re
            idea_text = re.sub(r'^\d+\.\s+', '', idea_text)
            lines.append(idea_text)
            initial_score = result.get('initial_score', 'N/A')
            if initial_score != 'N/A':
                lines.append(f"Initial Score: {initial_score:.2f}")
            else:
                lines.append(f"Initial Score: {initial_score}")
            lines.append(f"Initial Critique: {result.get('initial_critique', 'No critique available')}")
            
            # Agent feedback with structured parsing
            if 'advocacy' in result:
                advocacy_data = _parse_structured_agent_data(result['advocacy'], 'advocacy')
                lines.append(f"\n{advocacy_data['formatted']}")
                
            if 'skepticism' in result:
                skepticism_data = _parse_structured_agent_data(result['skepticism'], 'skepticism')
                lines.append(f"\n{skepticism_data['formatted']}")
            
            # Improved idea
            if 'improved_idea' in result:
                lines.append(f"\n✨ Improved Idea:")
                lines.append(result['improved_idea'])
                improved_score = result.get('improved_score', 'N/A')
                if improved_score != 'N/A':
                    lines.append(f"📈 Improved Score: {improved_score:.2f}")
                else:
                    lines.append(f"📈 Improved Score: {improved_score}")
                
                if 'score_delta' in result:
                    score_delta = result['score_delta']
                    if score_delta > 0:
                        lines.append(f"⬆️  Improvement: +{score_delta:.2f}")
                    elif score_delta < 0:
                        lines.append(f"⬇️  Change: {score_delta:.2f}")
                    else:
                        lines.append("➡️  No significant change")
            
            # Multi-dimensional evaluation with enhanced formatting
            if 'multi_dimensional_evaluation' in result:
                eval_data = result['multi_dimensional_evaluation']
                if eval_data:
                    try:
                        from madspark.utils.output_processor import format_multi_dimensional_scores
                        
                        overall_score = eval_data.get('overall_score', 0)
                        dimension_scores = eval_data.get('dimension_scores', {})
                        
                        if dimension_scores:
                            formatted_scores = format_multi_dimensional_scores(dimension_scores, overall_score)
                            lines.append(f"\n{formatted_scores}")
                        else:
                            lines.append(f"\n📊 Overall Score: {overall_score}")
                            
                        if 'evaluation_summary' in eval_data:
                            lines.append(f"\n💡 Summary: {eval_data['evaluation_summary']}")
                            
                    except ImportError:
                        # Fallback to simple formatting
                        lines.append(f"\n📊 Multi-Dimensional Evaluation:")
                        lines.append(f"  Overall Score: {eval_data.get('overall_score', 'N/A')}")
                        
                        if 'dimension_scores' in eval_data:
                            scores = eval_data['dimension_scores']
                            for dim, score in scores.items():
                                lines.append(f"  • {dim.replace('_', ' ').title()}: {score}")
            
            # Logical inference analysis (when --logical flag is used)
            if 'logical_inference' in result and result['logical_inference']:
                try:
                    from madspark.utils.output_processor import format_logical_inference_results
                    inference_data = result['logical_inference']
                    formatted_inference = format_logical_inference_results(inference_data)
                    if formatted_inference:
                        lines.append(f"\n{formatted_inference}")
                except ImportError:
                    # Fallback formatting
                    lines.append("\n🔍 Logical Inference Analysis:")
                    inference_data = result['logical_inference']
                    if 'causal_chains' in inference_data:
                        lines.append("  Causal Chains:")
                        for chain in inference_data['causal_chains']:
                            lines.append(f"    • {chain}")
            
            lines.append("-" * 80)
        
        return "\n".join(lines)
        
    elif format_type == 'summary':
        lines = [f"Generated {len(cleaned_results)} improved ideas:\n"]
        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"--- IMPROVED IDEA {i} ---")
            
            # Get cleaned improved idea (already cleaned by clean_improved_ideas_in_results)
            improved_idea = result.get('improved_idea', 'No improved idea available')
            
            if len(improved_idea) > 500:
                improved_idea = improved_idea[:497] + "..."
                lines.append(improved_idea)
                lines.append("\n[Note: Full improved idea available in text or JSON format]")
            else:
                lines.append(improved_idea)
            
            lines.append(f"\nImproved Score: {result.get('improved_score', 'N/A')}")
            
            # Add multi-dimensional evaluation if available
            if 'multi_dimensional_evaluation' in result:
                eval_data = result['multi_dimensional_evaluation']
                lines.append("\nMulti-Dimensional Evaluation:")
                lines.append(f"  Overall Score: {eval_data.get('overall_score', 'N/A')}")
                
                if 'dimension_scores' in eval_data:
                    scores = eval_data['dimension_scores']
                    lines.append(f"  - Feasibility: {scores.get('feasibility', 'N/A')}")
                    lines.append(f"  - Innovation: {scores.get('innovation', 'N/A')}")
                    lines.append(f"  - Impact: {scores.get('impact', 'N/A')}")
                    lines.append(f"  - Cost-Effectiveness: {scores.get('cost_effectiveness', 'N/A')}")
                    lines.append(f"  - Scalability: {scores.get('scalability', 'N/A')}")
                    lines.append(f"  - Risk Assessment: {scores.get('risk_assessment', 'N/A')} (lower is better)")
                    lines.append(f"  - Timeline: {scores.get('timeline', 'N/A')}")
                
                if 'evaluation_summary' in eval_data:
                    lines.append(f"  Summary: {eval_data['evaluation_summary']}")
            
            lines.append("")  # Empty line between ideas
        return "\n".join(lines)
    
    else:  # text format (legacy)
        lines = ["=" * 80]
        lines.append("MADSPARK MULTI-AGENT IDEA GENERATION RESULTS")
        lines.append("=" * 80)
        
        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"\n--- IDEA {i} ---")
            lines.append(result.get('idea', 'No idea available'))
            lines.append(f"Initial Score: {result.get('initial_score', 'N/A')}")
            lines.append(f"Initial Critique: {result.get('initial_critique', 'No critique available')}")
            
            # Agent feedback with structured parsing
            if 'advocacy' in result:
                advocacy_data = _parse_structured_agent_data(result['advocacy'], 'advocacy')
                lines.append(f"\nAdvocacy: {advocacy_data['formatted']}")
                
            if 'skepticism' in result:
                skepticism_data = _parse_structured_agent_data(result['skepticism'], 'skepticism')
                lines.append(f"\nSkepticism: {skepticism_data['formatted']}")
            
            # Include cleaned improved idea in text format
            if 'improved_idea' in result:
                lines.append(f"\nImproved Idea: {result['improved_idea']}")
                lines.append(f"Improved Score: {result.get('improved_score', 'N/A')}")
            
            lines.append("-" * 80)
        
        return "\n".join(lines)


def determine_num_candidates(args):
    """Determine the number of candidates to use, handling backward compatibility.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        int: Number of candidates to process
    """
    # If user explicitly set --num-candidates, use it and show deprecation warning
    if args.num_candidates is not None:
        logger = logging.getLogger(__name__)
        logger.warning("--num-candidates is deprecated. Please use --top-ideas instead.")
        # Ensure it's within the valid range for top_ideas
        return min(max(args.num_candidates, 1), 5)
    
    # If user explicitly set --top-ideas, use it
    if args.top_ideas is not None:
        return args.top_ideas
    
    # Default value
    return 1


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Validate timeout value
    if hasattr(args, 'timeout'):
        if args.timeout < 1:
            parser.error("Timeout must be at least 1 second")
        elif args.timeout > 3600:  # 1 hour max
            parser.error("Timeout cannot exceed 3600 seconds (1 hour)")
    
    
    # Validate similarity threshold
    if hasattr(args, 'similarity_threshold') and args.similarity_threshold is not None:
        if args.similarity_threshold < 0.0:
            parser.error("Similarity threshold must be at least 0.0")
        elif args.similarity_threshold > 1.0:
            parser.error("Similarity threshold cannot exceed 1.0")
    
    # Handle --no-logs option OR simple/brief modes by suppressing logging
    if (hasattr(args, 'no_logs') and args.no_logs) or \
       (hasattr(args, 'output_mode') and args.output_mode in ['simple', 'brief']) or \
       (hasattr(args, 'output_format') and args.output_format in ['simple', 'brief']):
        # Suppress all logging except critical errors
        logging.getLogger().setLevel(logging.CRITICAL)
        # Also suppress progress messages in non-verbose modes
        os.environ["SUPPRESS_MODE_MESSAGE"] = "1"
    
    # Handle standalone commands
    if args.list_bookmarks:
        list_bookmarks_command(args)
        return
    
    if args.search_bookmarks:
        search_bookmarks_command(args)
        return
    
    if args.remove_bookmark:
        remove_bookmark_command(args)
        return
    
    if hasattr(args, 'list_presets') and args.list_presets:
        print(TemperatureManager.describe_presets())
        return
    
    # Handle create sample batch file
    if args.create_sample_batch:
        filename = f"sample_batch.{args.create_sample_batch}"
        create_sample_batch_file(filename, args.create_sample_batch)
        print(f"✅ Created sample batch file: {filename}")
        print(f"You can now run: python {sys.argv[0]} --batch {filename}")
        return
    
    # Handle interactive mode
    if args.interactive:
        try:
            session_data = run_interactive_mode()
            # Update args with interactive session data
            args.theme = session_data['theme']
            args.constraints = session_data['constraints']
            
            # Update args with config from interactive session
            config = session_data['config']
            for key, value in config.items():
                if hasattr(args, key):
                    setattr(args, key, value)
                    
            # Continue with normal workflow
        except KeyboardInterrupt:
            print("\n\n❌ Interactive session cancelled.")
            return
        except Exception as e:
            print(f"\n❌ Error in interactive mode: {e}")
            return
    
    # Handle batch processing
    if args.batch:
        try:
            logger.info(f"Starting batch processing from: {args.batch}")
            
            # Create batch processor
            processor = BatchProcessor(
                max_concurrent=args.batch_concurrent,
                use_async=hasattr(args, 'async') and getattr(args, 'async'),
                enable_cache=args.enable_cache,
                export_dir=args.batch_export_dir,
                verbose=args.verbose
            )
            
            # Load batch items
            if args.batch.endswith('.csv'):
                batch_items = processor.load_batch_from_csv(args.batch)
            elif args.batch.endswith('.json'):
                batch_items = processor.load_batch_from_json(args.batch)
            else:
                print("❌ Unsupported batch file format. Use .csv or .json")
                sys.exit(1)
                
            print(f"📋 Loaded {len(batch_items)} items for batch processing")
            
            # Prepare workflow options
            workflow_options = {
                "enable_novelty_filter": not args.disable_novelty_filter,
                "novelty_threshold": args.novelty_threshold,
                "verbose": args.verbose,
                "enhanced_reasoning": args.enhanced_reasoning,
                "multi_dimensional_eval": True,  # Always enabled as a core feature
                "logical_inference": args.logical_inference
            }
            
            # Process batch
            print("🚀 Starting batch processing...")
            
            summary = processor.process_batch(batch_items, workflow_options)
            
            # Export results
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            exported_files = processor.export_batch_results(batch_items, batch_id)
            report_path = processor.create_batch_report(batch_items, batch_id)
            
            # Print summary
            print("\n✅ Batch processing completed!")
            print(f"⏱️  Total time: {summary['total_processing_time']:.2f}s")
            print(f"📊 Results: {summary['completed']} completed, {summary['failed']} failed")
            print(f"📁 Exports saved to: {args.batch_export_dir}/")
            print(f"📄 Report: {report_path}")
            
            return
            
        except FileNotFoundError:
            print(f"❌ Batch file not found: {args.batch}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            print(f"❌ Batch processing failed: {e}")
            sys.exit(1)
    
    # Validate main workflow arguments
    if not args.theme:
        if args.remix:
            # For remix mode, use a default theme if not provided
            args.theme = "Creative Innovation"
            args.constraints = args.constraints or "Generate novel ideas based on previous concepts"
        else:
            parser.error("Theme is required for idea generation")
    
    if not args.constraints:
        args.constraints = "Generate practical and innovative ideas"
    
    # Setup temperature management
    try:
        temp_manager = create_temperature_manager_from_args(args)
        logger.info(temp_manager.describe_settings())
    except (ValueError, ValidationError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Handle remix mode
    if args.remix:
        logger.info("Running in remix mode - incorporating bookmarked ideas")
        try:
            args.constraints = remix_with_bookmarks(
                theme=args.theme,
                additional_constraints=args.constraints,
                bookmark_ids=args.remix_ids,
                bookmark_tags=args.bookmark_tags,
                bookmark_file=args.bookmark_file
            )
        except Exception as e:
            logger.error(f"Failed to setup remix mode: {e}")
            sys.exit(1)
    
    # Run the main workflow
    logger.info(f"Running MadSpark workflow with theme: '{args.theme}'")
    logger.info(f"Constraints: {args.constraints}")
    
    # Show progress message to user
    if os.getenv("MADSPARK_MODE") != "mock":
        print("\n🚀 Generating ideas with Google Gemini API...")
        print("⏳ This may take 30-60 seconds for quality results...\n")
    
    try:
        # Determine number of candidates and whether to use async mode
        num_candidates = determine_num_candidates(args)
        use_async = (hasattr(args, 'async') and getattr(args, 'async')) or (num_candidates > 1)
        
        # Extract common workflow arguments to avoid duplication
        workflow_kwargs = {
            "theme": args.theme,
            "constraints": args.constraints,
            "num_top_candidates": num_candidates,
            "enable_novelty_filter": not args.disable_novelty_filter,
            "novelty_threshold": args.similarity_threshold if args.similarity_threshold is not None else args.novelty_threshold,
            "temperature_manager": temp_manager,
            "verbose": args.verbose,
            "enhanced_reasoning": args.enhanced_reasoning,
            "multi_dimensional_eval": True,  # Always enabled as a core feature
            "logical_inference": args.logical_inference,
            "timeout": max(args.timeout, MIN_TIMEOUT_FOR_MULTIPLE_IDEAS_SECONDS) if num_candidates > 1 else args.timeout
        }

        if use_async:
            # Use async execution (auto-enabled for multiple ideas or explicitly requested)
            if num_candidates > 1:
                logger.info(f"Auto-enabling async mode for {num_candidates} ideas (estimated time: up to 5 minutes)")
                print(f"⚡ Processing {num_candidates} ideas in parallel for faster results...")
            else:
                logger.info("Using async execution for better performance")
            
            async def run_async():
                # Initialize cache manager if enabled
                cache_manager = None
                if hasattr(args, 'enable_cache') and args.enable_cache:
                    cache_config = CacheConfig(
                        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                        ttl_seconds=int(os.getenv("CACHE_TTL", "3600"))
                    )
                    cache_manager = CacheManager(cache_config)
                    await cache_manager.initialize()
                    logger.info("Cache enabled for async execution")
                
                # Progress callback for user feedback during multiple ideas processing
                async def progress_callback(message: str, progress: float):
                    if num_candidates > 1:
                        print(f"[{progress:.0%}] {message}")
                
                # Create async coordinator
                async_coordinator = AsyncCoordinator(
                    max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
                    progress_callback=progress_callback if num_candidates > 1 else None,
                    cache_manager=cache_manager
                )
                
                try:
                    return await async_coordinator.run_workflow(**workflow_kwargs)
                finally:
                    if cache_manager:
                        await cache_manager.close()
            
            results = asyncio.run(run_async())
        else:
            # Use synchronous execution
            results = run_multistep_workflow(**workflow_kwargs)
        
        if not results:
            print("No ideas were generated. Check the logs for details.")
            sys.exit(1)
        
        # Bookmark results by default (unless disabled)
        if not args.no_bookmark:
            logger.info(f"Bookmarking requested. Processing {len(results)} results...")
            manager = BookmarkManager(args.bookmark_file)
            bookmark_success = False
            for result in results:
                try:
                    # Get the best version of the idea (improved if available, otherwise original)
                    idea_text = result.get("improved_idea", "") or result.get("idea", "")
                    if not idea_text:
                        logger.warning("Cannot bookmark result: missing both 'improved_idea' and 'idea' fields")
                        print("⚠️  Warning: Result missing idea text, skipping bookmark")
                        continue
                    
                    # Use the best score (improved if available, otherwise initial)
                    score = result.get("improved_score", result.get("initial_score", 0))
                    
                    # Use the best critique (improved if available, otherwise initial)
                    critique = result.get("improved_critique", result.get("initial_critique", ""))
                    
                    # Use provided tags or empty list
                    bookmark_tags = args.bookmark_tags or []
                    
                    bookmark_id = manager.bookmark_idea(
                        idea_text=idea_text,
                        theme=args.theme,
                        constraints=args.constraints,
                        score=score,
                        critique=critique,
                        advocacy=result.get("advocacy", ""),
                        skepticism=result.get("skepticism", ""),
                        tags=bookmark_tags
                    )
                    
                    if bookmark_id:
                        bookmark_success = True
                        print(f"✅ Bookmarked result (ID: {bookmark_id})")
                        if bookmark_tags:
                            print(f"   Tags: {', '.join(bookmark_tags)}")
                        logger.info(f"Bookmarked result as {bookmark_id}")
                    else:
                        logger.warning("Bookmark creation returned no ID")
                        
                except Exception as e:
                    logger.error(f"Failed to bookmark result: {e}")
                    print(f"❌ Error saving bookmark: {e}")
                    
            if not bookmark_success and not args.no_bookmark:
                print("\n💡 Tip: To manually bookmark this result later, save the output to a file:")
                print(f"   ms \"{args.theme}\" \"{args.constraints}\" --output-file result.txt")
        
        # Export results if requested (Phase 2.2)
        if args.export:
            try:
                export_manager = ExportManager(args.export_dir)
                metadata = create_metadata_from_args(args, results)
                
                if args.export == 'all':
                    exported_files = export_manager.export_all_formats(
                        results, metadata, args.export_filename
                    )
                    print("\n📁 Export Results:")
                    for format_name, file_path in exported_files.items():
                        print(f"  {format_name.upper()}: {file_path}")
                else:
                    # Single format export - using dictionary mapping for maintainability
                    export_methods = {
                        'json': export_manager.export_to_json,
                        'csv': export_manager.export_to_csv,
                        'markdown': export_manager.export_to_markdown,
                        'pdf': export_manager.export_to_pdf,
                    }
                    
                    export_method = export_methods.get(args.export)
                    if export_method:
                        file_path = export_method(results, metadata, args.export_filename)
                        print(f"\n📄 Exported to {args.export.upper()}: {file_path}")
                    else:
                        logger.error(f"Unsupported export format: {args.export}")
                    
            except Exception as e:
                logger.error(f"Export failed: {e}")
                print(f"❌ Export failed: {e}")
        
        # Determine output format (prioritize --output-format over mode flags)
        output_format = args.output_format if args.output_format else args.output_mode
        
        # Format and output results
        formatted_output = format_results(results, output_format)
        
        # Check if automatic output file is needed for long outputs
        if not args.output_file and output_format == 'detailed' and (
            (args.top_ideas >= 3 and (args.enhanced_reasoning or args.logical_inference)) or
            len(formatted_output) > 5000  # More than ~100 lines
        ):
            # Auto-generate output filename
            import os
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            theme_slug = args.theme[:30].replace(' ', '_').replace('/', '_')
            auto_filename = f"output/markdown/madspark_{theme_slug}_{timestamp}.md"
            
            # Ensure output directory exists
            os.makedirs("output/markdown", exist_ok=True)
            
            # Save to file
            with open(auto_filename, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            
            # Show truncated version on screen
            from madspark.utils.output_processor import smart_truncate_text
            truncated_output = smart_truncate_text(formatted_output)
            print(truncated_output)
            print(f"\n📄 Full output saved to: {auto_filename}")
            logger.info(f"Auto-saved long output to {auto_filename}")
        
        elif args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            logger.info(f"Results saved to {args.output_file}")
        else:
            print(formatted_output)
            
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()