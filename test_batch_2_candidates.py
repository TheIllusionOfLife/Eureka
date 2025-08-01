"""Test batch coordinator with 2 candidates to see batch efficiency."""
from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.utils.batch_monitor import get_batch_monitor, reset_batch_monitor
import time

print('🚀 Testing Batch Coordinator with 2 Candidates')
print('=' * 50)

# Reset monitor for clean test
reset_batch_monitor()

print('\n📊 Test 2: Two Candidates')
print('-' * 30)

start_time = time.time()
try:
    results = run_multistep_workflow_batch(
        theme='Smart City Infrastructure',
        constraints='Budget under $1M, deployable in major cities',
        num_top_candidates=2,
        verbose=False  # Less verbose for cleaner output
    )
    
    duration = time.time() - start_time
    print(f'\n✅ Completed in {duration:.2f} seconds')
    print(f'📋 Results: {len(results)} candidates processed')
    
    if results:
        for i, candidate in enumerate(results, 1):
            print(f'🎯 Idea {i}: {candidate["idea"][:50]}...')
            print(f'   Score: {candidate["initial_score"]} → {candidate["improved_score"]} (Δ{candidate["score_delta"]})')
        
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()

# Show monitoring results
print('\n📈 Monitoring Results')
print('-' * 30)
monitor = get_batch_monitor()
summary = monitor.get_session_summary()

if summary.get('total_calls', 0) > 0:
    print(f'Total API calls: {summary["total_calls"]}')
    print(f'Successful calls: {summary["successful_calls"]}/{summary["total_calls"]}')
    print(f'Items processed: {summary["total_items_processed"]}')
    print(f'Processing time: {summary["total_processing_time_seconds"]:.2f}s')
    print(f'Items per second: {summary.get("average_items_per_second", 0):.2f}')
    
    if summary.get('total_estimated_cost_usd'):
        cost = summary["total_estimated_cost_usd"]
        print(f'Estimated cost: ${cost:.4f}')
        
        # Conservative estimate of individual call cost
        estimated_individual_cost = cost * 1.5
        savings = estimated_individual_cost - cost
        print(f'Est. individual cost: ${estimated_individual_cost:.4f}')
        print(f'Est. savings: ${savings:.4f} ({savings/estimated_individual_cost*100:.1f}%)')
    
    if summary.get('batch_type_breakdown'):
        print('\nBatch efficiency by type:')
        for batch_type, stats in summary['batch_type_breakdown'].items():
            items_per_call = stats["items"] / stats["calls"] if stats["calls"] > 0 else 0
            print(f'  {batch_type}: {stats["calls"]} calls for {stats["items"]} items ({items_per_call:.1f} items/call)')

# Cost analysis
analysis = monitor.analyze_cost_effectiveness()
if analysis.get('batch_effectiveness'):
    print('\n💰 Detailed Cost Analysis:')
    for batch_type, stats in analysis['batch_effectiveness'].items():
        if stats['savings_percentage'] > 0:
            print(f'  ✅ {batch_type}: {stats["savings_percentage"]:.1f}% savings')
        else:
            print(f'  ⚠️  {batch_type}: {abs(stats["savings_percentage"]):.1f}% more expensive')

print('\n🏁 Test complete!')