"""Comprehensive tests for batch processing functionality."""
import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from datetime import datetime

from madspark.utils.batch_processor import (
    BatchProcessor, 
    BatchConfig, 
    BatchTask, 
    BatchResult,
    sanitize_filename,
    load_tasks_from_file,
    load_tasks_from_csv
)
from madspark.core.coordinator import CandidateData
from madspark.utils.temperature_control import TemperatureManager


class TestBatchUtilityFunctions:
    """Test utility functions for batch processing."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("My Test File") == "My_Test_File"
        assert sanitize_filename("file-name.txt") == "file-name.txt"
        assert sanitize_filename("normal_filename") == "normal_filename"
    
    def test_sanitize_filename_special_chars(self):
        """Test sanitization of special characters."""
        assert sanitize_filename("file<>name") == "filename"
        assert sanitize_filename("file:name|test") == "filenametest"
        assert sanitize_filename("path/to/file") == "pathtofile"
        assert sanitize_filename("file\\name") == "filename"
        assert sanitize_filename("file?name*") == "filename"
    
    def test_sanitize_filename_multiple_spaces(self):
        """Test handling of multiple spaces/underscores."""
        assert sanitize_filename("file   name") == "file_name"
        assert sanitize_filename("file___name") == "file_name"
        assert sanitize_filename("__leading") == "_leading"
        assert sanitize_filename("trailing__") == "trailing_"
    
    def test_sanitize_filename_max_length(self):
        """Test filename truncation."""
        long_name = "a" * 100
        result = sanitize_filename(long_name, max_length=30)
        assert len(result) == 30
        assert result == "a" * 30
    
    def test_sanitize_filename_unicode(self):
        """Test handling of unicode characters."""
        # Should preserve safe unicode
        assert sanitize_filename("café_résumé") == "café_résumé"
        # Should remove control characters
        assert sanitize_filename("file\x00name") == "filename"
    
    def test_load_tasks_from_file_json(self):
        """Test loading tasks from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            tasks = [
                {"theme": "AI automation", "constraints": "Cost-effective"},
                {"theme": "ML optimization", "constraints": "Scalable"}
            ]
            json.dump(tasks, f)
            f.flush()
            
            loaded_tasks = load_tasks_from_file(f.name)
            
        os.unlink(f.name)
        
        assert len(loaded_tasks) == 2
        assert loaded_tasks[0].theme == "AI automation"
        assert loaded_tasks[0].constraints == "Cost-effective"
        assert loaded_tasks[1].theme == "ML optimization"
    
    def test_load_tasks_from_file_invalid_json(self):
        """Test loading from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            f.flush()
            
            with pytest.raises(json.JSONDecodeError):
                load_tasks_from_file(f.name)
            
        os.unlink(f.name)
    
    def test_load_tasks_from_csv(self):
        """Test loading tasks from CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("theme,constraints\n")
            f.write("AI automation,Cost-effective\n")
            f.write("ML optimization,\"Scalable, robust\"\n")
            f.flush()
            
            loaded_tasks = load_tasks_from_csv(f.name)
            
        os.unlink(f.name)
        
        assert len(loaded_tasks) == 2
        assert loaded_tasks[0].theme == "AI automation"
        assert loaded_tasks[1].constraints == "Scalable, robust"
    
    def test_load_tasks_from_csv_missing_columns(self):
        """Test loading from CSV with missing columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("theme\n")  # Missing constraints column
            f.write("AI automation\n")
            f.flush()
            
            with pytest.raises(KeyError):
                load_tasks_from_csv(f.name)
            
        os.unlink(f.name)


class TestBatchConfig:
    """Test BatchConfig class."""
    
    def test_batch_config_defaults(self):
        """Test default BatchConfig values."""
        config = BatchConfig()
        assert config.parallel_workers == 3
        assert config.timeout_per_task == 300
        assert config.save_intermediate == True
        assert config.export_formats == ["json", "csv", "markdown"]
        assert config.output_dir == "batch_results"
    
    def test_batch_config_custom_values(self):
        """Test BatchConfig with custom values."""
        config = BatchConfig(
            parallel_workers=5,
            timeout_per_task=600,
            save_intermediate=False,
            export_formats=["json"],
            output_dir="custom_output"
        )
        assert config.parallel_workers == 5
        assert config.timeout_per_task == 600
        assert config.save_intermediate == False
        assert config.export_formats == ["json"]
        assert config.output_dir == "custom_output"


class TestBatchTask:
    """Test BatchTask class."""
    
    def test_batch_task_creation(self):
        """Test BatchTask creation."""
        task = BatchTask(
            theme="AI testing",
            constraints="Budget-friendly",
            task_id="task_001"
        )
        assert task.theme == "AI testing"
        assert task.constraints == "Budget-friendly"
        assert task.task_id == "task_001"
    
    def test_batch_task_auto_id(self):
        """Test BatchTask with auto-generated ID."""
        task = BatchTask(theme="Test", constraints="None")
        assert task.task_id is not None
        assert task.task_id.startswith("task_")


class TestBatchResult:
    """Test BatchResult class."""
    
    def test_batch_result_success(self):
        """Test successful BatchResult."""
        candidates = [
            CandidateData(
                idea="Test idea",
                initial_score=5.0,
                initial_critique="OK",
                advocacy="Good",
                skepticism="Bad",
                improved_idea="Better idea",
                improved_score=6.0,
                improved_critique="Better",
                confidence=0.8,
                dimension_scores={}
            )
        ]
        
        result = BatchResult(
            task_id="task_001",
            theme="Test theme",
            constraints="Test constraints",
            candidates=candidates,
            success=True,
            error=None,
            duration=10.5
        )
        
        assert result.success == True
        assert result.error is None
        assert len(result.candidates) == 1
        assert result.duration == 10.5
    
    def test_batch_result_failure(self):
        """Test failed BatchResult."""
        result = BatchResult(
            task_id="task_002",
            theme="Failed theme",
            constraints="None",
            candidates=[],
            success=False,
            error="API timeout",
            duration=300.0
        )
        
        assert result.success == False
        assert result.error == "API timeout"
        assert len(result.candidates) == 0


class TestBatchProcessor:
    """Test BatchProcessor class."""
    
    @pytest.fixture
    def batch_processor(self):
        """Create BatchProcessor instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(output_dir=tmpdir)
            yield BatchProcessor(config)
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample batch tasks."""
        return [
            BatchTask("AI automation", "Cost-effective", "task_001"),
            BatchTask("ML optimization", "Scalable", "task_002"),
            BatchTask("Data analytics", "Real-time", "task_003")
        ]
    
    def test_batch_processor_initialization(self, batch_processor):
        """Test BatchProcessor initialization."""
        assert batch_processor.config is not None
        assert batch_processor.results == []
        assert batch_processor._start_time is None
        assert Path(batch_processor.config.output_dir).exists()
    
    def test_batch_processor_output_dir_creation(self):
        """Test that BatchProcessor creates output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "new_batch_output")
            config = BatchConfig(output_dir=output_dir)
            processor = BatchProcessor(config)
            assert Path(output_dir).exists()
    
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    def test_process_single_task_success(self, mock_workflow, batch_processor):
        """Test processing a single task successfully."""
        task = BatchTask("Test theme", "Test constraints", "test_001")
        
        mock_candidates = [
            CandidateData(
                idea="Test idea",
                initial_score=7.0,
                initial_critique="Good",
                advocacy="Strong",
                skepticism="Weak",
                improved_idea="Better idea",
                improved_score=8.0,
                improved_critique="Excellent",
                confidence=0.9,
                dimension_scores={}
            )
        ]
        mock_workflow.return_value = mock_candidates
        
        result = batch_processor._process_single_task(task)
        
        assert result.success == True
        assert result.task_id == "test_001"
        assert len(result.candidates) == 1
        assert result.error is None
        mock_workflow.assert_called_once()
    
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    def test_process_single_task_failure(self, mock_workflow, batch_processor):
        """Test handling task processing failure."""
        task = BatchTask("Test theme", "Test constraints", "test_002")
        
        mock_workflow.side_effect = Exception("API error")
        
        result = batch_processor._process_single_task(task)
        
        assert result.success == False
        assert result.task_id == "test_002"
        assert len(result.candidates) == 0
        assert "API error" in result.error
    
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    def test_process_single_task_with_temperature(self, mock_workflow, batch_processor):
        """Test task processing with temperature manager."""
        task = BatchTask("Test theme", "Test constraints", "test_003")
        temp_manager = TemperatureManager.from_preset("creative")
        
        batch_processor._temperature_manager = temp_manager
        mock_workflow.return_value = []
        
        result = batch_processor._process_single_task(task)
        
        # Verify temperature manager was passed
        mock_workflow.assert_called_once()
        call_kwargs = mock_workflow.call_args[1]
        assert call_kwargs['temperature_manager'] == temp_manager
    
    @patch('madspark.utils.batch_processor.ExportManager')
    def test_save_intermediate_results(self, mock_export_manager, batch_processor):
        """Test saving intermediate results."""
        batch_processor.config.save_intermediate = True
        
        result = BatchResult(
            task_id="test_001",
            theme="Test",
            constraints="None",
            candidates=[],
            success=True,
            error=None,
            duration=5.0
        )
        
        mock_export_instance = Mock()
        mock_export_manager.return_value = mock_export_instance
        
        batch_processor._save_intermediate_result(result)
        
        # Verify export was called
        mock_export_instance.export_to_json.assert_called_once()
    
    def test_save_intermediate_results_disabled(self, batch_processor):
        """Test that intermediate saving can be disabled."""
        batch_processor.config.save_intermediate = False
        
        result = BatchResult(
            task_id="test_001",
            theme="Test",
            constraints="None",
            candidates=[],
            success=True,
            error=None,
            duration=5.0
        )
        
        # Should not raise error even though no saving occurs
        batch_processor._save_intermediate_result(result)
    
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    def test_process_batch_sequential(self, mock_workflow, batch_processor, sample_tasks):
        """Test sequential batch processing."""
        mock_workflow.return_value = []
        
        # Use sequential processing (1 worker)
        batch_processor.config.parallel_workers = 1
        
        batch_processor.process_batch(sample_tasks)
        
        assert len(batch_processor.results) == 3
        assert mock_workflow.call_count == 3
    
    def test_export_all_results(self, batch_processor):
        """Test exporting all batch results."""
        # Add some results
        batch_processor.results = [
            BatchResult(
                task_id="test_001",
                theme="Theme 1",
                constraints="Constraint 1",
                candidates=[],
                success=True,
                error=None,
                duration=5.0
            ),
            BatchResult(
                task_id="test_002",
                theme="Theme 2", 
                constraints="Constraint 2",
                candidates=[],
                success=False,
                error="Failed",
                duration=10.0
            )
        ]
        
        exported_files = batch_processor.export_all_results()
        
        # Check that files were created
        assert "summary" in exported_files
        assert exported_files["summary"].exists()
        
        # Verify summary content
        with open(exported_files["summary"], 'r') as f:
            summary = json.load(f)
        
        assert summary["total_tasks"] == 2
        assert summary["successful_tasks"] == 1
        assert summary["failed_tasks"] == 1
    
    @patch('madspark.utils.batch_processor.ExportManager')
    def test_export_individual_results(self, mock_export_manager, batch_processor):
        """Test exporting individual task results."""
        batch_processor.config.export_formats = ["json", "csv"]
        
        # Mock export manager
        mock_export_instance = Mock()
        mock_export_manager.return_value = mock_export_instance
        mock_export_instance.export_to_json.return_value = Path("test.json")
        mock_export_instance.export_to_csv.return_value = Path("test.csv")
        
        # Add results with candidates
        candidates = [
            CandidateData(
                idea="Idea 1",
                initial_score=5.0,
                initial_critique="OK",
                advocacy="Good",
                skepticism="Bad",
                improved_idea="Better",
                improved_score=6.0,
                improved_critique="Better",
                confidence=0.8,
                dimension_scores={}
            )
        ]
        
        batch_processor.results = [
            BatchResult(
                task_id="test_001",
                theme="Theme 1",
                constraints="Constraint 1", 
                candidates=candidates,
                success=True,
                error=None,
                duration=5.0
            )
        ]
        
        exported_files = batch_processor.export_all_results()
        
        # Verify individual exports were called
        assert mock_export_instance.export_to_json.called
        assert mock_export_instance.export_to_csv.called
    
    def test_get_summary_statistics(self, batch_processor):
        """Test summary statistics generation."""
        batch_processor.results = [
            BatchResult("t1", "Theme 1", "C1", [], True, None, 5.0),
            BatchResult("t2", "Theme 2", "C2", [], True, None, 10.0),
            BatchResult("t3", "Theme 3", "C3", [], False, "Error", 15.0)
        ]
        
        stats = batch_processor.get_summary_statistics()
        
        assert stats["total_tasks"] == 3
        assert stats["successful_tasks"] == 2
        assert stats["failed_tasks"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["average_duration"] == 10.0
        assert stats["total_duration"] == 30.0


class TestBatchProcessorAsync:
    """Test async functionality of BatchProcessor."""
    
    @pytest.mark.asyncio
    async def test_process_batch_async(self):
        """Test async batch processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(
                output_dir=tmpdir,
                parallel_workers=2
            )
            processor = BatchProcessor(config)
            
            tasks = [
                BatchTask("Task 1", "C1", "t1"),
                BatchTask("Task 2", "C2", "t2"),
                BatchTask("Task 3", "C3", "t3")
            ]
            
            with patch('madspark.utils.batch_processor.AsyncCoordinator') as mock_async:
                mock_coordinator = AsyncMock()
                mock_async.return_value = mock_coordinator
                mock_coordinator.run_workflow.return_value = []
                
                # Enable async mode
                processor._enable_async = True
                await processor.process_batch_async(tasks)
                
                assert len(processor.results) == 3
                assert mock_coordinator.run_workflow.call_count == 3
    
    @pytest.mark.asyncio  
    async def test_process_task_async_timeout(self):
        """Test async task timeout handling."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(
                output_dir=tmpdir,
                timeout_per_task=0.1  # Very short timeout
            )
            processor = BatchProcessor(config)
            
            task = BatchTask("Slow task", "Timeout test", "timeout_test")
            
            with patch('madspark.utils.batch_processor.AsyncCoordinator') as mock_async:
                mock_coordinator = AsyncMock()
                mock_async.return_value = mock_coordinator
                
                # Simulate slow task
                async def slow_workflow(*args, **kwargs):
                    await asyncio.sleep(1.0)  # Longer than timeout
                    return []
                
                mock_coordinator.run_workflow.side_effect = slow_workflow
                
                result = await processor._process_task_async(task)
                
                assert result.success == False
                assert "timeout" in result.error.lower()


class TestBatchProcessorEdgeCases:
    """Test edge cases for BatchProcessor."""
    
    def test_empty_batch(self):
        """Test processing empty batch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(output_dir=tmpdir)
            processor = BatchProcessor(config)
            
            processor.process_batch([])
            
            assert len(processor.results) == 0
            
            # Should still be able to export
            exported = processor.export_all_results()
            assert "summary" in exported
    
    def test_very_large_batch(self):
        """Test processing very large batch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(
                output_dir=tmpdir,
                parallel_workers=5
            )
            processor = BatchProcessor(config)
            
            # Create 100 tasks
            tasks = [
                BatchTask(f"Theme {i}", f"Constraint {i}", f"task_{i:03d}")
                for i in range(100)
            ]
            
            with patch('madspark.utils.batch_processor.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                
                processor.process_batch(tasks)
                
                assert len(processor.results) == 100
                assert mock_workflow.call_count == 100
    
    def test_batch_with_duplicate_ids(self):
        """Test handling duplicate task IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BatchConfig(output_dir=tmpdir)
            processor = BatchProcessor(config)
            
            tasks = [
                BatchTask("Theme 1", "C1", "duplicate_id"),
                BatchTask("Theme 2", "C2", "duplicate_id"),  # Duplicate ID
                BatchTask("Theme 3", "C3", "unique_id")
            ]
            
            with patch('madspark.utils.batch_processor.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                
                processor.process_batch(tasks)
                
                # Should process all tasks despite duplicate IDs
                assert len(processor.results) == 3
                
                # Check that all tasks were processed
                task_ids = [r.task_id for r in processor.results]
                assert task_ids.count("duplicate_id") == 2
                assert "unique_id" in task_ids