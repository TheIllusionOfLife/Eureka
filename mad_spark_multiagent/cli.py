"""Command Line Interface for MadSpark Multi-Agent System.

This module provides a comprehensive CLI for running the MadSpark workflow
with all Phase 1 features including temperature control, novelty filtering,
and bookmark management.
"""
import argparse
import json
import sys
import os
from typing import List, Dict, Any, Optional
import logging

# Import MadSpark components with fallback for local development
try:
    from mad_spark_multiagent.coordinator import run_multistep_workflow
    from mad_spark_multiagent.temperature_control import (
        TemperatureManager, 
        add_temperature_arguments,
        create_temperature_manager_from_args
    )
    from mad_spark_multiagent.bookmark_system import (
        BookmarkManager,
        bookmark_from_result,
        list_bookmarks_cli,
        remix_with_bookmarks
    )
except ImportError:
    # Fallback for local development/testing
    from coordinator import run_multistep_workflow
    from temperature_control import (
        TemperatureManager, 
        add_temperature_arguments,
        create_temperature_manager_from_args
    )
    from bookmark_system import (
        BookmarkManager,
        bookmark_from_result,
        list_bookmarks_cli,
        remix_with_bookmarks
    )

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory if verbose mode is enabled
    if verbose:
        import os
        from datetime import datetime
        os.makedirs("logs", exist_ok=True)
        
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
            ]
        )
        
        print(f"📁 Verbose logs will be saved to: {log_file}")
    else:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description='MadSpark Multi-Agent Idea Generation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s "Future transportation" "Budget-friendly, eco-friendly"
  
  # High creativity with novelty filtering
  %(prog)s "Smart cities" "Scalable solutions" -tp creative --novelty-threshold 0.6
  
  # Generate ideas based on bookmarks (remix)
  %(prog)s "Green energy" --remix --bookmark-tags renewable
  
  # List saved bookmarks
  %(prog)s --list-bookmarks
  
  # Show temperature presets
  %(prog)s --list-presets
        """
    )
    
    # Positional arguments for basic workflow
    parser.add_argument(
        'theme',
        nargs='?',
        help='Theme for idea generation'
    )
    
    parser.add_argument(
        'constraints',
        nargs='?',
        help='Constraints and criteria for idea generation'
    )
    
    # Workflow options
    workflow_group = parser.add_argument_group('workflow options')
    
    workflow_group.add_argument(
        '--num-candidates', '-n',
        type=int,
        default=2,
        help='Number of top candidates to fully process (default: 2)'
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
    
    # Temperature control
    add_temperature_arguments(parser)
    
    # Bookmark management
    bookmark_group = parser.add_argument_group('bookmark management')
    
    bookmark_group.add_argument(
        '--bookmark-results',
        action='store_true',
        help='Automatically bookmark generated results'
    )
    
    bookmark_group.add_argument(
        '--bookmark-tags',
        nargs='*',
        help='Tags to apply when bookmarking results'
    )
    
    bookmark_group.add_argument(
        '--bookmark-file',
        default='bookmarks.json',
        help='File to store bookmarks (default: bookmarks.json)'
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
    
    # Output options
    output_group = parser.add_argument_group('output options')
    
    output_group.add_argument(
        '--output-format',
        choices=['json', 'text', 'summary'],
        default='text',
        help='Output format (default: text)'
    )
    
    output_group.add_argument(
        '--output-file',
        help='Save results to file instead of stdout'
    )
    
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def list_bookmarks_command(args: argparse.Namespace):
    """Handle the list bookmarks command."""
    bookmarks = list_bookmarks_cli(args.bookmark_file)
    
    if not bookmarks:
        print("No bookmarks found.")
        return
    
    print(f"Found {len(bookmarks)} bookmarks:\n")
    
    for bookmark in bookmarks:
        print(f"ID: {bookmark['id']}")
        print(f"Text: {bookmark['text']}")
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
        print(f"Text: {bookmark.text}")
        print(f"Theme: {bookmark.theme}")
        print(f"Score: {bookmark.score}")
        print("-" * 60)


def format_results(results: List[Dict[str, Any]], format_type: str) -> str:
    """Format results according to specified format."""
    if format_type == 'json':
        return json.dumps(results, indent=2, ensure_ascii=False)
    
    elif format_type == 'summary':
        lines = [f"Generated {len(results)} ideas:\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result['idea']}")
            lines.append(f"   Score: {result['initial_score']}")
        return "\n".join(lines)
    
    else:  # text format
        lines = ["=" * 80]
        lines.append("MADSPARK MULTI-AGENT IDEA GENERATION RESULTS")
        lines.append("=" * 80)
        
        for i, result in enumerate(results, 1):
            lines.append(f"\n--- IDEA {i} ---")
            lines.append(f"Text: {result['idea']}")
            lines.append(f"Initial Score: {result['initial_score']}")
            lines.append(f"Initial Critique: {result['initial_critique']}")
            lines.append(f"\nAdvocacy: {result['advocacy']}")
            lines.append(f"\nSkepticism: {result['skepticism']}")
            lines.append("-" * 80)
        
        return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Handle standalone commands
    if args.list_bookmarks:
        list_bookmarks_command(args)
        return
    
    if args.search_bookmarks:
        search_bookmarks_command(args)
        return
    
    if hasattr(args, 'list_presets') and args.list_presets:
        print(TemperatureManager.describe_presets())
        return
    
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
    except ValueError as e:
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
                bookmark_file=args.bookmark_file
            )
        except Exception as e:
            logger.error(f"Failed to setup remix mode: {e}")
            sys.exit(1)
    
    # Run the main workflow
    logger.info(f"Running MadSpark workflow with theme: '{args.theme}'")
    logger.info(f"Constraints: {args.constraints}")
    
    try:
        results = run_multistep_workflow(
            theme=args.theme,
            constraints=args.constraints,
            num_top_candidates=args.num_candidates,
            enable_novelty_filter=not args.disable_novelty_filter,
            novelty_threshold=args.novelty_threshold,
            temperature_manager=temp_manager,
            verbose=args.verbose
        )
        
        if not results:
            print("No ideas were generated. Check the logs for details.")
            sys.exit(1)
        
        # Bookmark results if requested
        if args.bookmark_results:
            manager = BookmarkManager(args.bookmark_file)
            for result in results:
                bookmark_id = manager.bookmark_idea(
                    idea_text=result.get("idea", ""),
                    theme=args.theme,
                    constraints=args.constraints,
                    score=result.get("initial_score", 0),
                    critique=result.get("initial_critique", ""),
                    advocacy=result.get("advocacy", ""),
                    skepticism=result.get("skepticism", ""),
                    tags=args.bookmark_tags or []
                )
                logger.info(f"Bookmarked result as {bookmark_id}")
        
        # Format and output results
        formatted_output = format_results(results, args.output_format)
        
        if args.output_file:
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