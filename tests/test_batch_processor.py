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
    BatchItem,
    sanitize_filename,
    create_sample_batch_file
)


class TestSanitizeFilename:
    """Test cases for filename sanitization."""
    
    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization."""
        assert sanitize_filename("Hello World") == "Hello_World"
        assert sanitize_filename("Test/File*Name") == "Test_File_Name"
        assert sanitize_filename("Special:Chars?") == "Special_Chars_"
    
    def test_sanitize_filename_length(self):
        """Test filename length limiting."""
        long_name = "This is a very long filename that should be truncated"
        result = sanitize_filename(long_name, max_length=20)
        assert len(result) <= 20
        assert result == "This_is_a_very_long_"
    
    def test_sanitize_filename_unicode(self):
        """Test unicode character handling."""
        assert sanitize_filename("File with émojis 🤖") == "File_with_émojis__"
        assert sanitize_filename("中文文件名") == "中文文件名"


class TestBatchItem:
    """Test cases for BatchItem class."""
    
    def test_batch_item_creation(self):
        """Test BatchItem instantiation."""
        item = BatchItem(
            theme="AI Automation",
            constraints="Budget-friendly",
            task_id="task_001"
        )
        
        assert item.theme == "AI Automation"
        assert item.constraints == "Budget-friendly"
        assert item.task_id == "task_001"
        assert item.metadata == {}
    
    def test_batch_item_with_metadata(self):
        """Test BatchItem with metadata."""
        metadata = {"priority": "high", "category": "innovation"}
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints",
            task_id="test_id",
            metadata=metadata
        )
        
        assert item.metadata == metadata
        assert item.metadata["priority"] == "high"


class TestBatchProcessor:
    """Test cases for BatchProcessor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def batch_processor(self, temp_dir):
        """Create BatchProcessor instance."""
        return BatchProcessor(output_dir=temp_dir)
    
    def test_batch_processor_initialization(self, temp_dir):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(output_dir=temp_dir)
        
        assert processor.output_dir == Path(temp_dir)
        assert processor.batch_config is not None
        assert processor.stats["total_tasks"] == 0
        assert processor.stats["completed_tasks"] == 0
    
    @patch('madspark.utils.batch_processor.run_workflow')
    def test_process_single_task(self, mock_workflow, batch_processor):
        """Test processing a single task."""
        # Mock workflow result
        mock_workflow.return_value = [
            {"idea": "Test idea", "score": 8.5}
        ]
        
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints",
            task_id="test_001"
        )
        
        result = batch_processor.process_task(item)
        
        assert result is not None
        assert batch_processor.stats["completed_tasks"] == 1
        mock_workflow.assert_called_once()
    
    @patch('madspark.utils.batch_processor.run_workflow')
    def test_process_task_with_error(self, mock_workflow, batch_processor):
        """Test error handling in task processing."""
        mock_workflow.side_effect = Exception("Test error")
        
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints",
            task_id="test_002"
        )
        
        result = batch_processor.process_task(item)
        
        assert result is not None
        assert batch_processor.stats["failed_tasks"] == 1
        assert "test_002" in batch_processor.failed_tasks
    
    @patch('madspark.utils.batch_processor.run_workflow')
    def test_process_batch(self, mock_workflow, batch_processor):
        """Test batch processing multiple tasks."""
        mock_workflow.return_value = [{"idea": "Test", "score": 7.0}]
        
        tasks = [
            BatchItem(f"Theme{i}", f"Constraints{i}", f"task_{i}")
            for i in range(5)
        ]
        
        batch_processor.process_batch(tasks)
        
        assert batch_processor.stats["total_tasks"] == 5
        assert batch_processor.stats["completed_tasks"] == 5
        assert mock_workflow.call_count == 5
    
    def test_save_results(self, batch_processor, temp_dir):
        """Test saving results to file."""
        # Add some mock results
        batch_processor.results = [
            {
                "task_id": "test_001",
                "theme": "Test Theme",
                "results": [{"idea": "Test idea", "score": 8.0}]
            }
        ]
        
        output_file = batch_processor.save_results()
        
        assert output_file.exists()
        assert output_file.suffix == ".json"
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data["results"]) == 1
            assert data["results"][0]["task_id"] == "test_001"
    
    def test_save_summary(self, batch_processor, temp_dir):
        """Test saving summary report."""
        # Set up some stats
        batch_processor.stats = {
            "total_tasks": 10,
            "completed_tasks": 8,
            "failed_tasks": 2,
            "start_time": datetime.now(),
            "end_time": datetime.now()
        }
        
        summary_file = batch_processor.save_summary()
        
        assert summary_file.exists()
        assert summary_file.suffix == ".json"
        
        # Verify content
        with open(summary_file, 'r') as f:
            summary = json.load(f)
            assert summary["stats"]["total_tasks"] == 10
            assert summary["stats"]["completed_tasks"] == 8
    
    @patch('madspark.utils.batch_processor.run_workflow')
    def test_process_batch_parallel(self, mock_workflow, batch_processor):
        """Test parallel batch processing."""
        mock_workflow.return_value = [{"idea": "Test", "score": 7.0}]
        
        # Enable parallel processing
        batch_processor.batch_config["parallel_processing"] = True
        batch_processor.batch_config["num_workers"] = 2
        
        tasks = [
            BatchItem(f"Theme{i}", f"Constraints{i}", f"task_{i}")
            for i in range(4)
        ]
        
        batch_processor.process_batch(tasks)
        
        assert batch_processor.stats["completed_tasks"] == 4
        assert mock_workflow.call_count == 4
    
    def test_load_batch_config(self, temp_dir):
        """Test loading batch configuration from file."""
        config_file = Path(temp_dir) / "batch_config.json"
        config_data = {
            "batch_size": 50,
            "parallel_processing": True,
            "num_workers": 4,
            "save_intermediate": True
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        processor = BatchProcessor(
            output_dir=temp_dir,
            config_file=str(config_file)
        )
        
        assert processor.batch_config["batch_size"] == 50
        assert processor.batch_config["num_workers"] == 4


class TestCreateSampleBatchFile:
    """Test cases for create_sample_batch_file function."""
    
    def test_create_sample_csv(self, tmp_path):
        """Test creating sample CSV batch file."""
        output_file = tmp_path / "sample_batch.csv"
        
        create_sample_batch_file(str(output_file), format="csv")
        
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            content = f.read()
            assert "theme,constraints,task_id" in content
            assert "AI" in content
    
    def test_create_sample_json(self, tmp_path):
        """Test creating sample JSON batch file."""
        output_file = tmp_path / "sample_batch.json"
        
        create_sample_batch_file(str(output_file), format="json")
        
        assert output_file.exists()
        
        # Verify content
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert "tasks" in data
            assert len(data["tasks"]) > 0
            assert "theme" in data["tasks"][0]


class TestBatchProcessorIntegration:
    """Integration tests for BatchProcessor."""
    
    @pytest.fixture
    def integration_processor(self, tmp_path):
        """Create processor for integration tests."""
        return BatchProcessor(output_dir=str(tmp_path))
    
    @patch('madspark.utils.batch_processor.run_workflow')
    def test_end_to_end_batch_processing(self, mock_workflow, integration_processor, tmp_path):
        """Test complete batch processing workflow."""
        # Mock varied results
        mock_workflow.side_effect = [
            [{"idea": f"Idea {i}", "score": 7.0 + i * 0.5}]
            for i in range(3)
        ]
        
        # Create batch file
        batch_file = tmp_path / "test_batch.json"
        batch_data = {
            "tasks": [
                {
                    "theme": f"Theme {i}",
                    "constraints": f"Constraints {i}",
                    "task_id": f"task_{i:03d}"
                }
                for i in range(3)
            ]
        }
        
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f)
        
        # Process batch
        with open(batch_file, 'r') as f:
            data = json.load(f)
            tasks = [
                BatchItem(**task) for task in data["tasks"]
            ]
        
        integration_processor.process_batch(tasks)
        
        # Save results
        output_file = integration_processor.save_results()
        summary_file = integration_processor.save_summary()
        
        # Verify outputs
        assert output_file.exists()
        assert summary_file.exists()
        
        with open(output_file, 'r') as f:
            results = json.load(f)
            assert len(results["results"]) == 3
            assert results["stats"]["completed_tasks"] == 3
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
            assert summary["stats"]["total_tasks"] == 3
            assert summary["stats"]["success_rate"] == 100.0