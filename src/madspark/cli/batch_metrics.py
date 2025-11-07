"""CLI command for viewing batch API call metrics and cost analysis."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from madspark.utils.batch_monitor import BatchMetrics
from madspark.utils.constants import (
    INDIVIDUAL_CALL_OVERHEAD_MULTIPLIER,
    ORIGINAL_CALLS_PER_ITEM,
    PERCENTAGE_CONVERSION_FACTOR
)


def load_metrics_from_file(log_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load metrics from the batch monitoring log file."""
    if log_file is None:
        log_dir = Path.home() / ".madspark"
        log_file = str(log_dir / "batch_metrics.jsonl")
    
    if not Path(log_file).exists():
        return []
    
    metrics = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    metrics.append(json.loads(line.strip()))
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return []
    
    return metrics


def format_metrics_summary(metrics_data: List[Dict[str, Any]]) -> str:
    """Format metrics data into a human-readable summary."""
    if not metrics_data:
        return "No batch metrics found. Run some batch operations first."
    
    # Convert to BatchMetrics objects for analysis
    metrics_objects = []
    for data in metrics_data:
        try:
            metrics_objects.append(BatchMetrics(**data))
        except (TypeError, ValueError, KeyError):
            continue  # Skip malformed entries
    
    if not metrics_objects:
        return "No valid metrics found."
    
    # Group by date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=7)
    
    today_metrics = [m for m in metrics_objects if datetime.fromisoformat(m.timestamp).date() == today]
    yesterday_metrics = [m for m in metrics_objects if datetime.fromisoformat(m.timestamp).date() == yesterday]
    week_metrics = [m for m in metrics_objects if datetime.fromisoformat(m.timestamp).date() >= this_week]
    
    output = []
    output.append("🚀 Batch API Metrics Summary")
    output.append("=" * 40)
    
    # Today's summary
    if today_metrics:
        output.append(f"\n📅 Today ({today})")
        output.append(_format_period_summary(today_metrics))
    
    # Yesterday's summary
    if yesterday_metrics:
        output.append(f"\n📅 Yesterday ({yesterday})")
        output.append(_format_period_summary(yesterday_metrics))
    
    # This week's summary
    if week_metrics and len(week_metrics) > len(today_metrics) + len(yesterday_metrics):
        output.append("\n📅 This Week")
        output.append(_format_period_summary(week_metrics))
    
    # All time summary
    if len(metrics_objects) > len(week_metrics):
        output.append("\n📅 All Time")
        output.append(_format_period_summary(metrics_objects))
    
    # Cost effectiveness analysis
    output.append("\n💰 Cost Effectiveness Analysis")
    output.append(_format_cost_analysis(metrics_objects))
    
    return "\n".join(output)


def _format_period_summary(metrics: List[BatchMetrics]) -> str:
    """Format metrics for a specific time period."""
    if not metrics:
        return "  No data"
    
    successful = [m for m in metrics if m.success]
    failed = [m for m in metrics if not m.success]
    with_fallback = [m for m in metrics if m.fallback_used]
    
    total_items = sum(m.items_count for m in successful)
    total_cost = sum(m.estimated_cost_usd or 0 for m in successful)
    total_tokens = sum(m.tokens_used or 0 for m in successful)
    total_duration = sum(m.duration_seconds for m in successful)
    
    # Group by batch type
    by_type = {}
    for m in successful:
        if m.batch_type not in by_type:
            by_type[m.batch_type] = {"calls": 0, "items": 0, "tokens": 0, "cost": 0.0}
        by_type[m.batch_type]["calls"] += 1
        by_type[m.batch_type]["items"] += m.items_count
        by_type[m.batch_type]["tokens"] += m.tokens_used or 0
        by_type[m.batch_type]["cost"] += m.estimated_cost_usd or 0.0
    
    lines = []
    lines.append(f"  📊 Calls: {len(successful)} successful, {len(failed)} failed, {len(with_fallback)} with fallback")
    lines.append(f"  🎯 Items: {total_items} processed in {total_duration:.1f}s")
    
    if total_tokens > 0:
        lines.append(f"  🔤 Tokens: {total_tokens:,} ({total_tokens/total_items:.0f} per item)")
    
    if total_cost > 0:
        lines.append(f"  💵 Cost: ~${total_cost:.4f}")
    
    if by_type:
        lines.append("  📈 By Type:")
        for batch_type, stats in sorted(by_type.items()):
            cost_str = f", ~${stats['cost']:.4f}" if stats['cost'] > 0 else ""
            tokens_str = f", {stats['tokens']} tokens" if stats['tokens'] > 0 else ""
            lines.append(f"    • {batch_type}: {stats['calls']} calls, {stats['items']} items{tokens_str}{cost_str}")
    
    return "\n".join(lines)


def _format_cost_analysis(metrics: List[BatchMetrics]) -> str:
    """Format cost effectiveness analysis."""
    successful = [m for m in metrics if m.success and not m.fallback_used]
    
    if not successful:
        return "  No successful batch calls to analyze"
    
    # Estimate savings vs individual calls
    total_items = sum(m.items_count for m in successful)
    total_batch_cost = sum(m.estimated_cost_usd or 0 for m in successful)
    
    # Rough estimate: individual calls would cost more due to overhead
    estimated_individual_cost = total_batch_cost * INDIVIDUAL_CALL_OVERHEAD_MULTIPLIER
    savings = estimated_individual_cost - total_batch_cost
    savings_percentage = (savings / estimated_individual_cost * PERCENTAGE_CONVERSION_FACTOR) if estimated_individual_cost > 0 else 0
    
    lines = []
    lines.append("  💡 Estimated vs Individual Calls:")
    lines.append(f"    • Batch Cost: ~${total_batch_cost:.4f}")
    lines.append(f"    • Individual Cost (est): ~${estimated_individual_cost:.4f}")
    lines.append(f"    • Savings: ~${savings:.4f} ({savings_percentage:.1f}%)")
    
    if savings_percentage > 20:
        lines.append("    • Status: ✅ Excellent savings!")
    elif savings_percentage > 0:
        lines.append("    • Status: ✅ Good savings")
    else:
        lines.append("    • Status: ⚠️  Review needed - may be more expensive")
    
    # API call reduction
    original_calls = total_items * ORIGINAL_CALLS_PER_ITEM  # Estimate original calls per item in old system
    batch_calls = len(successful)
    call_reduction = ((original_calls - batch_calls) / original_calls * PERCENTAGE_CONVERSION_FACTOR) if original_calls > 0 else 0
    
    lines.append("  📞 API Call Reduction:")
    lines.append(f"    • Original: ~{original_calls} calls")
    lines.append(f"    • Batch: {batch_calls} calls")
    lines.append(f"    • Reduction: {call_reduction:.1f}%")
    
    return "\n".join(lines)


def show_recent_metrics(limit: int = 10) -> str:
    """Show the most recent batch operations."""
    metrics_data = load_metrics_from_file()
    
    if not metrics_data:
        return "No recent batch metrics found."
    
    # Sort by timestamp, most recent first
    metrics_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent = metrics_data[:limit]
    
    lines = []
    lines.append(f"🕒 Last {len(recent)} Batch Operations")
    lines.append("=" * 40)
    
    for i, data in enumerate(recent, 1):
        timestamp = datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S')
        batch_type = data['batch_type']
        items = data['items_count']
        duration = data['duration_seconds']
        success = "✅" if data['success'] else "❌"
        fallback = " (fallback)" if data.get('fallback_used') else ""
        
        cost_str = ""
        if data.get('estimated_cost_usd'):
            cost_str = f", ~${data['estimated_cost_usd']:.4f}"
        
        tokens_str = ""
        if data.get('tokens_used'):
            tokens_str = f", {data['tokens_used']} tokens"
        
        lines.append(f"{i:2d}. {timestamp} {success} {batch_type}: {items} items in {duration:.2f}s{tokens_str}{cost_str}{fallback}")
    
    return "\n".join(lines)


def clear_metrics() -> None:
    """Clear the metrics log file."""
    log_dir = Path.home() / ".madspark"
    log_file = log_dir / "batch_metrics.jsonl"
    
    if log_file.exists():
        log_file.unlink()
        print("✅ Batch metrics cleared")
    else:
        print("ℹ️  No metrics file found")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="View batch API call metrics and cost analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m madspark.cli.batch_metrics                # Show summary
  python -m madspark.cli.batch_metrics --recent       # Show recent operations
  python -m madspark.cli.batch_metrics --recent 20    # Show last 20 operations
  python -m madspark.cli.batch_metrics --clear        # Clear metrics
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--recent', nargs='?', const=10, type=int, metavar='N',
                      help='Show N most recent batch operations (default: 10)')
    group.add_argument('--clear', action='store_true',
                      help='Clear all stored metrics')
    
    parser.add_argument('--file', metavar='PATH',
                       help='Custom metrics file path (default: ~/.madspark/batch_metrics.jsonl)')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_metrics()
    elif args.recent is not None:
        print(show_recent_metrics(args.recent))
    else:
        metrics_data = load_metrics_from_file(args.file)
        print(format_metrics_summary(metrics_data))


if __name__ == "__main__":
    main()