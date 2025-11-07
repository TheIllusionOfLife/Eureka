"""Batch processing command handler."""

from datetime import datetime
from typing import List, Dict, Any

from .base import CommandHandler, CommandResult

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.batch_processor import BatchProcessor
except ImportError:
    from batch_processor import BatchProcessor


class BatchHandler(CommandHandler):
    """Handles batch processing of multiple themes.

    This handler is responsible for:
    - Loading batch items from CSV/JSON files
    - Configuring and running batch processor
    - Exporting batch results and generating reports
    """

    def execute(self) -> CommandResult:
        """Execute batch processing workflow.

        Returns:
            CommandResult with success status and summary data
        """
        try:
            # Validate batch file format
            if not self.args.batch.endswith(('.csv', '.json')):
                error_msg = "Unsupported batch file format. Use .csv or .json"
                print(f"❌ {error_msg}")
                return CommandResult(success=False, exit_code=1, message=error_msg)

            self.log_info(f"Starting batch processing from: {self.args.batch}")

            # Create and configure batch processor
            processor = self._create_batch_processor()

            # Load batch items
            batch_items = self._load_batch_items(processor)
            print(f"📋 Loaded {len(batch_items)} items for batch processing")

            # Prepare workflow options
            workflow_options = self._prepare_workflow_options()

            # Process batch
            print("🚀 Starting batch processing...")
            summary = processor.process_batch(batch_items, workflow_options)

            # Export results and generate report
            self._export_and_report(processor, batch_items, summary)

            return CommandResult(success=True, data=summary)

        except FileNotFoundError:
            error_msg = f"Batch file not found: {self.args.batch}"
            self.log_error(error_msg)
            print(f"❌ {error_msg}")
            return CommandResult(success=False, exit_code=1, message=error_msg)
        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            self.log_error(error_msg)
            print(f"❌ {error_msg}")
            return CommandResult(success=False, exit_code=1, message=str(e))

    def _create_batch_processor(self) -> BatchProcessor:
        """Create and configure batch processor.

        Returns:
            Configured BatchProcessor instance
        """
        return BatchProcessor(
            max_concurrent=self.args.batch_concurrent,
            use_async=hasattr(self.args, 'async') and getattr(self.args, 'async'),
            enable_cache=self.args.enable_cache,
            export_dir=self.args.batch_export_dir,
            verbose=self.args.verbose
        )

    def _load_batch_items(self, processor: BatchProcessor) -> List:
        """Load batch items from file.

        Args:
            processor: BatchProcessor instance

        Returns:
            List of batch items

        Raises:
            FileNotFoundError: If batch file doesn't exist
        """
        if self.args.batch.endswith('.csv'):
            return processor.load_batch_from_csv(self.args.batch)
        elif self.args.batch.endswith('.json'):
            return processor.load_batch_from_json(self.args.batch)
        else:
            # This shouldn't happen due to earlier validation, but just in case
            raise ValueError("Unsupported batch file format")

    def _prepare_workflow_options(self) -> Dict[str, Any]:
        """Prepare workflow options for batch processing.

        Returns:
            Dictionary of workflow options
        """
        return {
            "enable_novelty_filter": not self.args.disable_novelty_filter,
            "novelty_threshold": self.args.novelty_threshold,
            "verbose": self.args.verbose,
            "enhanced_reasoning": self.args.enhanced_reasoning,
            "multi_dimensional_eval": True,  # Always enabled as a core feature
            "logical_inference": self.args.logical_inference
        }

    def _export_and_report(self, processor: BatchProcessor, batch_items: List, summary: Dict) -> None:
        """Export results and create batch report.

        Args:
            processor: BatchProcessor instance
            batch_items: List of batch items
            summary: Processing summary dictionary
        """
        # Generate batch ID
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export results
        processor.export_batch_results(batch_items, batch_id)

        # Create report
        report_path = processor.create_batch_report(batch_items, batch_id)

        # Print summary
        print("\n✅ Batch processing completed!")
        print(f"⏱️  Total time: {summary['total_processing_time']:.2f}s")
        print(f"📊 Results: {summary['completed']} completed, {summary['failed']} failed")
        print(f"📁 Exports saved to: {self.args.batch_export_dir}/")
        print(f"📄 Report: {report_path}")
