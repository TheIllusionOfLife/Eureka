"""Command Line Interface for MadSpark Multi-Agent System.

This module provides a comprehensive CLI for running the MadSpark workflow
with all Phase 1 features including temperature control, novelty filtering,
and bookmark management.
"""
import argparse
import json
import sys
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

# Import idea cleaner (removed unused import)

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.temperature_control import (
        TemperatureManager,
        add_temperature_arguments
    )
    from madspark.utils.bookmark_system import (
        BookmarkManager,
        list_bookmarks_cli
    )
except ImportError:
    # Fallback for local development/testing
    from temperature_control import (
        TemperatureManager,
        add_temperature_arguments
    )
    from bookmark_system import (
        BookmarkManager,
        list_bookmarks_cli
    )

# Import interactive mode after the try/except blocks
try:
    from madspark.cli.interactive_mode import run_interactive_mode
    from madspark.utils.batch_processor import create_sample_batch_file
except ImportError:
    from interactive_mode import run_interactive_mode
    from batch_processor import create_sample_batch_file

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

  # Multi-modal inputs: Analyze competitor website
  ms "Improve our landing page" "Increase conversions" --url https://competitor.com

  # Multi-modal inputs: Visual design inspiration
  ms "Modern app redesign" "Clean, minimal" --image mockup.png --image wireframe.jpg

  # Multi-modal inputs: Document analysis
  ms "Summarize research findings" "Key insights" --file research.pdf --file data.csv

  # Multi-modal inputs: Combined context
  ms "Product improvement ideas" "User-focused" --url https://reviews.com --file feedback.pdf --image current-ui.png

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
        default=1200,
        help='Request timeout in seconds (default: 1200, i.e., 20 minutes)'
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

    # LLM Provider options
    llm_group = parser.add_argument_group(
        'LLM provider options',
        'Control LLM provider selection, caching, and model tier'
    )

    llm_group.add_argument(
        '--provider',
        choices=['auto', 'ollama', 'gemini'],
        default='auto',
        help='LLM provider: auto (Ollama primary, Gemini fallback), ollama (local), gemini (cloud)'
    )

    llm_group.add_argument(
        '--model-tier',
        choices=['fast', 'balanced', 'quality'],
        default=None,
        help='Model quality tier: fast (4B, quick), balanced (12B, better), quality (Gemini, best)'
    )

    llm_group.add_argument(
        '--no-fallback',
        action='store_true',
        help='Disable fallback to secondary provider on failure'
    )

    llm_group.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching (re-generate every time)'
    )

    llm_group.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear LLM response cache before running'
    )

    llm_group.add_argument(
        '--show-llm-stats',
        action='store_true',
        help='Show LLM provider statistics (tokens, cost, cache hits)'
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

    # Multi-modal inputs
    multimodal_group = parser.add_argument_group(
        'multi-modal inputs',
        'Provide additional context via files and URLs for richer idea generation'
    )

    multimodal_group.add_argument(
        '--url', '-u',
        action='append',
        dest='multimodal_urls',
        metavar='URL',
        help='Add URL for context (e.g., competitor website, reference material). Can specify multiple times.'
    )

    multimodal_group.add_argument(
        '--file', '-f',
        action='append',
        dest='multimodal_files',
        metavar='PATH',
        help='Add file for context: PDF, text, markdown, or document. Can specify multiple times.'
    )

    multimodal_group.add_argument(
        '--image', '-img',
        action='append',
        dest='multimodal_images',
        metavar='PATH',
        help='Add image for visual context (PNG, JPG, JPEG, WebP, GIF, BMP). Can specify multiple times.'
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


def list_bookmarks_command(args: argparse.Namespace) -> None:
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


def search_bookmarks_command(args: argparse.Namespace) -> None:
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
        print(f"Topic: {bookmark.topic}")
        print(f"Score: {bookmark.score}")
        print("-" * 60)


def remove_bookmark_command(args: argparse.Namespace) -> None:
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
    if not agent_data:
        return {"formatted": f"No {agent_type} available", "structured": {}}
    
    # Handle both string (JSON) and dict inputs
    if isinstance(agent_data, str):
        if not agent_data.strip():
            return {"formatted": f"No {agent_type} available", "structured": {}}
        agent_data_str = agent_data
    else:
        # Already a dict, convert to JSON string for processing
        agent_data_str = json.dumps(agent_data)
    
    try:
        # Try to parse as JSON first
        if isinstance(agent_data, dict):
            structured_data = agent_data
        else:
            structured_data = json.loads(agent_data_str)
        
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
        
        else:
            # Unknown agent type - return structured data with default formatting
            fallback_text = json.dumps(structured_data, indent=2) if structured_data else agent_data
            return {"formatted": fallback_text, "structured": structured_data}
            
    except (json.JSONDecodeError, TypeError, ImportError):
        # Fall back to text format for backward compatibility
        fallback_text = agent_data if isinstance(agent_data, str) else str(agent_data)
        return {"formatted": fallback_text, "structured": {}}


def format_results(results: List[Dict[str, Any]], format_type: str, args=None) -> str:
    """Format results according to specified format using formatter strategy pattern.

    Args:
        results: List of workflow result dictionaries
        format_type: Output format ('brief', 'simple', 'detailed', 'summary', 'json', 'text')
        args: Command-line arguments namespace (optional, defaults to empty Namespace)

    Returns:
        Formatted string representation of results
    """
    try:
        from madspark.cli.formatters import FormatterFactory
    except ImportError:
        from .formatters import FormatterFactory

    # Create appropriate formatter using factory pattern
    formatter = FormatterFactory.create(format_type)

    # Use empty Namespace if args not provided (for backward compatibility)
    from argparse import Namespace
    if args is None:
        args = Namespace()

    # Format results using the selected formatter
    return formatter.format(results, args)


def determine_num_candidates(args) -> int:
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


def _validate_numeric_arguments(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Validate numeric arguments (timeout and similarity threshold).

    Args:
        args: Parsed command-line arguments
        parser: ArgumentParser instance for error reporting
    """
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


def _should_suppress_logs(args: argparse.Namespace) -> bool:
    """Determine if logging should be suppressed.

    Args:
        args: Parsed command-line arguments

    Returns:
        True if logs should be suppressed
    """
    # Respect explicit verbose flag - never suppress when user requests verbose output
    if getattr(args, 'verbose', False):
        return False

    return (
        getattr(args, 'no_logs', False) or
        getattr(args, 'output_mode', None) in ['simple', 'brief'] or
        getattr(args, 'output_format', None) in ['simple', 'brief']
    )


def _configure_llm_provider(args: argparse.Namespace) -> bool:
    """Configure LLM provider based on CLI arguments.

    Sets environment variables and initializes LLM router with user preferences.

    Args:
        args: Parsed command-line arguments

    Returns:
        True if an early exit is warranted (e.g., --clear-cache used alone),
        False otherwise.
    """
    # Set environment variables based on CLI args
    if getattr(args, 'provider', None):
        os.environ['MADSPARK_LLM_PROVIDER'] = args.provider

    if getattr(args, 'model_tier', None):
        os.environ['MADSPARK_MODEL_TIER'] = args.model_tier

    if getattr(args, 'no_fallback', False):
        os.environ['MADSPARK_FALLBACK_ENABLED'] = 'false'

    if getattr(args, 'no_cache', False):
        os.environ['MADSPARK_CACHE_ENABLED'] = 'false'

    # Handle cache operations
    if getattr(args, 'clear_cache', False):
        try:
            from madspark.llm import get_cache
            cache = get_cache()
            if cache.enabled:
                cache.clear()
                logger.info("LLM response cache cleared")
                print("🗑️  LLM response cache cleared")
            else:
                print("ℹ️  Cache is disabled, nothing to clear")
        except ImportError:
            logger.warning("LLM module not available for cache clearing")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

        # If this was the only major action, signal to main to exit
        is_other_action = any([
            getattr(args, 'theme', None),
            getattr(args, 'batch', None),
            getattr(args, 'interactive', False),
            getattr(args, 'list_bookmarks', False),
            getattr(args, 'search_bookmarks', None),
            getattr(args, 'remove_bookmark', None),
            getattr(args, 'create_sample_batch', None),
        ])
        if not is_other_action:
            return True

    return False


def _handle_create_sample_batch(args: argparse.Namespace) -> None:
    """Handle create sample batch file command.

    Args:
        args: Parsed command-line arguments
    """
    filename = f"sample_batch.{args.create_sample_batch}"
    create_sample_batch_file(filename, args.create_sample_batch)
    print(f"✅ Created sample batch file: {filename}")
    print(f"You can now run: python {sys.argv[0]} --batch {filename}")


def _handle_interactive_mode(args: argparse.Namespace) -> bool:
    """Handle interactive mode and update args.

    Args:
        args: Parsed command-line arguments (modified in place)

    Returns:
        True if interactive mode succeeded, False if cancelled/failed
    """
    try:
        session_data = run_interactive_mode()
        # Update args with interactive session data
        args.theme = session_data['topic']
        args.constraints = session_data['context']

        # Update args with config from interactive session
        config = session_data['config']
        for key, value in config.items():
            if hasattr(args, key):
                setattr(args, key, value)

        return True

    except KeyboardInterrupt:
        print("\n\n❌ Interactive session cancelled.")
        return False
    except Exception as e:
        print(f"\n❌ Error in interactive mode: {e}")
        return False


def main() -> None:
    """Main CLI entry point with command routing."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    # Validate numeric arguments
    _validate_numeric_arguments(args, parser)

    # Handle logging suppression
    if _should_suppress_logs(args):
        logging.getLogger().setLevel(logging.CRITICAL)
        os.environ["SUPPRESS_MODE_MESSAGE"] = "1"

    # Handle LLM provider configuration early
    if _configure_llm_provider(args):
        # Early exit requested (e.g., --clear-cache used alone)
        return

    # Import command handlers
    try:
        from madspark.cli.commands import (
            WorkflowValidator,
            WorkflowExecutor,
            BatchHandler,
            BookmarkHandler,
            ExportHandler
        )
    except ImportError:
        from commands import (
            WorkflowValidator,
            WorkflowExecutor,
            BatchHandler,
            BookmarkHandler,
            ExportHandler
        )

    # Get logger for handlers
    logger = logging.getLogger(__name__)

    # Handle standalone bookmark commands
    if args.list_bookmarks:
        BookmarkHandler.list_bookmarks(args)
        return

    if args.search_bookmarks:
        BookmarkHandler.search_bookmarks(args)
        return

    if args.remove_bookmark:
        BookmarkHandler.remove_bookmarks(args)
        return

    # Handle other standalone commands
    if hasattr(args, 'list_presets') and args.list_presets:
        print(TemperatureManager.describe_presets())
        return

    if args.create_sample_batch:
        _handle_create_sample_batch(args)
        return

    # Handle interactive mode
    if args.interactive:
        if not _handle_interactive_mode(args):
            return  # Interactive mode failed or was cancelled

    # Handle batch processing mode
    if args.batch:
        handler = BatchHandler(args, logger)
        result = handler.execute()
        sys.exit(result.exit_code)
    
    # Main workflow mode
    try:
        # Step 1: Validate arguments
        validator = WorkflowValidator(args, logger)
        validation_result = validator.execute()
        if not validation_result.success:
            sys.exit(validation_result.exit_code)

        temp_manager = validation_result.data['temp_manager']
        logger.info(f"Running MadSpark workflow with theme: '{args.theme}'")
        logger.info(f"Constraints: {args.constraints}")

        # Step 2: Execute workflow
        executor = WorkflowExecutor(args, logger, temp_manager)
        workflow_result = executor.execute()
        if not workflow_result.success:
            sys.exit(workflow_result.exit_code)

        results = workflow_result.data

        # Step 3: Bookmark results
        bookmark_handler = BookmarkHandler(args, logger)
        bookmark_handler.execute(results)

        # Step 4: Export results
        export_handler = ExportHandler(args, logger)
        export_handler.execute(results)
        
        # Determine output format (prioritize --output-format over mode flags)
        output_format = args.output_format if args.output_format else args.output_mode
        
        # Format and output results
        formatted_output = format_results(results, output_format, args)
        
        # Check if automatic output file is needed for long outputs
        num_ideas = args.top_ideas if args.top_ideas is not None else 1
        if not args.output_file and output_format == 'detailed' and (
            (num_ideas >= 3 and (args.enhanced_reasoning or args.logical_inference)) or
            len(formatted_output) > 5000  # More than ~100 lines
        ):
            # Auto-generate output filename
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

        # Show LLM provider statistics if requested
        if getattr(args, 'show_llm_stats', False):
            _show_llm_stats()

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        sys.exit(1)


def _show_llm_stats() -> None:
    """Display LLM provider usage statistics."""
    try:
        from madspark.llm import get_router, get_cache

        router = get_router()
        cache = get_cache()

        print("\n" + "=" * 50)
        print("📊 LLM Provider Statistics")
        print("=" * 50)

        # Router metrics
        metrics = router.get_metrics()
        print(f"Total Requests: {metrics['total_requests']}")
        print(f"  - Ollama Calls: {metrics['ollama_calls']}")
        print(f"  - Gemini Calls: {metrics['gemini_calls']}")
        print(f"  - Cache Hits: {metrics['cache_hits']}")
        print(f"  - Fallback Triggers: {metrics['fallback_triggers']}")
        print(f"Total Tokens: {metrics['total_tokens']}")
        print(f"Total Cost: ${metrics['total_cost']:.6f}")
        if metrics['total_requests'] > 0:
            print(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1%}")
            print(f"Avg Latency: {metrics['avg_latency_ms']:.0f}ms")

        # Cache stats
        if cache.enabled:
            cache_stats = cache.stats()
            print("\nCache Status:")
            print(f"  - Size: {cache_stats.get('size', 0)} entries")
            print(f"  - TTL: {cache_stats.get('ttl_seconds', 0)}s")

        # Health status
        health = router.health_status()
        print("\nProvider Health:")
        print(f"  - Ollama: {'✅' if health['ollama']['healthy'] else '❌'} "
              f"({health['ollama'].get('model', 'N/A')})")
        print(f"  - Gemini: {'✅' if health['gemini']['healthy'] else '❌'} "
              f"({health['gemini'].get('model', 'N/A')})")

        print("=" * 50)

    except ImportError:
        print("\n⚠️  LLM statistics not available (module not installed)")
    except Exception as e:
        logger.warning(f"Failed to show LLM stats: {e}")


if __name__ == "__main__":
    main()