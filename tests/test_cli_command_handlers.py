"""Tests for CLI command handlers.

Following TDD principles, these tests are written BEFORE implementation
to define the expected behavior of each command handler.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
import argparse
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any


# Test fixtures
@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def basic_args():
    """Create basic argument namespace for testing."""
    args = argparse.Namespace()
    args.theme = "Test Theme"
    args.constraints = "Test Constraints"
    args.verbose = False
    args.timeout = 60
    args.similarity_threshold = 0.7
    args.novelty_threshold = 0.7
    args.disable_novelty_filter = False
    args.enhanced_reasoning = False
    args.logical_inference = False
    args.top_ideas = None
    args.no_bookmark = False
    args.bookmark_file = "bookmarks.json"
    args.bookmark_tags = []
    args.export = None
    args.export_dir = "output"
    args.export_filename = None
    args.output_format = "detailed"
    args.output_mode = "detailed"
    args.output_file = None
    args.enable_cache = False
    args.batch = None
    args.batch_concurrent = 5
    args.batch_export_dir = "batch_results"
    args.interactive = False
    args.remix = False
    args.remix_ids = None
    return args


# Tests for CommandResult dataclass
class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_success(self):
        """Test CommandResult with success status."""
        from madspark.cli.commands.base import CommandResult

        result = CommandResult(success=True, exit_code=0, message="Success")
        assert result.success is True
        assert result.exit_code == 0
        assert result.message == "Success"
        assert result.data is None

    def test_command_result_with_data(self):
        """Test CommandResult with data payload."""
        from madspark.cli.commands.base import CommandResult

        test_data = {"key": "value", "count": 42}
        result = CommandResult(success=True, data=test_data)
        assert result.success is True
        assert result.data == test_data

    def test_command_result_failure(self):
        """Test CommandResult with failure status."""
        from madspark.cli.commands.base import CommandResult

        result = CommandResult(success=False, exit_code=1, message="Error occurred")
        assert result.success is False
        assert result.exit_code == 1
        assert result.message == "Error occurred"


# Tests for CommandHandler base class
class TestCommandHandler:
    """Tests for CommandHandler abstract base class."""

    def test_command_handler_cannot_be_instantiated(self, basic_args, mock_logger):
        """Test that CommandHandler is abstract and cannot be instantiated."""
        from madspark.cli.commands.base import CommandHandler

        with pytest.raises(TypeError):
            CommandHandler(basic_args, mock_logger)

    def test_command_handler_requires_execute_method(self, basic_args, mock_logger):
        """Test that subclasses must implement execute method."""
        from madspark.cli.commands.base import CommandHandler

        # Create a subclass without execute method
        class IncompleteHandler(CommandHandler):
            pass

        with pytest.raises(TypeError):
            IncompleteHandler(basic_args, mock_logger)

    def test_command_handler_logging_methods(self, basic_args, mock_logger):
        """Test that logging helper methods work correctly."""
        from madspark.cli.commands.base import CommandHandler, CommandResult

        # Create concrete implementation for testing
        class TestHandler(CommandHandler):
            def execute(self):
                return CommandResult(success=True)

        handler = TestHandler(basic_args, mock_logger)

        # Test logging methods
        handler.log_info("Test info")
        mock_logger.info.assert_called_once_with("Test info")

        handler.log_error("Test error")
        mock_logger.error.assert_called_once_with("Test error")

        handler.log_warning("Test warning")
        mock_logger.warning.assert_called_once_with("Test warning")


# Tests for WorkflowValidator
class TestWorkflowValidator:
    """Tests for WorkflowValidator command handler."""

    def test_validates_theme_required(self, mock_logger):
        """Test that theme validation works - theme is required."""
        from madspark.cli.commands.validation import WorkflowValidator
        from madspark.cli.commands.base import CommandResult

        # Create args without theme
        args = argparse.Namespace()
        args.theme = None
        args.constraints = "Test constraints"
        args.remix = False
        args.temperature_preset = None
        args.temp_idea = 0.9
        args.temp_critic = 0.3
        args.temp_refiner = 0.7

        validator = WorkflowValidator(args, mock_logger)
        result = validator.execute()

        # Should fail when theme is missing and not in remix mode
        assert result.success is False
        assert result.exit_code == 1

    def test_allows_missing_theme_in_remix_mode(self, mock_logger):
        """Test that remix mode provides default theme."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = argparse.Namespace()
        args.theme = None
        args.constraints = None
        args.remix = True
        args.remix_ids = None
        args.bookmark_tags = None
        args.bookmark_file = "bookmarks.json"
        args.temperature_preset = None
        args.temp_idea = 0.9
        args.temp_critic = 0.3
        args.temp_refiner = 0.7

        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args'):
            with patch('madspark.cli.commands.validation.remix_with_bookmarks', return_value="Enhanced constraints"):
                validator = WorkflowValidator(args, mock_logger)
                result = validator.execute()

                assert result.success is True
                assert args.theme == "Creative Innovation"  # Default theme for remix

    def test_provides_default_constraints(self, mock_logger):
        """Test that default constraints are provided when missing."""
        from madspark.cli.commands.validation import WorkflowValidator

        args = argparse.Namespace()
        args.theme = "Test Theme"
        args.constraints = None
        args.remix = False
        args.temperature_preset = None
        args.temp_idea = 0.9
        args.temp_critic = 0.3
        args.temp_refiner = 0.7

        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args'):
            validator = WorkflowValidator(args, mock_logger)
            result = validator.execute()

            assert result.success is True
            assert args.constraints == "Generate practical and innovative ideas"

    def test_temperature_manager_creation(self, basic_args, mock_logger):
        """Test temperature manager setup from args."""
        from madspark.cli.commands.validation import WorkflowValidator

        basic_args.temperature_preset = None
        basic_args.temp_idea = 0.9
        basic_args.temp_critic = 0.3
        basic_args.temp_refiner = 0.7

        mock_temp_manager = Mock()
        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args', return_value=mock_temp_manager):
            validator = WorkflowValidator(basic_args, mock_logger)
            result = validator.execute()

            assert result.success is True
            assert result.data['temp_manager'] == mock_temp_manager
            assert result.data['theme'] == basic_args.theme
            assert result.data['constraints'] == basic_args.constraints

    def test_remix_mode_integration(self, basic_args, mock_logger):
        """Test remix mode handling."""
        from madspark.cli.commands.validation import WorkflowValidator

        basic_args.remix = True
        basic_args.remix_ids = [1, 2, 3]
        basic_args.bookmark_tags = ["tag1", "tag2"]
        basic_args.temperature_preset = None
        basic_args.temp_idea = 0.9
        basic_args.temp_critic = 0.3
        basic_args.temp_refiner = 0.7

        original_constraints = basic_args.constraints  # Store original value

        mock_temp_manager = Mock()
        enhanced_constraints = "Enhanced with bookmarked ideas"

        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args', return_value=mock_temp_manager):
            with patch('madspark.cli.commands.validation.remix_with_bookmarks', return_value=enhanced_constraints) as mock_remix:
                validator = WorkflowValidator(basic_args, mock_logger)
                result = validator.execute()

                assert result.success is True
                assert basic_args.constraints == enhanced_constraints
                mock_remix.assert_called_once_with(
                    theme=basic_args.theme,
                    additional_constraints=original_constraints,  # Use original value
                    bookmark_ids=basic_args.remix_ids,
                    bookmark_tags=basic_args.bookmark_tags,
                    bookmark_file=basic_args.bookmark_file
                )

    def test_validation_error_handling(self, basic_args, mock_logger):
        """Test handling of validation errors."""
        from madspark.cli.commands.validation import WorkflowValidator
        from madspark.utils.errors import ValidationError

        basic_args.temperature_preset = None
        basic_args.temp_idea = 0.9
        basic_args.temp_critic = 0.3
        basic_args.temp_refiner = 0.7

        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args', side_effect=ValidationError("Invalid temperature")):
            validator = WorkflowValidator(basic_args, mock_logger)
            result = validator.execute()

            assert result.success is False
            assert result.exit_code == 1


# Tests for WorkflowExecutor
class TestWorkflowExecutor:
    """Tests for WorkflowExecutor command handler."""

    def test_sync_execution(self, basic_args, mock_logger):
        """Test synchronous workflow execution."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()
        basic_args.top_ideas = None  # Single idea

        mock_results = [{"idea": "Test idea", "score": 85}]

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results):
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                result = executor.execute()

                assert result.success is True
                assert result.data == mock_results

    def test_async_execution_single_idea(self, basic_args, mock_logger):
        """Test async execution with single idea (explicitly requested)."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()
        basic_args.top_ideas = None
        setattr(basic_args, 'async', True)  # Explicitly request async

        mock_results = [{"idea": "Test idea", "score": 85}]

        with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
            with patch('madspark.cli.commands.workflow_executor.asyncio.run') as mock_async_run:
                mock_async_run.return_value = mock_results

                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                result = executor.execute()

                assert result.success is True
                assert result.data == mock_results
                mock_async_run.assert_called_once()

    def test_async_execution_multiple_ideas(self, basic_args, mock_logger):
        """Test async execution with multiple ideas (auto-enabled)."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()
        basic_args.top_ideas = 3
        setattr(basic_args, 'async', False)  # Not explicitly requested

        mock_results = [
            {"idea": "Idea 1", "score": 85},
            {"idea": "Idea 2", "score": 82},
            {"idea": "Idea 3", "score": 80}
        ]

        with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=3):
            with patch('madspark.cli.commands.workflow_executor.asyncio.run') as mock_async_run:
                mock_async_run.return_value = mock_results

                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                result = executor.execute()

                assert result.success is True
                assert result.data == mock_results
                # Should auto-enable async for multiple ideas
                mock_async_run.assert_called_once()

    def test_cache_manager_integration(self, basic_args, mock_logger):
        """Test cache manager setup when enabled."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()
        basic_args.enable_cache = True
        setattr(basic_args, 'async', True)

        mock_results = [{"idea": "Test idea", "score": 85}]

        with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
            with patch('madspark.cli.commands.workflow_executor.asyncio.run') as mock_async_run:
                mock_async_run.return_value = mock_results

                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                result = executor.execute()

                assert result.success is True
                # Cache manager should be initialized in async workflow
                mock_async_run.assert_called_once()

    def test_workflow_kwargs_construction(self, basic_args, mock_logger):
        """Test that workflow kwargs are constructed correctly."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()
        basic_args.top_ideas = 2
        basic_args.enhanced_reasoning = True
        basic_args.logical_inference = True

        mock_results = [{"idea": "Test", "score": 85}]

        with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=2):
            with patch('madspark.cli.commands.workflow_executor.asyncio.run', return_value=mock_results) as mock_run:
                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                executor.execute()

                # Verify async.run was called (which means kwargs were passed to async workflow)
                mock_run.assert_called_once()

    def test_no_results_handling(self, basic_args, mock_logger):
        """Test handling when no results are generated."""
        from madspark.cli.commands.workflow_executor import WorkflowExecutor

        mock_temp_manager = Mock()

        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=None):
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(basic_args, mock_logger, mock_temp_manager)
                result = executor.execute()

                assert result.success is False
                assert result.exit_code == 1


# Tests for BatchHandler
class TestBatchHandler:
    """Tests for BatchHandler command handler."""

    def test_csv_batch_loading(self, basic_args, mock_logger):
        """Test CSV batch file loading."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "test.csv"

        mock_processor = Mock()
        mock_batch_items = [
            {"theme": "Theme1", "constraints": "Context1"},
            {"theme": "Theme2", "constraints": "Context2"}
        ]
        mock_processor.load_batch_from_csv.return_value = mock_batch_items
        mock_processor.process_batch.return_value = {
            'total_processing_time': 10.5,
            'completed': 2,
            'failed': 0
        }
        mock_processor.export_batch_results.return_value = {}
        mock_processor.create_batch_report.return_value = "report.txt"

        with patch('madspark.cli.commands.batch_handler.BatchProcessor', return_value=mock_processor):
            handler = BatchHandler(basic_args, mock_logger)
            result = handler.execute()

            assert result.success is True
            mock_processor.load_batch_from_csv.assert_called_once_with("test.csv")

    def test_json_batch_loading(self, basic_args, mock_logger):
        """Test JSON batch file loading."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "test.json"

        mock_processor = Mock()
        mock_batch_items = [
            {"theme": "Theme1", "constraints": "Context1"}
        ]
        mock_processor.load_batch_from_json.return_value = mock_batch_items
        mock_processor.process_batch.return_value = {
            'total_processing_time': 5.2,
            'completed': 1,
            'failed': 0
        }
        mock_processor.export_batch_results.return_value = {}
        mock_processor.create_batch_report.return_value = "report.txt"

        with patch('madspark.cli.commands.batch_handler.BatchProcessor', return_value=mock_processor):
            handler = BatchHandler(basic_args, mock_logger)
            result = handler.execute()

            assert result.success is True
            mock_processor.load_batch_from_json.assert_called_once_with("test.json")

    def test_unsupported_format_error(self, basic_args, mock_logger):
        """Test error handling for unsupported batch file formats."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "test.txt"

        handler = BatchHandler(basic_args, mock_logger)
        result = handler.execute()

        assert result.success is False
        assert result.exit_code == 1

    def test_batch_execution(self, basic_args, mock_logger):
        """Test batch processing execution."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "test.csv"
        basic_args.enhanced_reasoning = True
        basic_args.logical_inference = True

        mock_processor = Mock()
        mock_batch_items = [{"theme": "Test", "constraints": "Context"}]
        mock_processor.load_batch_from_csv.return_value = mock_batch_items

        mock_summary = {
            'total_processing_time': 15.3,
            'completed': 1,
            'failed': 0
        }
        mock_processor.process_batch.return_value = mock_summary
        mock_processor.export_batch_results.return_value = {}
        mock_processor.create_batch_report.return_value = "report.txt"

        with patch('madspark.cli.commands.batch_handler.BatchProcessor', return_value=mock_processor):
            handler = BatchHandler(basic_args, mock_logger)
            result = handler.execute()

            assert result.success is True
            assert result.data == mock_summary

            # Verify workflow options were passed correctly
            call_args = mock_processor.process_batch.call_args
            workflow_options = call_args[0][1]
            assert workflow_options['enhanced_reasoning'] is True
            assert workflow_options['logical_inference'] is True

    def test_file_not_found_error(self, basic_args, mock_logger):
        """Test handling of missing batch file."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "nonexistent.csv"

        mock_processor = Mock()
        mock_processor.load_batch_from_csv.side_effect = FileNotFoundError()

        with patch('madspark.cli.commands.batch_handler.BatchProcessor', return_value=mock_processor):
            handler = BatchHandler(basic_args, mock_logger)
            result = handler.execute()

            assert result.success is False
            assert result.exit_code == 1


# Tests for BookmarkHandler
class TestBookmarkHandler:
    """Tests for BookmarkHandler command handler."""

    def test_bookmark_results_success(self, basic_args, mock_logger):
        """Test successful bookmarking of workflow results."""
        from madspark.cli.commands.bookmark_handler import BookmarkHandler

        results = [
            {
                "improved_idea": "Improved idea 1",
                "idea": "Original idea 1",
                "improved_score": 90,
                "initial_score": 85,
                "improved_critique": "Great improvement",
                "initial_critique": "Good start",
                "advocacy": "Strong support",
                "skepticism": "Minor concerns"
            }
        ]

        mock_manager = Mock()
        mock_manager.bookmark_idea.return_value = "BM123"

        with patch('madspark.cli.commands.bookmark_handler.BookmarkManager', return_value=mock_manager):
            handler = BookmarkHandler(basic_args, mock_logger)
            result = handler.execute(results)

            assert result.success is True
            mock_manager.bookmark_idea.assert_called_once()

    def test_bookmark_with_tags(self, basic_args, mock_logger):
        """Test bookmark tagging."""
        from madspark.cli.commands.bookmark_handler import BookmarkHandler

        basic_args.bookmark_tags = ["innovation", "ai"]

        results = [
            {
                "improved_idea": "Tagged idea",
                "improved_score": 88
            }
        ]

        mock_manager = Mock()
        mock_manager.bookmark_idea.return_value = "BM456"

        with patch('madspark.cli.commands.bookmark_handler.BookmarkManager', return_value=mock_manager):
            handler = BookmarkHandler(basic_args, mock_logger)
            result = handler.execute(results)

            assert result.success is True
            # Verify tags were passed
            call_args = mock_manager.bookmark_idea.call_args
            assert call_args[1]['tags'] == ["innovation", "ai"]

    def test_no_bookmark_flag(self, basic_args, mock_logger):
        """Test that bookmarking is skipped when disabled."""
        from madspark.cli.commands.bookmark_handler import BookmarkHandler

        basic_args.no_bookmark = True
        results = [{"idea": "Test", "score": 80}]

        handler = BookmarkHandler(basic_args, mock_logger)
        result = handler.execute(results)

        assert result.success is True
        # No bookmark operations should occur

    def test_missing_idea_text_handling(self, basic_args, mock_logger):
        """Test handling of results missing idea text."""
        from madspark.cli.commands.bookmark_handler import BookmarkHandler

        results = [
            {"score": 80}  # Missing both 'idea' and 'improved_idea'
        ]

        mock_manager = Mock()

        with patch('madspark.cli.commands.bookmark_handler.BookmarkManager', return_value=mock_manager):
            handler = BookmarkHandler(basic_args, mock_logger)
            result = handler.execute(results)

            # Should complete but with warnings
            assert result.success is True
            # bookmark_idea should not be called for invalid results
            mock_manager.bookmark_idea.assert_not_called()

    def test_list_bookmarks_static(self, basic_args, mock_logger):
        """Test static list bookmarks method."""
        from madspark.cli.commands.bookmark_handler import BookmarkHandler

        basic_args.list_bookmarks = True

        mock_manager = Mock()
        mock_manager.list_all.return_value = [
            {"id": "BM1", "idea": "Idea 1"},
            {"id": "BM2", "idea": "Idea 2"}
        ]

        with patch('madspark.cli.commands.bookmark_handler.BookmarkManager', return_value=mock_manager):
            result = BookmarkHandler.list_bookmarks(basic_args)

            assert result.success is True
            mock_manager.list_all.assert_called_once()


# Tests for ExportHandler
class TestExportHandler:
    """Tests for ExportHandler command handler."""

    def test_export_json(self, basic_args, mock_logger):
        """Test JSON export."""
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.export = 'json'
        results = [{"idea": "Test", "score": 85}]

        mock_export_manager = Mock()
        mock_export_manager.export_to_json.return_value = "/output/results.json"

        with patch('madspark.cli.commands.export_handler.ExportManager', return_value=mock_export_manager):
            with patch('madspark.cli.commands.export_handler.create_metadata_from_args', return_value={}):
                handler = ExportHandler(basic_args, mock_logger)
                result = handler.execute(results)

                assert result.success is True
                mock_export_manager.export_to_json.assert_called_once()

    def test_export_all_formats(self, basic_args, mock_logger):
        """Test export to all formats."""
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.export = 'all'
        results = [{"idea": "Test", "score": 85}]

        mock_export_manager = Mock()
        exported_files = {
            'json': '/output/results.json',
            'csv': '/output/results.csv',
            'markdown': '/output/results.md',
            'pdf': '/output/results.pdf'
        }
        mock_export_manager.export_all_formats.return_value = exported_files

        with patch('madspark.cli.commands.export_handler.ExportManager', return_value=mock_export_manager):
            with patch('madspark.cli.commands.export_handler.create_metadata_from_args', return_value={}):
                handler = ExportHandler(basic_args, mock_logger)
                result = handler.execute(results)

                assert result.success is True
                mock_export_manager.export_all_formats.assert_called_once()

    def test_no_export_flag(self, basic_args, mock_logger):
        """Test that export is skipped when not requested."""
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.export = None
        results = [{"idea": "Test", "score": 85}]

        handler = ExportHandler(basic_args, mock_logger)
        result = handler.execute(results)

        assert result.success is True
        # No export operations should occur

    def test_export_failure_handling(self, basic_args, mock_logger):
        """Test export error handling."""
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.export = 'pdf'
        results = [{"idea": "Test", "score": 85}]

        mock_export_manager = Mock()
        mock_export_manager.export_to_pdf.side_effect = Exception("PDF generation failed")

        with patch('madspark.cli.commands.export_handler.ExportManager', return_value=mock_export_manager):
            with patch('madspark.cli.commands.export_handler.create_metadata_from_args', return_value={}):
                handler = ExportHandler(basic_args, mock_logger)
                result = handler.execute(results)

                assert result.success is False

    def test_custom_filename(self, basic_args, mock_logger):
        """Test export with custom filename."""
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.export = 'json'
        basic_args.export_filename = 'custom_results'
        results = [{"idea": "Test", "score": 85}]

        mock_export_manager = Mock()
        mock_export_manager.export_to_json.return_value = "/output/custom_results.json"

        with patch('madspark.cli.commands.export_handler.ExportManager', return_value=mock_export_manager):
            with patch('madspark.cli.commands.export_handler.create_metadata_from_args', return_value={}):
                handler = ExportHandler(basic_args, mock_logger)
                result = handler.execute(results)

                assert result.success is True
                # Verify filename was passed
                call_args = mock_export_manager.export_to_json.call_args
                assert call_args[0][2] == 'custom_results'


# Integration tests for command handlers
class TestCommandHandlerIntegration:
    """Integration tests for command handler workflow."""

    def test_full_workflow_execution_chain(self, basic_args, mock_logger):
        """Test complete workflow execution chain: validate -> execute -> bookmark -> export."""
        from madspark.cli.commands.validation import WorkflowValidator
        from madspark.cli.commands.workflow_executor import WorkflowExecutor
        from madspark.cli.commands.bookmark_handler import BookmarkHandler
        from madspark.cli.commands.export_handler import ExportHandler

        basic_args.temperature_preset = None
        basic_args.temp_idea = 0.9
        basic_args.temp_critic = 0.3
        basic_args.temp_refiner = 0.7
        basic_args.export = 'json'

        # Step 1: Validation
        mock_temp_manager = Mock()
        with patch('madspark.cli.commands.validation.create_temperature_manager_from_args', return_value=mock_temp_manager):
            validator = WorkflowValidator(basic_args, mock_logger)
            validation_result = validator.execute()

            assert validation_result.success is True
            temp_manager = validation_result.data['temp_manager']

        # Step 2: Workflow execution
        mock_results = [{"improved_idea": "Test idea", "improved_score": 88}]
        with patch('madspark.cli.commands.workflow_executor.run_multistep_workflow', return_value=mock_results):
            with patch('madspark.cli.commands.workflow_executor.determine_num_candidates', return_value=1):
                executor = WorkflowExecutor(basic_args, mock_logger, temp_manager)
                workflow_result = executor.execute()

                assert workflow_result.success is True
                results = workflow_result.data

        # Step 3: Bookmarking
        mock_bookmark_manager = Mock()
        mock_bookmark_manager.bookmark_idea.return_value = "BM789"
        with patch('madspark.cli.commands.bookmark_handler.BookmarkManager', return_value=mock_bookmark_manager):
            bookmark_handler = BookmarkHandler(basic_args, mock_logger)
            bookmark_result = bookmark_handler.execute(results)

            assert bookmark_result.success is True

        # Step 4: Export
        mock_export_manager = Mock()
        mock_export_manager.export_to_json.return_value = "/output/results.json"
        with patch('madspark.cli.commands.export_handler.ExportManager', return_value=mock_export_manager):
            with patch('madspark.cli.commands.export_handler.create_metadata_from_args', return_value={}):
                export_handler = ExportHandler(basic_args, mock_logger)
                export_result = export_handler.execute(results)

                assert export_result.success is True

    def test_batch_mode_workflow(self, basic_args, mock_logger):
        """Test batch processing workflow."""
        from madspark.cli.commands.batch_handler import BatchHandler

        basic_args.batch = "test.csv"

        mock_processor = Mock()
        mock_batch_items = [{"theme": "Test", "constraints": "Context"}]
        mock_processor.load_batch_from_csv.return_value = mock_batch_items
        mock_processor.process_batch.return_value = {
            'total_processing_time': 10.0,
            'completed': 1,
            'failed': 0
        }
        mock_processor.export_batch_results.return_value = {}
        mock_processor.create_batch_report.return_value = "report.txt"

        with patch('madspark.cli.commands.batch_handler.BatchProcessor', return_value=mock_processor):
            handler = BatchHandler(basic_args, mock_logger)
            result = handler.execute()

            assert result.success is True
            assert result.data['completed'] == 1
