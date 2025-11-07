"""Export management command handler."""

import argparse
import logging
from typing import List, Dict, Any

from .base import CommandHandler, CommandResult

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.export_utils import ExportManager, create_metadata_from_args
except ImportError:
    from export_utils import ExportManager, create_metadata_from_args


class ExportHandler(CommandHandler):
    """Handles result export operations.

    This handler is responsible for:
    - Exporting results to various formats (JSON, CSV, Markdown, PDF)
    - Managing export directory
    - Generating export metadata
    """

    def execute(self, results: List[Dict[str, Any]]) -> CommandResult:
        """Export results to requested format(s).

        Args:
            results: List of workflow results to export

        Returns:
            CommandResult with success status
        """
        # Skip if export is not requested
        if not self.args.export:
            return CommandResult(success=True)

        try:
            export_manager = ExportManager(self.args.export_dir)
            metadata = create_metadata_from_args(self.args, results)

            if self.args.export == 'all':
                exported_files = self._export_all_formats(export_manager, results, metadata)
                self._print_export_summary(exported_files)
            else:
                file_path = self._export_single_format(export_manager, results, metadata)
                self._print_single_export(file_path, self.args.export)

            return CommandResult(success=True)

        except Exception as e:
            self.log_error(f"Export failed: {e}")
            print(f"❌ Export failed: {e}")
            return CommandResult(success=False, message=str(e))

    def _export_all_formats(self, export_manager: ExportManager,
                           results: List[Dict[str, Any]],
                           metadata: Dict[str, Any]) -> Dict[str, str]:
        """Export to all supported formats.

        Args:
            export_manager: ExportManager instance
            results: Results to export
            metadata: Export metadata

        Returns:
            Dictionary mapping format names to file paths
        """
        return export_manager.export_all_formats(
            results, metadata, self.args.export_filename
        )

    def _export_single_format(self, export_manager: ExportManager,
                             results: List[Dict[str, Any]],
                             metadata: Dict[str, Any]) -> str:
        """Export to a single format.

        Args:
            export_manager: ExportManager instance
            results: Results to export
            metadata: Export metadata

        Returns:
            Path to exported file

        Raises:
            ValueError: If export format is unsupported
        """
        # Dictionary mapping for maintainability
        export_methods = {
            'json': export_manager.export_to_json,
            'csv': export_manager.export_to_csv,
            'markdown': export_manager.export_to_markdown,
            'pdf': export_manager.export_to_pdf,
        }

        export_method = export_methods.get(self.args.export)
        if export_method:
            return export_method(results, metadata, self.args.export_filename)
        else:
            error_msg = f"Unsupported export format: {self.args.export}"
            self.log_error(error_msg)
            raise ValueError(error_msg)

    def _print_export_summary(self, exported_files: Dict[str, str]) -> None:
        """Print summary of exported files.

        Args:
            exported_files: Dictionary mapping format names to file paths
        """
        print("\n📁 Export Results:")
        for format_name, file_path in exported_files.items():
            print(f"  {format_name.upper()}: {file_path}")

    def _print_single_export(self, file_path: str, format_name: str) -> None:
        """Print single export result.

        Args:
            file_path: Path to exported file
            format_name: Name of the export format
        """
        print(f"\n📄 Exported to {format_name.upper()}: {file_path}")
