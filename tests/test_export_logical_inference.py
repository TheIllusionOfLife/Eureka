"""Tests for logical inference inclusion in export functions."""
import pytest
import tempfile
import os
from madspark.utils.export_utils import ExportManager
from madspark.core.coordinator import CandidateData


class TestExportLogicalInference:
    """Test cases for logical inference in export formats."""
    
    @pytest.fixture
    def sample_results_with_logical_inference(self):
        """Sample results with logical inference data."""
        return [CandidateData({
            "idea": "Test game concept",
            "initial_score": 8.5,
            "initial_critique": "Good concept with potential",
            "advocacy": "Strong points include innovation",
            "skepticism": "Concerns about market fit",
            "logical_inference": {
                "inference_chain": [
                    "Analyzing game concept feasibility",
                    "Evaluating resource requirements" 
                ],
                "improvements": "**Clarify Mechanics:** Add detailed control scheme\n**Enhance Graphics:** Improve visual appeal\n**Define Target Audience:** Specify age group"
            }
        })]
    
    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for exports."""
        return {
            "theme": "Test theme",
            "constraints": "Test constraints",
            "logical_inference": True
        }
    
    def test_markdown_export_includes_logical_inference(self, sample_results_with_logical_inference, sample_metadata):
        """Test that markdown export includes logical inference section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            # Export to markdown
            markdown_file = export_manager.export_to_markdown(
                sample_results_with_logical_inference, 
                sample_metadata,
                "test_export.md"
            )
            
            # Read the exported file
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify logical inference section is present
            assert "### 🔍 Logical Inference Analysis" in content
            assert "Clarify Mechanics:" in content
            assert "Enhance Graphics:" in content
            assert "Define Target Audience:" in content
            
            # Verify proper markdown formatting (bullets converted to dashes)
            assert "- **Clarify Mechanics:** Add detailed control scheme" in content
            assert "- **Enhance Graphics:** Improve visual appeal" in content
            assert "- **Define Target Audience:** Specify age group" in content
    
    def test_pdf_export_includes_logical_inference(self, sample_results_with_logical_inference, sample_metadata):
        """Test that PDF export includes logical inference section."""
        pytest.importorskip("reportlab", reason="reportlab not available for PDF export")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            # Export to PDF (should not raise error)
            pdf_file = export_manager.export_to_pdf(
                sample_results_with_logical_inference,
                sample_metadata, 
                "test_export.pdf"
            )
            
            # Verify file was created
            assert os.path.exists(pdf_file)
            assert pdf_file.endswith('.pdf')
    
    def test_json_export_preserves_logical_inference_data(self, sample_results_with_logical_inference, sample_metadata):
        """Test that JSON export preserves logical inference data structure."""
        import json
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            # Export to JSON
            json_file = export_manager.export_to_json(
                sample_results_with_logical_inference,
                sample_metadata,
                "test_export.json"
            )
            
            # Read and parse JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verify logical inference data is preserved
            result = data['results'][0]
            assert 'logical_inference' in result
            
            logical_inference = result['logical_inference']
            assert 'inference_chain' in logical_inference
            assert 'improvements' in logical_inference
            assert len(logical_inference['inference_chain']) == 2
            assert "Clarify Mechanics:" in logical_inference['improvements']
    
    def test_export_without_logical_inference(self):
        """Test export works correctly when logical inference is not present."""
        results_without_logical = [CandidateData({
            "idea": "Simple game concept",
            "initial_score": 7.0,
            "initial_critique": "Basic concept",
            "advocacy": "Simple to implement", 
            "skepticism": "May lack engagement"
        })]
        
        metadata = {"theme": "Test", "constraints": "None"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_manager = ExportManager(temp_dir)
            
            # Export to markdown
            markdown_file = export_manager.export_to_markdown(
                results_without_logical,
                metadata,
                "test_no_logical.md"
            )
            
            # Read the exported file
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify logical inference section is NOT present
            assert "### 🔍 Logical Inference Analysis" not in content
            
            # But other sections should still be there
            assert "### Description" in content
            assert "### 🔍 Initial Critique" in content
            assert "### ✅ Advocacy" in content
            assert "### ⚠️ Skeptical Analysis" in content