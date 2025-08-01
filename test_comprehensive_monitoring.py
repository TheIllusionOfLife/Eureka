"""Test comprehensive token monitoring with real API calls."""
from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.utils.batch_monitor import get_batch_monitor, reset_batch_monitor
import time

print('🚀 Comprehensive Token Monitoring Test')
print('=' * 50)

# Reset monitor for clean test
reset_batch_monitor()

print('\n📊 Test: 2 Candidates with Full Token Monitoring')
print('-' * 50)

start_time = time.time()
try:
    results = run_multistep_workflow_batch(
        theme='Efficient Public Transportation',
        constraints='Environmentally friendly and cost-effective',
        num_top_candidates=2,
        verbose=False
    )
    
    duration = time.time() - start_time
    print(f'\n✅ Completed in {duration:.2f} seconds')
    print(f'📋 Results: {len(results)} candidates processed')
    
    # Show detailed monitoring results
    print('\n📈 Detailed Monitoring Results')
    print('-' * 30)
    monitor = get_batch_monitor()
    summary = monitor.get_session_summary()
    
    print(f'Total API calls: {summary["total_calls"]}')
    print(f'Successful calls: {summary["successful_calls"]}/{summary["total_calls"]}')
    print(f'Items processed: {summary["total_items_processed"]}')
    print(f'Processing time: {summary["total_processing_time_seconds"]:.2f}s')
    print(f'Items per second: {summary.get("average_items_per_second", 0):.2f}')
    
    if summary.get('total_tokens_used', 0) > 0:
        tokens = summary["total_tokens_used"]
        items = summary["total_items_processed"]
        print(f'🔤 Total tokens: {tokens:,} ({tokens/items:.0f} per item)')
        
        if summary.get('total_estimated_cost_usd'):
            cost = summary["total_estimated_cost_usd"]
            print(f'💵 Estimated cost: ${cost:.4f} (${cost/items:.4f} per item)')
    
    # Detailed breakdown by batch type
    if summary.get('batch_type_breakdown'):
        print('\n📊 Batch Type Analysis:')
        total_batch_calls = 0
        total_individual_calls_estimate = 0
        
        for batch_type, stats in summary['batch_type_breakdown'].items():
            calls = stats["calls"]
            items = stats["items"]
            tokens = stats.get("tokens", 0)
            cost = stats.get("cost", 0)
            
            # Calculate efficiency
            items_per_call = items / calls if calls > 0 else 0
            tokens_per_item = tokens / items if items > 0 and tokens > 0 else 0
            
            total_batch_calls += calls
            total_individual_calls_estimate += items
            
            print(f'  {batch_type}:')
            print(f'    • {calls} batch calls vs {items} individual calls would be')
            print(f'    • {items_per_call:.1f} items per batch call')
            if tokens > 0:
                print(f'    • {tokens:,} tokens ({tokens_per_item:.0f} per item)')
            if cost > 0:
                print(f'    • ${cost:.4f} cost')
        
        # Overall API call reduction
        call_reduction = ((total_individual_calls_estimate - total_batch_calls) / total_individual_calls_estimate * 100) if total_individual_calls_estimate > 0 else 0
        print(f'\n📞 API Call Efficiency:')
        print(f'  • Batch calls: {total_batch_calls}')
        print(f'  • Individual calls would be: {total_individual_calls_estimate}')
        print(f'  • Reduction: {call_reduction:.1f}%')
    
    # Cost effectiveness analysis
    print('\n💰 Cost Effectiveness Analysis:')
    analysis = monitor.analyze_cost_effectiveness()
    
    if analysis.get('batch_effectiveness'):
        for batch_type, stats in analysis['batch_effectiveness'].items():
            savings_pct = stats.get('savings_percentage', 0)
            if savings_pct > 0:
                print(f'  ✅ {batch_type}: {savings_pct:.1f}% cost savings')
            elif savings_pct == 0:
                print(f'  🟡 {batch_type}: Cost neutral (no significant difference)')
            else:
                print(f'  ⚠️  {batch_type}: {abs(savings_pct):.1f}% more expensive')
                print(f'      This may be due to complex batch prompts requiring more tokens')
    
    if analysis.get('recommendations'):
        print('\n💡 Recommendations:')
        for rec in analysis['recommendations']:
            print(f'  • {rec}')
    
    # Show some sample results
    if results:
        print(f'\n🎯 Sample Results:')
        for i, candidate in enumerate(results[:2], 1):
            print(f'  Idea {i}: {candidate["idea"][:60]}...')
            print(f'    Score: {candidate["initial_score"]} → {candidate["improved_score"]} (Δ{candidate["score_delta"]})')
        
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()

print('\n🏁 Comprehensive monitoring test complete!')