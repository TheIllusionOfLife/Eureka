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
        assert sanitize_filename("Test/File*Name") == "TestFileName"
        assert sanitize_filename("Special:Chars?") == "SpecialChars"
    
    def test_sanitize_filename_length(self):
        """Test filename length limiting."""
        long_name = "This is a very long filename that should be truncated"
        result = sanitize_filename(long_name, max_length=20)
        assert len(result) <= 20
        assert result == "This_is_a_very_long"
    
    def test_sanitize_filename_unicode(self):
        """Test unicode character handling."""
        # Special chars are removed, not replaced with underscores
        assert sanitize_filename("File with spaces") == "File_with_spaces"
        assert sanitize_filename("中文文件名") == "中文文件名"


class TestBatchItem:
    """Test cases for BatchItem class."""
    
    def test_batch_item_creation(self):
        """Test BatchItem instantiation."""
        item = BatchItem(
            theme="AI Automation",
            constraints="Budget-friendly",
            temperature_preset="balanced",
            num_candidates=3,
            tags=["ai", "automation"]
        )
        
        assert item.theme == "AI Automation"
        assert item.constraints == "Budget-friendly"
        assert item.temperature_preset == "balanced"
        assert item.num_candidates == 3
        assert item.tags == ["ai", "automation"]
        assert item.status == "pending"
    
    def test_batch_item_defaults(self):
        """Test BatchItem with default values."""
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints"
        )
        
        assert item.temperature_preset is None
        assert item.tags == []
        assert item.status == "pending"
        assert item.result is None
        assert item.error is None
    
    def test_batch_item_to_dict(self):
        """Test BatchItem serialization."""
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints",
            temperature_preset="creative",
            tags=["test"]
        )
        
        data = item.to_dict()
        assert data["theme"] == "Test Theme"
        assert data["constraints"] == "Test Constraints"
        assert data["temperature_preset"] == "creative"
        assert data["tags"] == ["test"]
        assert data["status"] == "pending"


class TestBatchProcessor:
    """Test cases for BatchProcessor class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    async def batch_processor(self, temp_dir):
        """Create BatchProcessor instance."""
        processor = BatchProcessor(
            max_concurrent=2,
            use_async=True,
            enable_cache=False,
            export_dir=temp_dir,
            verbose=False
        )
        await processor.initialize()
        yield processor
        await processor.close()
    
    def test_batch_processor_initialization(self, temp_dir):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(
            export_dir=temp_dir,
            max_concurrent=3,
            use_async=True
        )
        
        assert processor.export_dir == Path(temp_dir)
        assert processor.max_concurrent == 3
        assert processor.use_async == True
        assert processor.enable_cache == False
    
    @pytest.mark.asyncio
    async def test_load_batch_from_csv(self, batch_processor, tmp_path):
        """Test loading batch from CSV."""
        csv_file = tmp_path / "test_batch.csv"
        csv_content = """theme,constraints,temperature_preset,num_candidates,tags
"AI Healthcare","Budget-friendly","balanced",2,"health,ai"
"Urban Farming","Small spaces","creative",3,"urban,farming"
"""
        with open(csv_file, 'w') as f:
            f.write(csv_content)
        
        items = batch_processor.load_batch_from_csv(str(csv_file))
        
        assert len(items) == 2
        assert items[0].theme == "AI Healthcare"
        assert items[0].constraints == "Budget-friendly"
        assert items[0].temperature_preset == "balanced"
        assert items[0].num_candidates == 2
        assert items[0].tags == ["health", "ai"]
    
    @pytest.mark.asyncio
    async def test_load_batch_from_json(self, batch_processor, tmp_path):
        """Test loading batch from JSON."""
        json_file = tmp_path / "test_batch.json"
        json_data = [
            {
                "theme": "AI Testing",
                "constraints": "Simple",
                "temperature_preset": "balanced",
                "num_candidates": 2,
                "tags": ["test"]
            }
        ]
        
        with open(json_file, 'w') as f:
            json.dump(json_data, f)
        
        items = batch_processor.load_batch_from_json(str(json_file))
        
        assert len(items) == 1
        assert items[0].theme == "AI Testing"
    
    @pytest.mark.asyncio
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    async def test_process_single_item(self, mock_workflow, batch_processor):
        """Test processing a single batch item."""
        mock_workflow.return_value = [
            {"idea": "Test idea", "score": 8.5}
        ]
        
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints"
        )
        
        # Process single item using the actual method - use sync version for simplicity
        batch_processor.process_single_item_sync(
            item, 
            {"enable_novelty_filter": True}
        )
        
        assert item.status == "completed"
        assert item.result is not None
        assert item.error is None
        mock_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('madspark.utils.batch_processor.run_multistep_workflow')
    async def test_process_item_with_error(self, mock_workflow, batch_processor):
        """Test error handling in item processing."""
        mock_workflow.side_effect = Exception("Test error")
        
        item = BatchItem(
            theme="Test Theme",
            constraints="Test Constraints"
        )
        
        batch_processor.process_single_item_sync(
            item,
            {"enable_novelty_filter": True}
        )
        
        assert item.status == "failed"
        assert item.error == "Test error"
        assert item.result is None
    
    @pytest.mark.asyncio
    @patch('madspark.utils.batch_processor.AsyncCoordinator')
    async def test_process_batch_async(self, mock_coordinator_class, batch_processor):
        """Test async batch processing."""
        # Mock the coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.run_workflow.return_value = [{"idea": "Test", "score": 7.0}]
        mock_coordinator_class.return_value = mock_coordinator
        
        items = [
            BatchItem(f"Theme{i}", f"Constraints{i}")
            for i in range(3)
        ]
        
        # Use the async method directly instead of process_batch which uses asyncio.run
        results = await batch_processor.process_batch_async(items, {})
        
        assert "total_items" in results
        assert results["total_items"] == 3
    
    @pytest.mark.asyncio
    async def test_export_results(self, batch_processor, tmp_path):
        """Test exporting batch results."""
        # Create some completed items
        items = []
        for i in range(2):
            item = BatchItem(f"Theme{i}", f"Constraints{i}")
            item.status = "completed"
            item.result = [{"idea": f"Idea{i}", "initial_score": 7.0 + i}]
            items.append(item)
        
        # Export results
        export_files = batch_processor.export_batch_results(
            items,
            batch_id="test_batch"
        )
        
        assert "summary" in export_files
        assert os.path.exists(export_files["summary"])
        
        # Verify summary content
        with open(export_files["summary"], 'r') as f:
            data = json.load(f)
            assert "total_items" in data
            assert data["total_items"] == 2


class TestCreateSampleBatchFile:
    """Test cases for create_sample_batch_file function."""
    
    def test_create_sample_csv(self, tmp_path):
        """Test creating sample CSV batch file."""
        output_file = tmp_path / "sample_batch.csv"
        
        create_sample_batch_file(str(output_file), format="csv")
        
        assert output_file.exists()
        
        # Verify content structure
        with open(output_file, 'r') as f:
            content = f.read()
            assert "theme,constraints,temperature_preset,num_candidates,tags" in content
            assert "AI" in content or "ai" in content.lower()
    
    def test_create_sample_json(self, tmp_path):
        """Test creating sample JSON batch file."""
        output_file = tmp_path / "sample_batch.json"
        
        create_sample_batch_file(str(output_file), format="json")
        
        assert output_file.exists()
        
        # Verify content structure
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0
            assert "theme" in data[0]
            assert "constraints" in data[0]