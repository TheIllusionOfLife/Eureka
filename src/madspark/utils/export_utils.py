"""
Export utilities for MadSpark Multi-Agent System - Phase 2.2

This module provides functionality to export idea generation results
to various formats including JSON, CSV, Markdown, and PDF.
"""
import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from coordinator import CandidateData


class ExportManager:
    """Manages export functionality for MadSpark results."""
    
    def __init__(self, output_dir: str = "exports"):
        """Initialize export manager with output directory."""
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(exist_ok=True, parents=True)
        except PermissionError:
            raise PermissionError(f"Permission denied: Cannot create export directory '{output_dir}'")
        except OSError as e:
            raise OSError(f"Failed to create export directory '{output_dir}': {e}")
        
    def _get_output_filepath(self, filename: Optional[str], extension: str) -> Path:
        """Generate output filepath with timestamp if filename not provided."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"madspark_results_{timestamp}.{extension}"
        return self.output_dir / filename
        
    def export_to_json(
        self, 
        results: List[CandidateData], 
        metadata: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export results to JSON format."""
        filepath = self._get_output_filepath(filename, "json")
        
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "madspark_version": "2.2.0",
                "total_results": len(results),
                **metadata
            },
            "results": [dict(result) for result in results]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def export_to_csv(
        self, 
        results: List[CandidateData], 
        metadata: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export results to CSV format."""
        filepath = self._get_output_filepath(filename, "csv")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write metadata as comments
            writer.writerow([f"# MadSpark Export - {datetime.now().isoformat()}"])
            writer.writerow([f"# Theme: {metadata.get('theme', 'N/A')}"])
            writer.writerow([f"# Constraints: {metadata.get('constraints', 'N/A')}"])
            writer.writerow([f"# Total Results: {len(results)}"])
            writer.writerow([])  # Empty row
            
            # Write headers
            headers = [
                "Idea",
                "Initial Score",
                "Initial Critique",
                "Advocacy",
                "Skepticism"
            ]
            writer.writerow(headers)
            
            # Write data
            for result in results:
                result_dict = dict(result)  # Convert to dict for safe access
                row = [
                    result_dict["idea"],
                    result_dict["initial_score"],
                    result_dict["initial_critique"],
                    result_dict["advocacy"],
                    result_dict["skepticism"]
                ]
                writer.writerow(row)
        
        return str(filepath)
    
    def export_to_markdown(
        self, 
        results: List[CandidateData], 
        metadata: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export results to Markdown format."""
        filepath = self._get_output_filepath(filename, "md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("# MadSpark Idea Generation Results\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Theme:** {metadata.get('theme', 'N/A')}\n\n")
            f.write(f"**Constraints:** {metadata.get('constraints', 'N/A')}\n\n")
            f.write(f"**Total Results:** {len(results)}\n\n")
            
            # Write enhanced features info if available
            if metadata.get('enhanced_reasoning'):
                f.write("**Enhanced Features:** 🧠 Enhanced Reasoning")
                if metadata.get('multi_dimensional_eval'):
                    f.write(", 📊 Multi-Dimensional Evaluation")
                if metadata.get('logical_inference'):
                    f.write(", 🔗 Logical Inference")
                f.write("\n\n")
            
            f.write("---\n\n")
            
            # Write results
            for i, result in enumerate(results, 1):
                result_dict = dict(result)  # Convert to dict for safe access
                f.write(f"## 💡 Idea #{i}\n\n")
                f.write(f"**Score:** {result_dict['initial_score']}/10 ⭐\n\n")
                f.write(f"### Description\n\n")
                f.write(f"{result_dict['idea']}\n\n")
                
                f.write(f"### 🔍 Initial Critique\n\n")
                f.write(f"{result_dict['initial_critique']}\n\n")
                
                f.write(f"### ✅ Advocacy\n\n")
                f.write(f"{result_dict['advocacy']}\n\n")
                
                f.write(f"### ⚠️ Skeptical Analysis\n\n")
                f.write(f"{result_dict['skepticism']}\n\n")
                
                if i < len(results):
                    f.write("---\n\n")
        
        return str(filepath)
    
    def export_to_pdf(
        self, 
        results: List[CandidateData], 
        metadata: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """Export results to PDF format."""
        if not PDF_AVAILABLE:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )
        
        filepath = self._get_output_filepath(filename, "pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1d4ed8')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#3b82f6')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=6,
            textColor=colors.HexColor('#6b7280')
        )
        
        # Title
        story.append(Paragraph("🧠 MadSpark Idea Generation Results", title_style))
        story.append(Spacer(1, 20))
        
        # Metadata table
        metadata_data = [
            ["Generated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Theme:", metadata.get('theme', 'N/A')],
            ["Constraints:", metadata.get('constraints', 'N/A')],
            ["Total Results:", str(len(results))],
        ]
        
        if metadata.get('enhanced_reasoning'):
            features = ["Enhanced Reasoning"]
            if metadata.get('multi_dimensional_eval'):
                features.append("Multi-Dimensional Evaluation")
            if metadata.get('logical_inference'):
                features.append("Logical Inference")
            metadata_data.append(["Enhanced Features:", ", ".join(features)])
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Results
        for i, result in enumerate(results, 1):
            result_dict = dict(result)  # Convert to dict for safe access
            # Idea header
            story.append(Paragraph(f"💡 Idea #{i}", heading_style))
            story.append(Paragraph(f"Score: {result_dict['initial_score']}/10 ⭐", subheading_style))
            story.append(Spacer(1, 10))
            
            # Idea description
            story.append(Paragraph("<b>Description:</b>", styles['Normal']))
            story.append(Paragraph(result_dict['idea'], styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Critique
            story.append(Paragraph("<b>🔍 Initial Critique:</b>", styles['Normal']))
            story.append(Paragraph(result_dict['initial_critique'], styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Advocacy
            story.append(Paragraph("<b>✅ Advocacy:</b>", styles['Normal']))
            story.append(Paragraph(result_dict['advocacy'], styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Skepticism
            story.append(Paragraph("<b>⚠️ Skeptical Analysis:</b>", styles['Normal']))
            story.append(Paragraph(result_dict['skepticism'], styles['Normal']))
            
            if i < len(results):
                story.append(Spacer(1, 30))
        
        # Build PDF
        doc.build(story)
        
        return str(filepath)
    
    def export_all_formats(
        self, 
        results: List[CandidateData], 
        metadata: Dict[str, Any],
        base_filename: Optional[str] = None
    ) -> Dict[str, str]:
        """Export results to all available formats."""
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"madspark_results_{timestamp}"
        
        exported_files = {}
        
        # JSON export
        try:
            json_file = self.export_to_json(results, metadata, f"{base_filename}.json")
            exported_files['json'] = json_file
        except Exception as e:
            exported_files['json'] = f"Error: {e}"
        
        # CSV export
        try:
            csv_file = self.export_to_csv(results, metadata, f"{base_filename}.csv")
            exported_files['csv'] = csv_file
        except Exception as e:
            exported_files['csv'] = f"Error: {e}"
        
        # Markdown export
        try:
            md_file = self.export_to_markdown(results, metadata, f"{base_filename}.md")
            exported_files['markdown'] = md_file
        except Exception as e:
            exported_files['markdown'] = f"Error: {e}"
        
        # PDF export (only if available)
        if PDF_AVAILABLE:
            try:
                pdf_file = self.export_to_pdf(results, metadata, f"{base_filename}.pdf")
                exported_files['pdf'] = pdf_file
            except Exception as e:
                exported_files['pdf'] = f"Error: {e}"
        else:
            exported_files['pdf'] = "Not available (install reportlab for PDF export)"
        
        return exported_files


def create_metadata_from_args(args, results: List[CandidateData]) -> Dict[str, Any]:
    """Create metadata dictionary from command line arguments."""
    return {
        "theme": getattr(args, 'theme', 'N/A'),
        "constraints": getattr(args, 'constraints', 'N/A'),
        "num_top_candidates": getattr(args, 'num_top_candidates', len(results)),
        "temperature_preset": getattr(args, 'temperature_preset', None),
        "temperature": getattr(args, 'temperature', None),
        "enhanced_reasoning": getattr(args, 'enhanced_reasoning', False),
        "multi_dimensional_eval": getattr(args, 'multi_dimensional_eval', False),
        "logical_inference": getattr(args, 'logical_inference', False),
        "novelty_filter_enabled": getattr(args, 'enable_novelty_filter', True),
        "novelty_threshold": getattr(args, 'novelty_threshold', 0.8),
        "verbose": getattr(args, 'verbose', False),
    }