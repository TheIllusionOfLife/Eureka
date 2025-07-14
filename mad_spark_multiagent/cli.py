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
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Import idea cleaner
from improved_idea_cleaner import clean_improved_idea

# Import MadSpark components with fallback for local development
try:
    from mad_spark_multiagent.coordinator import run_multistep_workflow
    from mad_spark_multiagent.async_coordinator import AsyncCoordinator
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
    from mad_spark_multiagent.export_utils import ExportManager, create_metadata_from_args
    from mad_spark_multiagent.cache_manager import CacheManager, CacheConfig
except ImportError:
    # Fallback for local development/testing
    from coordinator import run_multistep_workflow
    from async_coordinator import AsyncCoordinator
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
    from export_utils import ExportManager, create_metadata_from_args
    from cache_manager import CacheManager, CacheConfig

# Import interactive mode after the try/except blocks
try:
    from mad_spark_multiagent.interactive_mode import run_interactive_mode
    from mad_spark_multiagent.batch_processor import BatchProcessor, create_sample_batch_file
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
  
  # Enhanced reasoning with multi-dimensional evaluation
  %(prog)s "AI healthcare" "Rural deployment" --enhanced-reasoning --multi-dimensional-eval
  
  # Generate ideas based on bookmarks (remix)
  %(prog)s "Green energy" --remix --bookmark-tags renewable
  
  # Verbose mode with enhanced reasoning for detailed analysis
  %(prog)s "Sustainable agriculture" "Low-cost" --verbose --enhanced-reasoning
  
  # List saved bookmarks
  %(prog)s --list-bookmarks
  
  # Show temperature presets
  %(prog)s --list-presets
  
  # Batch processing
  %(prog)s --create-sample-batch csv
  %(prog)s --batch sample_batch.csv --batch-concurrent 5
  
  # Interactive mode
  %(prog)s --interactive
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
    
    # Interactive mode
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
    
    # Enhanced reasoning (Phase 2.1)
    reasoning_group = parser.add_argument_group('enhanced reasoning (Phase 2.1)')
    
    reasoning_group.add_argument(
        '--enhanced-reasoning',
        action='store_true',
        help='Enable enhanced reasoning capabilities with context awareness'
    )
    
    # Multi-dimensional evaluation is now always enabled
    # Keeping the argument for backward compatibility but it has no effect
    reasoning_group.add_argument(
        '--multi-dimensional-eval',
        action='store_true',
        help='(DEPRECATED: Always enabled) Multi-dimensional evaluation across 7 dimensions is now a core feature'
    )
    
    reasoning_group.add_argument(
        '--logical-inference',
        action='store_true',
        help='Enable logical inference chains for enhanced reasoning'
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
    # Apply cleaning to all results before formatting (consistent across all formats)
    from improved_idea_cleaner import clean_improved_ideas_in_results
    cleaned_results = clean_improved_ideas_in_results(results)
    
    if format_type == 'json':
        return json.dumps(cleaned_results, indent=2, ensure_ascii=False)
    
    elif format_type == 'summary':
<<<<<<< HEAD
        lines = [f"Generated {len(results)} improved ideas:\n"]
        for i, result in enumerate(results, 1):
            lines.append(f"--- IMPROVED IDEA {i} ---")
            
            # Clean and truncate improved ideas for summary view
            improved_idea = result.get('improved_idea', 'No improved idea available')
            if improved_idea != 'No improved idea available':
                improved_idea = clean_improved_idea(improved_idea)
=======
        lines = [f"Generated {len(cleaned_results)} improved ideas:\n"]
        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"--- IMPROVED IDEA {i} ---")
            
            # Get cleaned improved idea (already cleaned by clean_improved_ideas_in_results)
            improved_idea = result.get('improved_idea', 'No improved idea available')
>>>>>>> fc1c0dd9320f0bffb38b6b7327992a9cc51ee60d
            
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
                lines.append(f"\nMulti-Dimensional Evaluation:")
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
    
    else:  # text format
        lines = ["=" * 80]
        lines.append("MADSPARK MULTI-AGENT IDEA GENERATION RESULTS")
        lines.append("=" * 80)
        
        for i, result in enumerate(cleaned_results, 1):
            lines.append(f"\n--- IDEA {i} ---")
            lines.append(f"Text: {result['idea']}")
            lines.append(f"Initial Score: {result['initial_score']}")
            lines.append(f"Initial Critique: {result['initial_critique']}")
            lines.append(f"\nAdvocacy: {result['advocacy']}")
            lines.append(f"\nSkepticism: {result['skepticism']}")
            
            # Include cleaned improved idea in text format
            if 'improved_idea' in result:
                lines.append(f"\nImproved Idea: {result['improved_idea']}")
                lines.append(f"Improved Score: {result.get('improved_score', 'N/A')}")
            
            lines.append("-" * 80)
        
        return "\n".join(lines)


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
                print(f"❌ Unsupported batch file format. Use .csv or .json")
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
            start_time = datetime.now()
            
            summary = processor.process_batch(batch_items, workflow_options)
            
            # Export results
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            exported_files = processor.export_batch_results(batch_items, batch_id)
            report_path = processor.create_batch_report(batch_items, batch_id)
            
            # Print summary
            print(f"\n✅ Batch processing completed!")
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
        # Extract common workflow arguments to avoid duplication
        workflow_kwargs = {
            "theme": args.theme,
            "constraints": args.constraints,
            "num_top_candidates": args.num_candidates,
            "enable_novelty_filter": not args.disable_novelty_filter,
            "novelty_threshold": args.novelty_threshold,
            "temperature_manager": temp_manager,
            "verbose": args.verbose,
            "enhanced_reasoning": args.enhanced_reasoning,
            "multi_dimensional_eval": True,  # Always enabled as a core feature
            "logical_inference": args.logical_inference,
            "timeout": args.timeout
        }

        if hasattr(args, 'async') and getattr(args, 'async'):
            # Use async execution
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
                
                # Create async coordinator
                async_coordinator = AsyncCoordinator(
                    max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
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
        
        # Export results if requested (Phase 2.2)
        if args.export:
            try:
                export_manager = ExportManager(args.export_dir)
                metadata = create_metadata_from_args(args, results)
                
                if args.export == 'all':
                    exported_files = export_manager.export_all_formats(
                        results, metadata, args.export_filename
                    )
                    print(f"\n📁 Export Results:")
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