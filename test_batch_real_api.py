"""Test batch coordinator with real API calls."""
from madspark.core.coordinator_batch import run_multistep_workflow_batch
from madspark.utils.batch_monitor import get_batch_monitor, reset_batch_monitor
import time

print('🚀 Testing Batch Coordinator with Real API Calls')
print('=' * 50)

# Reset monitor for clean test
reset_batch_monitor()

# Test with 1 candidate first (lower cost)
print('\n📊 Test 1: Single Candidate')
print('-' * 30)

start_time = time.time()
try:
    results = run_multistep_workflow_batch(
        theme='Sustainable Urban Technology',
        constraints='Must be implementable within 2 years and cost-effective',
        num_top_candidates=1,
        verbose=True
    )
    
    duration = time.time() - start_time
    print(f'\n✅ Completed in {duration:.2f} seconds')
    print(f'📋 Results: {len(results)} candidates processed')
    
    if results:
        candidate = results[0]
        print(f'🎯 Top idea: {candidate["idea"][:60]}...')
        print(f'📈 Score improvement: {candidate["initial_score"]} → {candidate["improved_score"]} (Δ{candidate["score_delta"]})')
        
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
    
    if summary.get('total_estimated_cost_usd'):
        print(f'Estimated cost: ${summary["total_estimated_cost_usd"]:.4f}')
    
    if summary.get('batch_type_breakdown'):
        print('\nBatch breakdown:')
        for batch_type, stats in summary['batch_type_breakdown'].items():
            print(f'  {batch_type}: {stats["calls"]} calls, {stats["items"]} items')

# Cost analysis
analysis = monitor.analyze_cost_effectiveness()
if analysis.get('recommendations'):
    print('\n💰 Cost Analysis:')
    for rec in analysis['recommendations']:
        print(f'  • {rec}')

print('\n🏁 Test complete!')