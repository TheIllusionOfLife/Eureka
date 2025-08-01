"""Batch API Call Monitoring and Cost Analysis.

This module provides comprehensive monitoring for batch API calls to ensure
cost-effectiveness and performance tracking.
"""
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from .pricing_config import estimate_cost


@dataclass
class BatchMetrics:
    """Metrics for a single batch API call."""
    timestamp: str
    batch_type: str  # 'advocate', 'skeptic', 'improve', 'multi_dimensional', etc.
    items_count: int  # Number of items processed in batch
    tokens_used: Optional[int] = None  # Actual tokens from API response
    duration_seconds: float = 0.0
    estimated_cost_usd: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    fallback_used: bool = False  # If batch failed and fell back to individual calls
    
    @property
    def tokens_per_item(self) -> Optional[float]:
        """Calculate tokens per item if tokens are available."""
        if self.tokens_used and self.items_count > 0:
            return self.tokens_used / self.items_count
        return None
    
    @property
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        if self.duration_seconds > 0:
            return self.items_count / self.duration_seconds
        return 0.0


class BatchMonitor:
    """Monitor batch API performance and cost-effectiveness."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize the batch monitor.
        
        Args:
            log_file: Optional path to log metrics to file. If None, logs to .madspark/batch_metrics.jsonl
        """
        self.metrics_history: List[BatchMetrics] = []
        self.session_start = datetime.now()
        
        # Set up logging file
        if log_file is None:
            log_dir = Path.home() / ".madspark"
            log_dir.mkdir(exist_ok=True)
            log_file = str(log_dir / "batch_metrics.jsonl")
        
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
    
    def start_batch_call(self, batch_type: str, items_count: int) -> Dict[str, Any]:
        """Start tracking a batch call.
        
        Args:
            batch_type: Type of batch operation ('advocate', 'skeptic', etc.)
            items_count: Number of items being processed
            
        Returns:
            Context dict to pass to end_batch_call()
        """
        return {
            "batch_type": batch_type,
            "items_count": items_count,
            "start_time": time.time(),
            "timestamp": datetime.now().isoformat()
        }
    
    def end_batch_call(
        self, 
        context: Dict[str, Any], 
        success: bool = True,
        tokens_used: Optional[int] = None,
        error_message: Optional[str] = None,
        fallback_used: bool = False,
        model_name: Optional[str] = None
    ) -> BatchMetrics:
        """End tracking a batch call and record metrics.
        
        Args:
            context: Context dict from start_batch_call()
            success: Whether the batch call succeeded
            tokens_used: Actual tokens used (if available from API response)
            error_message: Error message if call failed
            fallback_used: Whether fallback to individual calls was used
            model_name: The model name used for the API call (e.g., 'gemini-1.5-pro')
            
        Returns:
            BatchMetrics object with recorded data
        """
        end_time = time.time()
        duration = end_time - context["start_time"]
        
        # Estimate cost if tokens are available
        estimated_cost = None
        if tokens_used and model_name:
            # Use pricing configuration to estimate cost
            estimated_cost = estimate_cost(model_name, tokens_used)
        elif tokens_used:
            # Fallback to default model if not specified
            estimated_cost = estimate_cost("gemini-1.5-pro", tokens_used)
        
        metrics = BatchMetrics(
            timestamp=context["timestamp"],
            batch_type=context["batch_type"],
            items_count=context["items_count"],
            tokens_used=tokens_used,
            duration_seconds=duration,
            estimated_cost_usd=estimated_cost,
            success=success,
            error_message=error_message,
            fallback_used=fallback_used
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Log to file
        self._log_to_file(metrics)
        
        # Log summary
        self._log_summary(metrics)
        
        return metrics
    
    def _log_to_file(self, metrics: BatchMetrics):
        """Log metrics to JSONL file."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(asdict(metrics)) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to log metrics to file: {e}")
    
    def _log_summary(self, metrics: BatchMetrics):
        """Log human-readable summary."""
        if metrics.success:
            tokens_info = f", {metrics.tokens_used} tokens" if metrics.tokens_used else ""
            cost_info = f", ~${metrics.estimated_cost_usd:.4f}" if metrics.estimated_cost_usd else ""
            fallback_info = " (fallback used)" if metrics.fallback_used else ""
            
            self.logger.info(
                f"Batch {metrics.batch_type}: {metrics.items_count} items in {metrics.duration_seconds:.2f}s"
                f"{tokens_info}{cost_info}{fallback_info}"
            )
        else:
            self.logger.error(
                f"Batch {metrics.batch_type} FAILED: {metrics.error_message}"
            )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session metrics."""
        if not self.metrics_history:
            return {"message": "No batch calls recorded in this session"}
        
        successful_calls = [m for m in self.metrics_history if m.success]
        failed_calls = [m for m in self.metrics_history if not m.success]
        fallback_calls = [m for m in self.metrics_history if m.fallback_used]
        
        total_items = sum(m.items_count for m in successful_calls)
        total_duration = sum(m.duration_seconds for m in successful_calls)
        total_tokens = sum(m.tokens_used for m in successful_calls if m.tokens_used)
        total_cost = sum(m.estimated_cost_usd for m in successful_calls if m.estimated_cost_usd)
        
        # Calculate efficiency metrics
        batch_types = {}
        for metrics in successful_calls:
            if metrics.batch_type not in batch_types:
                batch_types[metrics.batch_type] = {
                    "calls": 0,
                    "items": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "duration": 0.0
                }
            
            batch_types[metrics.batch_type]["calls"] += 1
            batch_types[metrics.batch_type]["items"] += metrics.items_count
            batch_types[metrics.batch_type]["tokens"] += metrics.tokens_used or 0
            batch_types[metrics.batch_type]["cost"] += metrics.estimated_cost_usd or 0.0
            batch_types[metrics.batch_type]["duration"] += metrics.duration_seconds
        
        return {
            "session_start": self.session_start.isoformat(),
            "session_duration_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "total_calls": len(self.metrics_history),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "fallback_calls": len(fallback_calls),
            "total_items_processed": total_items,
            "total_tokens_used": total_tokens,
            "total_estimated_cost_usd": total_cost,
            "total_processing_time_seconds": total_duration,
            "average_items_per_second": total_items / total_duration if total_duration > 0 else 0,
            "average_tokens_per_item": total_tokens / total_items if total_items > 0 else 0,
            "batch_type_breakdown": batch_types
        }
    
    def analyze_cost_effectiveness(self) -> Dict[str, Any]:
        """Analyze whether batch processing is cost-effective vs individual calls."""
        successful_calls = [m for m in self.metrics_history if m.success and not m.fallback_used]
        
        if not successful_calls:
            return {"message": "No successful batch calls to analyze"}
        
        analysis = {
            "batch_effectiveness": {},
            "recommendations": []
        }
        
        # Group by batch type for analysis
        by_type = {}
        for metrics in successful_calls:
            if metrics.batch_type not in by_type:
                by_type[metrics.batch_type] = []
            by_type[metrics.batch_type].append(metrics)
        
        for batch_type, calls in by_type.items():
            total_items = sum(c.items_count for c in calls)
            total_cost = sum(c.estimated_cost_usd or 0 for c in calls)
            avg_tokens_per_item = sum(c.tokens_per_item or 0 for c in calls) / len(calls)
            
            # Estimate individual call cost (rough estimate)
            estimated_individual_cost = total_items * (avg_tokens_per_item * 0.005 / 1000)  # Rough estimate
            
            cost_savings = estimated_individual_cost - total_cost
            savings_percentage = (cost_savings / estimated_individual_cost * 100) if estimated_individual_cost > 0 else 0
            
            analysis["batch_effectiveness"][batch_type] = {
                "total_calls": len(calls),
                "total_items": total_items,
                "batch_cost": total_cost,
                "estimated_individual_cost": estimated_individual_cost,
                "cost_savings": cost_savings,
                "savings_percentage": savings_percentage,
                "average_tokens_per_item": avg_tokens_per_item,
                "recommendation": "EFFECTIVE" if savings_percentage > 0 else "REVIEW_NEEDED"
            }
            
            if savings_percentage > 20:
                analysis["recommendations"].append(f"{batch_type}: Excellent savings ({savings_percentage:.1f}%)")
            elif savings_percentage > 0:
                analysis["recommendations"].append(f"{batch_type}: Good savings ({savings_percentage:.1f}%)")
            else:
                analysis["recommendations"].append(f"{batch_type}: Review needed - may be more expensive than individual calls")
        
        return analysis


# Global monitor instance
_global_monitor: Optional[BatchMonitor] = None


def get_batch_monitor() -> BatchMonitor:
    """Get the global batch monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = BatchMonitor()
    return _global_monitor


def reset_batch_monitor():
    """Reset the global monitor (useful for testing)."""
    global _global_monitor
    _global_monitor = None


# Context manager for easy batch monitoring
class batch_call_context:
    """Context manager for monitoring batch API calls."""
    
    def __init__(self, batch_type: str, items_count: int, monitor: Optional[BatchMonitor] = None):
        self.batch_type = batch_type
        self.items_count = items_count
        self.monitor = monitor or get_batch_monitor()
        self.context = None
        self.tokens_used = None
        self.error_message = None
        self.fallback_used = False
        self.model_name = None
    
    def __enter__(self):
        self.context = self.monitor.start_batch_call(self.batch_type, self.items_count)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        error_message = str(exc_val) if exc_val else self.error_message
        
        self.monitor.end_batch_call(
            self.context,
            success=success,
            tokens_used=self.tokens_used,
            error_message=error_message,
            fallback_used=self.fallback_used,
            model_name=self.model_name
        )
        
        # Don't suppress exceptions
        return False
    
    def set_tokens_used(self, tokens: int):
        """Set the actual tokens used from API response."""
        self.tokens_used = tokens
    
    def set_fallback_used(self, error_message: str = None):
        """Mark that fallback to individual calls was used."""
        self.fallback_used = True
        if error_message:
            self.error_message = error_message
    
    def set_model_name(self, model_name: str):
        """Set the model name used for the API call."""
        self.model_name = model_name