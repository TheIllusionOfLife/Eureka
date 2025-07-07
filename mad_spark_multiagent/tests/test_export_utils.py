"""Tests for export utilities in MadSpark Phase 2.2."""
import json
import csv
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from export_utils import ExportManager, create_metadata_from_args


@pytest.fixture
def sample_results():
    """Sample results for testing."""
    return [
        {
            "idea": "Smart city IoT platform for traffic optimization",
            "initial_score": 8,
            "initial_critique": "Strong technical feasibility with good market potential",
            "advocacy": "This idea leverages existing IoT infrastructure and could significantly reduce urban congestion",
            "skepticism": "Implementation costs could be high and requires coordination between multiple city departments"
        },
        {
            "idea": "AI-powered personalized learning assistant",
            "initial_score": 7,
            "initial_critique": "Good educational value but competitive market",
            "advocacy": "Addresses growing need for personalized education in digital age",
            "skepticism": "Privacy concerns and need for extensive content development"
        }
    ]


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        "theme": "Urban Innovation",
        "constraints": "Cost-effective, scalable solutions",
        "enhanced_reasoning": True,
        "multi_dimensional_eval": False,
        "logical_inference": True,
        "temperature_preset": "creative"
    }


@pytest.fixture
def export_manager():
    """Export manager with temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield ExportManager(temp_dir)


class TestExportManager:
    """Test cases for ExportManager class."""

    def test_json_export(self, export_manager, sample_results, sample_metadata):
        """Test JSON export functionality."""
        filepath = export_manager.export_to_json(sample_results, sample_metadata)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('.json')
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert 'results' in data
        assert data['metadata']['total_results'] == 2
        assert data['metadata']['theme'] == "Urban Innovation"
        assert len(data['results']) == 2
        assert data['results'][0]['idea'] == sample_results[0]['idea']

    def test_csv_export(self, export_manager, sample_results, sample_metadata):
        """Test CSV export functionality."""
        filepath = export_manager.export_to_csv(sample_results, sample_metadata)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('.csv')
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Urban Innovation" in content
        assert "Smart city IoT platform" in content
        assert "AI-powered personalized learning" in content

    def test_markdown_export(self, export_manager, sample_results, sample_metadata):
        """Test Markdown export functionality."""
        filepath = export_manager.export_to_markdown(sample_results, sample_metadata)
        
        assert os.path.exists(filepath)
        assert filepath.endswith('.md')
        
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# MadSpark Idea Generation Results" in content
        assert "## 💡 Idea #1" in content
        assert "## 💡 Idea #2" in content
        assert "**Enhanced Features:** 🧠 Enhanced Reasoning" in content
        assert sample_results[0]['idea'] in content

    def test_pdf_export_not_available(self, export_manager, sample_results, sample_metadata):
        """Test PDF export when reportlab is not available."""
        with patch('export_utils.PDF_AVAILABLE', False):
            with pytest.raises(ImportError, match="PDF export requires reportlab"):
                export_manager.export_to_pdf(sample_results, sample_metadata)

    @patch('export_utils.PDF_AVAILABLE', True)
    @patch('export_utils.SimpleDocTemplate')
    def test_pdf_export_available(self, mock_doc, export_manager, sample_results, sample_metadata):
        """Test PDF export when reportlab is available."""
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        
        filepath = export_manager.export_to_pdf(sample_results, sample_metadata)
        
        assert filepath.endswith('.pdf')
        mock_doc.assert_called_once()
        mock_doc_instance.build.assert_called_once()

    def test_export_all_formats(self, export_manager, sample_results, sample_metadata):
        """Test exporting to all formats."""
        with patch('export_utils.PDF_AVAILABLE', True):
            with patch('export_utils.SimpleDocTemplate'):
                exported_files = export_manager.export_all_formats(
                    sample_results, sample_metadata, "test_export"
                )
        
        assert 'json' in exported_files
        assert 'csv' in exported_files
        assert 'markdown' in exported_files
        assert 'pdf' in exported_files
        
        # Verify JSON file exists and is valid
        json_path = exported_files['json']
        assert os.path.exists(json_path)
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert len(data['results']) == 2

    def test_custom_filename(self, export_manager, sample_results, sample_metadata):
        """Test export with custom filename."""
        custom_name = "my_custom_export.json"
        filepath = export_manager.export_to_json(sample_results, sample_metadata, custom_name)
        
        assert filepath.endswith(custom_name)
        assert os.path.exists(filepath)

    def test_export_with_enhanced_features(self, export_manager, sample_results):
        """Test export with enhanced reasoning features."""
        metadata = {
            "theme": "AI Innovation",
            "constraints": "Ethical, beneficial",
            "enhanced_reasoning": True,
            "multi_dimensional_eval": True,
            "logical_inference": True
        }
        
        filepath = export_manager.export_to_markdown(sample_results, metadata)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "🧠 Enhanced Reasoning" in content
        assert "📊 Multi-Dimensional Evaluation" in content
        assert "🔗 Logical Inference" in content


class TestCreateMetadataFromArgs:
    """Test cases for create_metadata_from_args function."""

    def test_create_metadata_basic(self, sample_results):
        """Test basic metadata creation from args."""
        mock_args = MagicMock()
        mock_args.theme = "Test Theme"
        mock_args.constraints = "Test Constraints"
        mock_args.enhanced_reasoning = False
        mock_args.multi_dimensional_eval = False
        mock_args.logical_inference = False
        mock_args.temperature_preset = "balanced"
        mock_args.temperature = None
        mock_args.enable_novelty_filter = True
        mock_args.novelty_threshold = 0.8
        mock_args.verbose = False
        mock_args.num_top_candidates = 3
        
        metadata = create_metadata_from_args(mock_args, sample_results)
        
        assert metadata['theme'] == "Test Theme"
        assert metadata['constraints'] == "Test Constraints"
        assert metadata['enhanced_reasoning'] is False
        assert metadata['temperature_preset'] == "balanced"
        assert metadata['novelty_filter_enabled'] is True

    def test_create_metadata_enhanced_features(self, sample_results):
        """Test metadata creation with enhanced features enabled."""
        mock_args = MagicMock()
        mock_args.theme = "Advanced Theme"
        mock_args.constraints = "Complex Constraints"
        mock_args.enhanced_reasoning = True
        mock_args.multi_dimensional_eval = True
        mock_args.logical_inference = True
        mock_args.temperature_preset = None
        mock_args.temperature = 0.9
        mock_args.enable_novelty_filter = False
        mock_args.novelty_threshold = 0.6
        mock_args.verbose = True
        mock_args.num_top_candidates = 5
        
        metadata = create_metadata_from_args(mock_args, sample_results)
        
        assert metadata['enhanced_reasoning'] is True
        assert metadata['multi_dimensional_eval'] is True
        assert metadata['logical_inference'] is True
        assert metadata['temperature'] == 0.9
        assert metadata['novelty_filter_enabled'] is False
        assert metadata['verbose'] is True

    def test_create_metadata_missing_attributes(self, sample_results):
        """Test metadata creation with missing attributes."""
        mock_args = MagicMock()
        # Simulate missing attributes
        del mock_args.theme
        del mock_args.enhanced_reasoning
        
        metadata = create_metadata_from_args(mock_args, sample_results)
        
        assert metadata['theme'] == 'N/A'
        assert metadata['enhanced_reasoning'] is False


class TestExportIntegration:
    """Integration tests for export functionality."""

    def test_export_workflow_integration(self):
        """Test export workflow with realistic data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            # Simulate realistic workflow results
            results = [
                {
                    "idea": "Blockchain-based supply chain transparency platform",
                    "initial_score": 9,
                    "initial_critique": "Excellent technical innovation with strong market demand for supply chain visibility",
                    "advocacy": "Addresses critical need for transparency in global supply chains, particularly for ethical sourcing and authenticity verification",
                    "skepticism": "Requires significant industry adoption and standardization. Energy consumption concerns with blockchain technology"
                }
            ]
            
            metadata = {
                "theme": "Supply Chain Innovation",
                "constraints": "Environmentally sustainable, cost-effective implementation",
                "enhanced_reasoning": True,
                "multi_dimensional_eval": True,
                "logical_inference": False,
                "temperature_preset": "creative",
                "processing_time": 45.2,
                "total_ideas_generated": 8,
                "novelty_filter_removed": 3
            }
            
            # Test all export formats
            exported_files = export_manager.export_all_formats(results, metadata)
            
            # Verify all files were created
            for format_name, file_path in exported_files.items():
                if not file_path.startswith("Error:") and not file_path.startswith("Not available"):
                    assert os.path.exists(file_path)
                    assert os.path.getsize(file_path) > 0  # File is not empty

    def test_export_empty_results(self):
        """Test export behavior with empty results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            results = []
            metadata = {"theme": "Empty Test", "constraints": "None"}
            
            # Should not raise errors
            filepath = export_manager.export_to_json(results, metadata)
            assert os.path.exists(filepath)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            assert data['metadata']['total_results'] == 0
            assert data['results'] == []

    def test_export_unicode_content(self):
        """Test export with Unicode content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            results = [
                {
                    "idea": "日本の伝統技術とAIの融合プラットフォーム",
                    "initial_score": 8,
                    "initial_critique": "文化的価値と技術革新の優れた組み合わせ",
                    "advocacy": "伝統文化の保護と現代技術の利点を両立",
                    "skepticism": "実装の複雑さと市場受容性の課題"
                }
            ]
            
            metadata = {"theme": "Cultural Innovation", "constraints": "Respectful integration"}
            
            # Test JSON export with Unicode
            filepath = export_manager.export_to_json(results, metadata)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "日本の伝統技術" in content
            
            # Test Markdown export with Unicode
            md_filepath = export_manager.export_to_markdown(results, metadata)
            with open(md_filepath, 'r', encoding='utf-8') as f:
                md_content = f.read()
            assert "日本の伝統技術" in md_content