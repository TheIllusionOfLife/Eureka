"""Tests for batch processing functionality."""

import pytest
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from batch_processor import BatchItem, BatchProcessor, create_sample_batch_file


class TestBatchItem:
    """Test suite for BatchItem class."""
    
    def test_batch_item_init(self):
        """Test BatchItem initialization."""
        item = BatchItem(
            theme="AI in healthcare",
            constraints="Budget-friendly",
            temperature_preset="creative",
            num_candidates=3,
            tags=["health", "ai"]
        )
        
        assert item.theme == "AI in healthcare"
        assert item.constraints == "Budget-friendly"
        assert item.temperature_preset == "creative"
        assert item.num_candidates == 3
        assert item.tags == ["health", "ai"]
        assert item.status == "pending"
        assert item.result is None
        assert item.error is None
        
    def test_batch_item_to_dict(self):
        """Test BatchItem to_dict conversion."""
        item = BatchItem(
            theme="Test theme",
            constraints="Test constraints"
        )
        
        item_dict = item.to_dict()
        
        assert item_dict["theme"] == "Test theme"
        assert item_dict["constraints"] == "Test constraints"
        assert item_dict["status"] == "pending"
        assert "error" in item_dict
        assert "processing_time" in item_dict


class TestBatchProcessor:
    """Test suite for BatchProcessor class."""
    
    def test_batch_processor_init(self):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(
            max_concurrent=5,
            use_async=True,
            enable_cache=True,
            export_dir="test_exports"
        )
        
        assert processor.max_concurrent == 5
        assert processor.use_async is True
        assert processor.enable_cache is True
        assert processor.export_dir.name == "test_exports"
        
    def test_load_batch_from_csv(self, tmp_path):
        """Test loading batch items from CSV."""
        # Create test CSV
        csv_path = tmp_path / "test_batch.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["theme", "constraints", "temperature_preset", "num_candidates", "tags"])
            writer.writerow(["AI healthcare", "Budget-friendly", "creative", "2", "health,ai"])
            writer.writerow(["Urban farming", "Small spaces", "balanced", "3", "urban,farming"])
            
        processor = BatchProcessor()
        items = processor.load_batch_from_csv(str(csv_path))
        
        assert len(items) == 2
        assert items[0].theme == "AI healthcare"
        assert items[0].tags == ["health", "ai"]
        assert items[1].num_candidates == 3
        
    def test_load_batch_from_json(self, tmp_path):
        """Test loading batch items from JSON."""
        # Create test JSON
        json_path = tmp_path / "test_batch.json"
        data = [
            {
                "theme": "AI healthcare",
                "constraints": "Budget-friendly",
                "temperature_preset": "creative",
                "num_candidates": 2,
                "tags": ["health", "ai"]
            },
            {
                "theme": "Urban farming",
                "constraints": "Small spaces"
            }
        ]
        
        with open(json_path, 'w') as f:
            json.dump(data, f)
            
        processor = BatchProcessor()
        items = processor.load_batch_from_json(str(json_path))
        
        assert len(items) == 2
        assert items[0].theme == "AI healthcare"
        assert items[0].temperature_preset == "creative"
        assert items[1].tags == []
        
    @patch('batch_processor.run_multistep_workflow')
    def test_process_single_item_sync(self, mock_workflow):
        """Test synchronous processing of a single item."""
        # Mock workflow result
        mock_workflow.return_value = [
            {"idea": "Test idea 1", "initial_score": 8},
            {"idea": "Test idea 2", "initial_score": 7}
        ]
        
        processor = BatchProcessor(use_async=False)
        item = BatchItem("Test theme", "Test constraints")
        
        processor.process_single_item_sync(item, {})
        
        assert item.status == "completed"
        assert len(item.result) == 2
        assert item.error is None
        assert item.processing_time > 0
        
        # Verify workflow was called correctly
        mock_workflow.assert_called_once()
        call_args = mock_workflow.call_args[1]
        assert call_args['theme'] == "Test theme"
        assert call_args['constraints'] == "Test constraints"
        
    @patch('batch_processor.run_multistep_workflow')
    def test_process_single_item_sync_failure(self, mock_workflow):
        """Test handling of processing failure."""
        # Mock workflow failure
        mock_workflow.side_effect = Exception("Test error")
        
        processor = BatchProcessor(use_async=False)
        item = BatchItem("Test theme", "Test constraints")
        
        processor.process_single_item_sync(item, {})
        
        assert item.status == "failed"
        assert item.error == "Test error"
        assert item.result is None
        
    @pytest.mark.asyncio
    async def test_process_single_item_async(self):
        """Test asynchronous processing of a single item."""
        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.run_workflow.return_value = [
            {"idea": "Test idea 1", "initial_score": 8}
        ]
        
        processor = BatchProcessor(use_async=True)
        item = BatchItem("Test theme", "Test constraints")
        
        await processor.process_single_item_async(item, mock_coordinator, {})
        
        assert item.status == "completed"
        assert len(item.result) == 1
        assert item.error is None
        
    def test_create_summary(self):
        """Test summary creation."""
        processor = BatchProcessor()
        
        items = [
            BatchItem("Theme 1", "Constraints 1"),
            BatchItem("Theme 2", "Constraints 2"),
            BatchItem("Theme 3", "Constraints 3")
        ]
        
        # Set different statuses
        items[0].status = "completed"
        items[0].result = [{"idea": "Test"}]
        items[1].status = "failed"
        items[1].error = "Test error"
        items[2].status = "pending"
        
        summary = processor._create_summary(items)
        
        assert summary["total_items"] == 3
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["pending"] == 1
        assert len(summary["items"]) == 3
        
    @patch('batch_processor.run_multistep_workflow')
    def test_process_batch_sync(self, mock_workflow):
        """Test synchronous batch processing."""
        # Mock workflow
        mock_workflow.return_value = [{"idea": "Test idea"}]
        
        processor = BatchProcessor(use_async=False)
        items = [
            BatchItem("Theme 1", "Constraints 1"),
            BatchItem("Theme 2", "Constraints 2")
        ]
        
        summary = processor.process_batch(items)
        
        assert summary["total_items"] == 2
        assert summary["completed"] == 2
        assert summary["failed"] == 0
        assert "total_processing_time" in summary
        
        # Verify workflow was called for each item
        assert mock_workflow.call_count == 2
        
    def test_export_batch_results(self, tmp_path):
        """Test exporting batch results."""
        processor = BatchProcessor(export_dir=str(tmp_path))
        
        # Create completed items with results
        items = [
            BatchItem("AI Healthcare", "Budget-friendly"),
            BatchItem("Urban Farming", "Small spaces")
        ]
        
        items[0].status = "completed"
        items[0].result = [
            {
                "idea": "AI diagnosis tool", 
                "initial_score": 8,
                "initial_critique": "Good potential",
                "advocacy": "Strong benefits",
                "skepticism": "Some challenges"
            }
        ]
        
        items[1].status = "completed"
        items[1].result = [
            {
                "idea": "Vertical garden system", 
                "initial_score": 7,
                "initial_critique": "Innovative approach",
                "advocacy": "Space efficient",
                "skepticism": "Setup costs"
            }
        ]
        
        exported = processor.export_batch_results(items, "test_batch")
        
        # Check summary was exported
        assert "summary" in exported
        assert Path(exported["summary"]).exists()
        
        # Check individual items were exported
        assert "item_1" in exported
        assert "item_2" in exported
        
    def test_create_batch_report(self, tmp_path):
        """Test creating batch report."""
        processor = BatchProcessor(export_dir=str(tmp_path))
        
        items = [
            BatchItem("AI Healthcare", "Budget-friendly", temperature_preset="creative"),
            BatchItem("Urban Farming", "Small spaces", tags=["urban", "farming"])
        ]
        
        items[0].status = "completed"
        items[0].result = [{"idea": "AI tool", "initial_score": 8}]
        items[0].processing_time = 5.5
        
        items[1].status = "failed"
        items[1].error = "API error"
        items[1].processing_time = 1.2
        
        report_path = processor.create_batch_report(items, "test_report")
        
        assert Path(report_path).exists()
        
        # Check report content
        with open(report_path, 'r') as f:
            content = f.read()
            assert "MadSpark Batch Processing Report" in content
            assert "AI Healthcare" in content
            assert "creative" in content
            assert "API error" in content
            
    def test_create_sample_batch_file_csv(self, tmp_path):
        """Test creating sample CSV batch file."""
        csv_path = tmp_path / "sample.csv"
        create_sample_batch_file(str(csv_path), "csv")
        
        assert csv_path.exists()
        
        # Verify content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0]["theme"] == "AI in healthcare"
            
    def test_create_sample_batch_file_json(self, tmp_path):
        """Test creating sample JSON batch file."""
        json_path = tmp_path / "sample.json"
        create_sample_batch_file(str(json_path), "json")
        
        assert json_path.exists()
        
        # Verify content
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 3
            assert data[0]["theme"] == "AI in healthcare"
            assert isinstance(data[0]["tags"], list)