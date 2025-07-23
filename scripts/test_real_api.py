#!/usr/bin/env python3
"""Test MadSpark with real Google API key."""
import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def check_api_key():
    """Check if a real API key is available."""
    api_key = os.environ.get('GOOGLE_API_KEY', '')
    
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment")
        print("\nTo run this test, set your API key:")
        print("export GOOGLE_API_KEY='your-actual-api-key'")
        return False
    
    if api_key.startswith('mock-') or api_key == 'your-api-key-here':
        print("❌ Mock API key detected. Please use a real API key.")
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    return True


def test_cli_with_real_api():
    """Test CLI with real API."""
    print("\n🧪 Testing CLI with real API...")
    
    test_cases = [
        {
            "topic": "sustainable urban farming",
            "context": "limited space and budget constraints",
            "description": "Basic idea generation"
        },
        {
            "topic": "How can AI help with climate change mitigation?",
            "context": "Focus on practical solutions for individuals",
            "description": "Question format"
        },
        {
            "topic": "quantum computing applications",
            "context": "healthcare and drug discovery",
            "description": "Technical topic"
        },
        {
            "topic": "みんなのためのAI教育",  # AI education for everyone
            "context": "小学生向けのプログラム",  # Programs for elementary students
            "description": "Japanese language test"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}/{len(test_cases)}: {test['description']}")
        print(f"   Topic: {test['topic']}")
        print(f"   Context: {test['context']}")
        
        start_time = time.time()
        
        # Run CLI command
        cmd = [
            sys.executable, "-m", "madspark.cli.cli",
            test['topic'], test['context']
        ]
        
        env = os.environ.copy()
        env['MADSPARK_MODE'] = 'direct'  # Force direct API mode
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=60  # 60 second timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                print(f"   ✅ Success! (took {elapsed:.1f}s)")
                # Check output quality
                output_lines = result.stdout.strip().split('\n')
                print(f"   Output lines: {len(output_lines)}")
                
                # Look for key indicators
                has_ideas = any('idea' in line.lower() for line in output_lines)
                has_scores = any('score' in line.lower() for line in output_lines)
                
                results.append({
                    'test': test['description'],
                    'status': 'success',
                    'time': elapsed,
                    'output_lines': len(output_lines),
                    'has_ideas': has_ideas,
                    'has_scores': has_scores
                })
            else:
                print(f"   ❌ Failed with exit code {result.returncode}")
                print(f"   Error: {result.stderr[:200]}...")
                results.append({
                    'test': test['description'],
                    'status': 'failed',
                    'error': result.stderr[:200]
                })
                
        except subprocess.TimeoutExpired:
            print(f"   ⏱️  Timeout after 60 seconds")
            results.append({
                'test': test['description'],
                'status': 'timeout'
            })
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            results.append({
                'test': test['description'],
                'status': 'error',
                'error': str(e)
            })
    
    return results


def test_api_with_real_key():
    """Test Web API with real API key."""
    print("\n🧪 Testing Web API with real API key...")
    
    # Start API server
    print("Starting API server...")
    env = os.environ.copy()
    env['MADSPARK_MODE'] = 'direct'
    
    server_process = subprocess.Popen(
        [sys.executable, "web/backend/main.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        import requests
        
        # Test health endpoint
        print("\n📍 Testing health endpoint...")
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
        
        # Test idea generation
        print("\n📍 Testing idea generation endpoint...")
        test_data = {
            "topic": "renewable energy solutions",
            "context": "residential applications with ROI focus",
            "num_top_candidates": 3,
            "multi_dimensional_eval": True
        }
        
        response = requests.post(
            "http://localhost:8000/api/generate-ideas",
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Generated {len(data.get('results', []))} ideas")
            print(f"   Processing time: {data.get('processing_time', 0):.1f}s")
            
            # Check quality of results
            if data.get('results'):
                result = data['results'][0]
                print(f"   First idea score: {result.get('initial_score', 0)}")
                print(f"   Improved score: {result.get('improved_score', 0)}")
        else:
            print(f"   ❌ Idea generation failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}...")
            
    finally:
        # Stop server
        print("\nStopping API server...")
        server_process.terminate()
        server_process.wait(timeout=5)


def test_performance_metrics():
    """Test performance with real API."""
    print("\n🧪 Testing performance metrics...")
    
    from madspark.core.async_coordinator import AsyncCoordinator
    from madspark.utils.temperature_control import TemperatureManager
    
    import asyncio
    
    async def run_performance_test():
        coordinator = AsyncCoordinator()
        temp_mgr = TemperatureManager()
        
        # Test different numbers of candidates
        test_configs = [
            {"candidates": 1, "description": "Single candidate"},
            {"candidates": 3, "description": "Default (3 candidates)"},
            {"candidates": 5, "description": "Extended (5 candidates)"}
        ]
        
        results = []
        
        for config in test_configs:
            print(f"\n📊 Testing with {config['candidates']} candidates...")
            
            start_time = time.time()
            
            try:
                result = await coordinator.run_workflow(
                    theme="AI-powered education",
                    constraints="personalized learning for K-12",
                    num_top_candidates=config['candidates'],
                    temperature_manager=temp_mgr,
                    multi_dimensional_eval=True
                )
                
                elapsed = time.time() - start_time
                
                print(f"   ✅ Completed in {elapsed:.1f}s")
                print(f"   Results: {len(result)} ideas processed")
                
                results.append({
                    'config': config['description'],
                    'time': elapsed,
                    'ideas': len(result),
                    'success': True
                })
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append({
                    'config': config['description'],
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run_performance_test())
    loop.close()
    
    return results


def save_test_results(all_results):
    """Save test results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_real_api_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {filename}")


def main():
    """Run all real API tests."""
    print("🚀 MadSpark Real API Testing Suite")
    print("=" * 50)
    
    if not check_api_key():
        return 1
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'api_key_length': len(os.environ.get('GOOGLE_API_KEY', '')),
        'tests': {}
    }
    
    # Run CLI tests
    cli_results = test_cli_with_real_api()
    all_results['tests']['cli'] = cli_results
    
    # Run API tests
    try:
        test_api_with_real_key()
        all_results['tests']['api'] = {'status': 'completed'}
    except Exception as e:
        all_results['tests']['api'] = {'status': 'failed', 'error': str(e)}
    
    # Run performance tests
    perf_results = test_performance_metrics()
    all_results['tests']['performance'] = perf_results
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    # CLI summary
    cli_success = sum(1 for r in cli_results if r.get('status') == 'success')
    print(f"\nCLI Tests: {cli_success}/{len(cli_results)} passed")
    
    # Performance summary
    if perf_results:
        avg_time = sum(r['time'] for r in perf_results if r.get('time', 0) > 0) / len(perf_results)
        print(f"Average performance: {avg_time:.1f}s per test")
    
    # Save results
    save_test_results(all_results)
    
    print("\n✅ Real API testing complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())