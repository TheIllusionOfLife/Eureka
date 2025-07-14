"""Batch Processing for MadSpark Multi-Agent System.

This module provides functionality to process multiple themes and constraints
in batch mode, with support for parallel execution and progress tracking.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import csv

from coordinator import run_multistep_workflow
from async_coordinator import AsyncCoordinator
from temperature_control import TemperatureManager
from cache_manager import CacheManager, CacheConfig
from export_utils import ExportManager
from constants import DEFAULT_NUM_TOP_CANDIDATES

logger = logging.getLogger(__name__)


def sanitize_filename(text: str, max_length: int = 30) -> str:
    """Sanitize text for use in filenames.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length of sanitized text
        
    Returns:
        Sanitized filename component
    """
    # Replace spaces with underscores
    sanitized = text.replace(' ', '_')
    # Remove/replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', sanitized)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Trim length and remove trailing underscores
    sanitized = sanitized[:max_length].rstrip('_')
    # Ensure we have at least something
    return sanitized or 'untitled'


class BatchItem:
    """Represents a single item in a batch processing job."""
    
    def __init__(self, theme: str, constraints: str, 
                 temperature_preset: Optional[str] = None,
                 num_candidates: int = DEFAULT_NUM_TOP_CANDIDATES,
                 tags: Optional[List[str]] = None):
        """Initialize a batch item.
        
        Args:
            theme: Theme for idea generation
            constraints: Constraints for the ideas
            temperature_preset: Optional temperature preset name
            num_candidates: Number of top candidates to process
            tags: Optional tags for bookmarking
        """
        self.theme = theme
        self.constraints = constraints
        self.temperature_preset = temperature_preset
        self.num_candidates = num_candidates
        self.tags = tags or []
        self.status = "pending"
        self.result = None
        self.error = None
        self.processing_time = 0.0
        self.start_time = None
        self.end_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch item to dictionary."""
        return {
            "theme": self.theme,
            "constraints": self.constraints,
            "temperature_preset": self.temperature_preset,
            "num_candidates": self.num_candidates,
            "tags": self.tags,
            "status": self.status,
            "error": self.error,
            "processing_time": self.processing_time
        }


class BatchProcessor:
    """Processes multiple themes in batch mode."""
    
    def __init__(self, 
                 max_concurrent: int = 3,
                 use_async: bool = True,
                 enable_cache: bool = False,
                 export_dir: str = "batch_exports",
                 verbose: bool = False):
        """Initialize batch processor.
        
        Args:
            max_concurrent: Maximum concurrent processing tasks
            use_async: Use async processing for better performance
            enable_cache: Enable Redis caching
            export_dir: Directory for batch export results
            verbose: Enable verbose logging
        """
        self.max_concurrent = max_concurrent
        self.use_async = use_async
        self.enable_cache = enable_cache
        self.export_dir = Path(export_dir)
        self.verbose = verbose
        self.cache_manager = None
        self.export_manager = ExportManager(str(self.export_dir))
        
        # Create export directory
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize async components like cache manager."""
        if self.enable_cache:
            cache_config = CacheConfig(
                redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                ttl_seconds=int(os.getenv("CACHE_TTL", "3600"))
            )
            self.cache_manager = CacheManager(cache_config)
            await self.cache_manager.initialize()
            logger.info("Cache manager initialized for batch processing")
            
    async def close(self):
        """Close async components."""
        if self.cache_manager:
            await self.cache_manager.close()
            
    def load_batch_from_csv(self, csv_path: str) -> List[BatchItem]:
        """Load batch items from CSV file.
        
        CSV format:
        theme,constraints,temperature_preset,num_candidates,tags
        "AI in healthcare","Budget-friendly",creative,3,"health,ai"
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of BatchItem objects
        """
        batch_items = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse tags if provided
                tags = []
                if 'tags' in row and row['tags']:
                    tags = [tag.strip() for tag in row['tags'].split(',')]
                
                # Parse num_candidates
                num_candidates = DEFAULT_NUM_TOP_CANDIDATES
                if 'num_candidates' in row and row['num_candidates']:
                    try:
                        num_candidates = int(row['num_candidates'])
                    except ValueError:
                        logger.warning(f"Invalid num_candidates: {row['num_candidates']}, using default")
                
                # Validate required fields
                if 'theme' not in row or not row['theme']:
                    logger.warning(f"Skipping row {reader.line_num}: missing required 'theme' field")
                    continue
                    
                item = BatchItem(
                    theme=row['theme'],
                    constraints=row.get('constraints', ''),
                    temperature_preset=row.get('temperature_preset'),
                    num_candidates=num_candidates,
                    tags=tags
                )
                batch_items.append(item)
                
        logger.info(f"Loaded {len(batch_items)} items from {csv_path}")
        return batch_items
        
    def load_batch_from_json(self, json_path: str) -> List[BatchItem]:
        """Load batch items from JSON file.
        
        JSON format:
        [
            {
                "theme": "AI in healthcare",
                "constraints": "Budget-friendly",
                "temperature_preset": "creative",
                "num_candidates": 3,
                "tags": ["health", "ai"]
            }
        ]
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            List of BatchItem objects
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        batch_items = []
        for i, item_data in enumerate(data):
            # Validate required fields
            if 'theme' not in item_data or not item_data['theme']:
                logger.warning(f"Skipping item {i}: missing required 'theme' field")
                continue
                
            item = BatchItem(
                theme=item_data['theme'],
                constraints=item_data.get('constraints', ''),
                temperature_preset=item_data.get('temperature_preset'),
                num_candidates=item_data.get('num_candidates', DEFAULT_NUM_TOP_CANDIDATES),
                tags=item_data.get('tags', [])
            )
            batch_items.append(item)
            
        logger.info(f"Loaded {len(batch_items)} items from {json_path}")
        return batch_items
        
    async def process_single_item_async(self, item: BatchItem, 
                                      coordinator: AsyncCoordinator,
                                      workflow_options: Dict[str, Any]) -> None:
        """Process a single batch item asynchronously.
        
        Args:
            item: BatchItem to process
            coordinator: AsyncCoordinator instance
            workflow_options: Common workflow options
        """
        item.status = "processing"
        item.start_time = datetime.now()
        
        try:
            # Create temperature manager for this item
            temp_manager = None
            if item.temperature_preset:
                temp_manager = TemperatureManager.from_preset(item.temperature_preset)
            else:
                temp_manager = TemperatureManager()
                
            # Run workflow
            logger.info(f"Processing: {item.theme}")
            result = await coordinator.run_workflow(
                theme=item.theme,
                constraints=item.constraints,
                num_top_candidates=item.num_candidates,
                temperature_manager=temp_manager,
                **workflow_options
            )
            
            item.result = result
            item.status = "completed"
            logger.info(f"Completed: {item.theme} - {len(result)} ideas generated")
            
        except Exception as e:
            item.status = "failed"
            item.error = str(e)
            logger.error(f"Failed to process '{item.theme}': {e}")
            
        finally:
            item.end_time = datetime.now()
            item.processing_time = (item.end_time - item.start_time).total_seconds()
            
    def process_single_item_sync(self, item: BatchItem,
                               workflow_options: Dict[str, Any]) -> None:
        """Process a single batch item synchronously.
        
        Args:
            item: BatchItem to process
            workflow_options: Common workflow options
        """
        item.status = "processing"
        item.start_time = datetime.now()
        
        try:
            # Create temperature manager for this item
            temp_manager = None
            if item.temperature_preset:
                temp_manager = TemperatureManager.from_preset(item.temperature_preset)
            else:
                temp_manager = TemperatureManager()
                
            # Run workflow
            logger.info(f"Processing: {item.theme}")
            result = run_multistep_workflow(
                theme=item.theme,
                constraints=item.constraints,
                num_top_candidates=item.num_candidates,
                temperature_manager=temp_manager,
                **workflow_options
            )
            
            item.result = result
            item.status = "completed"
            logger.info(f"Completed: {item.theme} - {len(result)} ideas generated")
            
        except Exception as e:
            item.status = "failed"
            item.error = str(e)
            logger.error(f"Failed to process '{item.theme}': {e}")
            
        finally:
            item.end_time = datetime.now()
            item.processing_time = (item.end_time - item.start_time).total_seconds()
            
    async def process_batch_async(self, batch_items: List[BatchItem],
                                workflow_options: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch items asynchronously with concurrency control.
        
        Args:
            batch_items: List of BatchItem objects
            workflow_options: Common workflow options
            
        Returns:
            Batch processing summary
        """
        # Initialize async components
        await self.initialize()
        
        try:
            # Create coordinator
            coordinator = AsyncCoordinator(
                max_concurrent_agents=10,
                cache_manager=self.cache_manager
            )
            
            # Process items with semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def process_with_semaphore(item):
                async with semaphore:
                    await self.process_single_item_async(item, coordinator, workflow_options)
                    
            # Process all items
            tasks = [process_with_semaphore(item) for item in batch_items]
            await asyncio.gather(*tasks)
            
        finally:
            await self.close()
            
        return self._create_summary(batch_items)
        
    def process_batch_sync(self, batch_items: List[BatchItem],
                         workflow_options: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch items synchronously.
        
        Args:
            batch_items: List of BatchItem objects
            workflow_options: Common workflow options
            
        Returns:
            Batch processing summary
        """
        for i, item in enumerate(batch_items):
            logger.info(f"Processing item {i+1}/{len(batch_items)}")
            self.process_single_item_sync(item, workflow_options)
            
        return self._create_summary(batch_items)
        
    def process_batch(self, batch_items: List[BatchItem],
                     workflow_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a batch of items.
        
        Args:
            batch_items: List of BatchItem objects
            workflow_options: Optional workflow options
            
        Returns:
            Batch processing summary
        """
        if workflow_options is None:
            workflow_options = {
                "enable_novelty_filter": True,
                "novelty_threshold": 0.8,
                "verbose": self.verbose
            }
            
        start_time = datetime.now()
        
        # Process batch
        if self.use_async:
            summary = asyncio.run(self.process_batch_async(batch_items, workflow_options))
        else:
            summary = self.process_batch_sync(batch_items, workflow_options)
            
        # Calculate total time
        end_time = datetime.now()
        summary['total_processing_time'] = (end_time - start_time).total_seconds()
        
        return summary
        
    def _create_summary(self, batch_items: List[BatchItem]) -> Dict[str, Any]:
        """Create summary of batch processing results.
        
        Args:
            batch_items: Processed batch items
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_items": len(batch_items),
            "completed": sum(1 for item in batch_items if item.status == "completed"),
            "failed": sum(1 for item in batch_items if item.status == "failed"),
            "pending": sum(1 for item in batch_items if item.status == "pending"),
            "items": []
        }
        
        for item in batch_items:
            item_summary = item.to_dict()
            if item.result:
                item_summary['ideas_generated'] = len(item.result)
            summary["items"].append(item_summary)
            
        return summary
        
    def export_batch_results(self, batch_items: List[BatchItem], 
                           batch_id: Optional[str] = None) -> Dict[str, str]:
        """Export batch processing results to files.
        
        Args:
            batch_items: Processed batch items
            batch_id: Optional batch identifier
            
        Returns:
            Dictionary of export file paths
        """
        if not batch_id:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        exported_files = {}
        
        # Create batch summary
        summary = self._create_summary(batch_items)
        summary['batch_id'] = batch_id
        summary['export_timestamp'] = datetime.now().isoformat()
        
        # Export summary JSON
        summary_path = self.export_dir / f"batch_{batch_id}_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        exported_files['summary'] = str(summary_path)
        
        # Export detailed results for each completed item
        for i, item in enumerate(batch_items):
            if item.status == "completed" and item.result:
                # Create metadata for this item
                metadata = {
                    "theme": item.theme,
                    "constraints": item.constraints,
                    "temperature_preset": item.temperature_preset,
                    "num_candidates": item.num_candidates,
                    "tags": item.tags,
                    "processing_time": item.processing_time,
                    "timestamp": item.end_time.isoformat() if item.end_time else None
                }
                
                # Export to multiple formats
                base_filename = f"batch_{batch_id}_item_{i+1}_{sanitize_filename(item.theme)}"
                
                # JSON export
                json_path = self.export_manager.export_to_json(
                    item.result, metadata, base_filename
                )
                
                # Markdown export
                md_path = self.export_manager.export_to_markdown(
                    item.result, metadata, base_filename
                )
                
                exported_files[f"item_{i+1}"] = {
                    "json": json_path,
                    "markdown": md_path
                }
                
        logger.info(f"Exported batch results to {self.export_dir}")
        return exported_files
        
    def create_batch_report(self, batch_items: List[BatchItem], 
                          batch_id: Optional[str] = None) -> str:
        """Create a human-readable batch processing report.
        
        Args:
            batch_items: Processed batch items
            batch_id: Optional batch identifier
            
        Returns:
            Path to the report file
        """
        if not batch_id:
            batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        report_path = self.export_dir / f"batch_{batch_id}_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# MadSpark Batch Processing Report\n\n")
            f.write(f"**Batch ID:** {batch_id}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary
            summary = self._create_summary(batch_items)
            f.write("## Summary\n\n")
            f.write(f"- **Total Items:** {summary['total_items']}\n")
            f.write(f"- **Completed:** {summary['completed']}\n")
            f.write(f"- **Failed:** {summary['failed']}\n")
            f.write(f"- **Pending:** {summary['pending']}\n\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            
            for i, item in enumerate(batch_items, 1):
                f.write(f"### {i}. {item.theme}\n\n")
                f.write(f"**Status:** {item.status}\n")
                f.write(f"**Constraints:** {item.constraints}\n")
                f.write(f"**Processing Time:** {item.processing_time:.2f}s\n")
                
                if item.temperature_preset:
                    f.write(f"**Temperature Preset:** {item.temperature_preset}\n")
                    
                if item.tags:
                    f.write(f"**Tags:** {', '.join(item.tags)}\n")
                    
                if item.status == "completed" and item.result:
                    f.write(f"**Ideas Generated:** {len(item.result)}\n\n")
                    
                    # Show top idea
                    if item.result:
                        top_idea = item.result[0]
                        f.write("**Top Idea:**\n")
                        f.write(f"> {top_idea.get('idea', 'N/A')}\n\n")
                        f.write(f"**Score:** {top_idea.get('initial_score', 'N/A')}/10\n\n")
                        
                elif item.status == "failed":
                    f.write(f"**Error:** {item.error}\n\n")
                    
                f.write("---\n\n")
                
        logger.info(f"Created batch report: {report_path}")
        return str(report_path)


def create_sample_batch_file(output_path: str, format: str = "csv"):
    """Create a sample batch file for testing.
    
    Args:
        output_path: Path to save the sample file
        format: File format ('csv' or 'json')
    """
    sample_data = [
        {
            "theme": "AI in healthcare",
            "constraints": "Budget-friendly, implementable within 6 months",
            "temperature_preset": "balanced",
            "num_candidates": 2,
            "tags": ["healthcare", "ai", "budget"]
        },
        {
            "theme": "Sustainable urban farming",
            "constraints": "Small spaces, minimal water usage",
            "temperature_preset": "creative",
            "num_candidates": 3,
            "tags": ["sustainability", "urban", "farming"]
        },
        {
            "theme": "Remote education technology",
            "constraints": "Works offline, accessible to all ages",
            "temperature_preset": "conservative",
            "num_candidates": 2,
            "tags": ["education", "remote", "accessibility"]
        }
    ]
    
    if format == "csv":
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "theme", "constraints", "temperature_preset", 
                "num_candidates", "tags"
            ])
            writer.writeheader()
            
            for item in sample_data:
                row = item.copy()
                row['tags'] = ','.join(row['tags'])
                writer.writerow(row)
                
    else:  # json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
    print(f"Created sample batch file: {output_path}")