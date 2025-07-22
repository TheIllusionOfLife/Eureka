"""Comprehensive tests for export utilities."""
import pytest
import json
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

from madspark.utils.export_utils import ExportManager, PDF_AVAILABLE
from madspark.core.coordinator import CandidateData


class TestExportManager:
    """Test cases for ExportManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def export_manager(self, temp_dir):
        """Create an ExportManager instance with temp directory."""
        return ExportManager(output_dir=temp_dir)
    
    @pytest.fixture
    def sample_results(self):
        """Create sample results for testing."""
        return [
            CandidateData(
                idea="AI-powered task automation",
                initial_score=7.5,
                initial_critique="Good market potential",
                advocacy="Strong demand, proven ROI",
                skepticism="High development costs",
                improved_idea="Enhanced AI task automation with cloud integration",
                improved_score=8.5,
                improved_critique="Excellent scalability",
                confidence=0.85,
                dimension_scores={
                    "feasibility": 8,
                    "innovation": 9,
                    "impact": 8,
                    "scalability": 9
                }
            ),
            CandidateData(
                idea="Smart workflow optimizer",
                initial_score=6.5,
                initial_critique="Needs refinement",
                advocacy="Addresses pain points",
                skepticism="Competition exists",
                improved_idea="ML-driven workflow optimization platform",
                improved_score=7.5,
                improved_critique="Better differentiation",
                confidence=0.75,
                dimension_scores={
                    "feasibility": 7,
                    "innovation": 8,
                    "impact": 7,
                    "scalability": 8
                }
            )
        ]
    
    def test_export_manager_initialization(self, temp_dir):
        """Test ExportManager initialization."""
        manager = ExportManager(output_dir=temp_dir)
        assert manager.output_dir == Path(temp_dir)
        assert manager.output_dir.exists()
    
    def test_export_manager_creates_directory(self):
        """Test that ExportManager creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_exports")
            manager = ExportManager(output_dir=new_dir)
            assert os.path.exists(new_dir)
    
    def test_export_manager_permission_error(self):
        """Test ExportManager handles permission errors."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            with pytest.raises(PermissionError) as exc_info:
                ExportManager(output_dir="/restricted/path")
            assert "Permission denied" in str(exc_info.value)
    
    def test_export_manager_os_error(self):
        """Test ExportManager handles OS errors."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = OSError("Disk full")
            with pytest.raises(OSError) as exc_info:
                ExportManager(output_dir="/invalid/path")
            assert "Failed to create export directory" in str(exc_info.value)
    
    def test_get_output_filepath_with_filename(self, export_manager):
        """Test filepath generation with provided filename."""
        filepath = export_manager._get_output_filepath("results.json", "json")
        assert filepath.name == "results.json"
        assert filepath.parent == export_manager.output_dir
    
    def test_get_output_filepath_without_filename(self, export_manager):
        """Test filepath generation with auto-generated filename."""
        with patch('madspark.utils.export_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            filepath = export_manager._get_output_filepath(None, "json")
            assert filepath.name == "madspark_results_20240101_120000.json"
    
    def test_export_to_json_success(self, export_manager, sample_results):
        """Test successful JSON export."""
        theme = "AI automation"
        constraints = "Cost-effective"
        filename = "test_results.json"
        
        filepath = export_manager.export_to_json(
            results=sample_results,
            theme=theme,
            constraints=constraints,
            filename=filename
        )
        
        assert filepath.exists()
        assert filepath.name == filename
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["theme"] == theme
        assert data["constraints"] == constraints
        assert len(data["candidates"]) == 2
        assert data["candidates"][0]["idea"] == "AI-powered task automation"
        assert data["candidates"][0]["improved_score"] == 8.5
        assert "timestamp" in data
        assert "total_candidates" in data
    
    def test_export_to_json_with_metadata(self, export_manager, sample_results):
        """Test JSON export with additional metadata."""
        metadata = {"version": "2.0", "user": "test_user"}
        
        filepath = export_manager.export_to_json(
            results=sample_results,
            theme="Testing",
            constraints="None",
            metadata=metadata
        )
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["version"] == "2.0"
        assert data["user"] == "test_user"
    
    def test_export_to_csv_success(self, export_manager, sample_results):
        """Test successful CSV export."""
        filename = "test_results.csv"
        
        filepath = export_manager.export_to_csv(
            results=sample_results,
            theme="AI automation",
            constraints="Scalable",
            filename=filename
        )
        
        assert filepath.exists()
        assert filepath.name == filename
        
        # Verify content
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["idea"] == "AI-powered task automation"
        assert rows[0]["improved_score"] == "8.5"
        assert "theme" in rows[0]
        assert "constraints" in rows[0]
    
    def test_export_to_markdown_success(self, export_manager, sample_results):
        """Test successful Markdown export."""
        filename = "test_results.md"
        
        filepath = export_manager.export_to_markdown(
            results=sample_results,
            theme="AI automation",
            constraints="Budget-friendly",
            filename=filename
        )
        
        assert filepath.exists()
        assert filepath.name == filename
        
        # Verify content
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert "# MadSpark Results" in content
        assert "AI automation" in content
        assert "Budget-friendly" in content
        assert "AI-powered task automation" in content
        assert "Score: 7.5 → 8.5" in content
        assert "### Advocacy" in content
        assert "### Skepticism" in content
    
    @pytest.mark.skipif(not PDF_AVAILABLE, reason="ReportLab not available")
    def test_export_to_pdf_success(self, export_manager, sample_results):
        """Test successful PDF export when ReportLab is available."""
        filename = "test_results.pdf"
        
        filepath = export_manager.export_to_pdf(
            results=sample_results,
            theme="AI automation",
            constraints="Enterprise-ready",
            filename=filename
        )
        
        assert filepath.exists()
        assert filepath.name == filename
        assert filepath.stat().st_size > 0  # PDF should have content
    
    def test_export_to_pdf_not_available(self, export_manager, sample_results):
        """Test PDF export when ReportLab is not available."""
        with patch('madspark.utils.export_utils.PDF_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                export_manager.export_to_pdf(
                    results=sample_results,
                    theme="Testing",
                    constraints="None"
                )
            assert "ReportLab" in str(exc_info.value)
    
    def test_export_all_formats(self, export_manager, sample_results):
        """Test exporting to all available formats."""
        base_filename = "all_formats_test"
        
        results = export_manager.export_all_formats(
            results=sample_results,
            theme="Comprehensive test",
            constraints="All formats",
            base_filename=base_filename
        )
        
        assert "json" in results
        assert "csv" in results
        assert "markdown" in results
        
        # Verify all files exist
        assert results["json"].exists()
        assert results["csv"].exists()
        assert results["markdown"].exists()
        
        # PDF might or might not be included depending on ReportLab
        if PDF_AVAILABLE:
            assert "pdf" in results
            assert results["pdf"].exists()
    
    def test_export_empty_results(self, export_manager):
        """Test exporting empty results."""
        filepath = export_manager.export_to_json(
            results=[],
            theme="Empty test",
            constraints="None"
        )
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["total_candidates"] == 0
        assert len(data["candidates"]) == 0
    
    def test_export_with_none_values(self, export_manager):
        """Test exporting results with None values."""
        results = [
            CandidateData(
                idea="Test idea",
                initial_score=5.0,
                initial_critique=None,
                advocacy=None,
                skepticism=None,
                improved_idea="Improved test idea",
                improved_score=6.0,
                improved_critique=None,
                confidence=None,
                dimension_scores=None
            )
        ]
        
        # Should handle None values gracefully
        filepath = export_manager.export_to_json(
            results=results,
            theme="None test",
            constraints=None
        )
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["candidates"][0]["initial_critique"] is None
        assert data["constraints"] is None
    
    def test_export_file_write_error(self, export_manager, sample_results):
        """Test handling file write errors."""
        with patch('builtins.open', side_effect=IOError("Disk full")):
            with pytest.raises(IOError):
                export_manager.export_to_json(
                    results=sample_results,
                    theme="Test",
                    constraints="Test"
                )
    
    def test_export_summary_statistics(self, export_manager, sample_results):
        """Test that exports include summary statistics."""
        filepath = export_manager.export_to_json(
            results=sample_results,
            theme="Stats test",
            constraints="Include stats"
        )
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Check for computed statistics
        assert data["total_candidates"] == 2
        assert "timestamp" in data
        
        # Verify scores are preserved
        assert data["candidates"][0]["initial_score"] == 7.5
        assert data["candidates"][0]["improved_score"] == 8.5
        assert data["candidates"][1]["initial_score"] == 6.5
        assert data["candidates"][1]["improved_score"] == 7.5


class TestExportFormattingEdgeCases:
    """Test edge cases in export formatting."""
    
    @pytest.fixture
    def export_manager(self):
        """Create ExportManager with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ExportManager(output_dir=tmpdir)
    
    def test_export_very_long_text(self, export_manager):
        """Test exporting results with very long text."""
        long_text = "A" * 10000  # 10k characters
        results = [
            CandidateData(
                idea=long_text,
                initial_score=5.0,
                initial_critique=long_text,
                advocacy=long_text,
                skepticism=long_text,
                improved_idea=long_text,
                improved_score=6.0,
                improved_critique=long_text,
                confidence=0.5,
                dimension_scores={}
            )
        ]
        
        # Should handle long text without issues
        filepath = export_manager.export_to_csv(
            results=results,
            theme="Long text test",
            constraints="Handle gracefully"
        )
        
        assert filepath.exists()
        assert filepath.stat().st_size > 10000  # Should have substantial content
    
    def test_export_special_characters(self, export_manager):
        """Test exporting results with special characters."""
        results = [
            CandidateData(
                idea='Test with "quotes" and \nnewlines',
                initial_score=5.0,
                initial_critique="Contains, commas, and; semicolons",
                advocacy="Tab\there and carriage\rreturn",
                skepticism="Unicode: 你好 мир 🌍",
                improved_idea="<html>tags</html> & entities",
                improved_score=6.0,
                improved_critique="Mixed: 'single' and \"double\" quotes",
                confidence=0.8,
                dimension_scores={}
            )
        ]
        
        # Test all formats handle special characters
        csv_path = export_manager.export_to_csv(results, "Special chars", "Test")
        json_path = export_manager.export_to_json(results, "Special chars", "Test")
        md_path = export_manager.export_to_markdown(results, "Special chars", "Test")
        
        # Verify files are created and readable
        assert csv_path.exists()
        assert json_path.exists()
        assert md_path.exists()
        
        # Verify JSON handles special chars
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert "你好" in data["candidates"][0]["skepticism"]
            assert "🌍" in data["candidates"][0]["skepticism"]