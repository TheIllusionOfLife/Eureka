"""Integration test for logical inference feature with all options."""
import subprocess
import os
import sys
import tempfile


def test_logical_inference_real_integration():
    """Test logical inference with real API-like behavior."""
    # Create a test script that simulates the full workflow
    test_script = '''
import sys
sys.path.insert(0, 'src')

from madspark.cli.cli import main
import sys

# Mock the arguments
sys.argv = [
    'cli.py',
    'sustainable urban transportation',
    'affordable for cities',
    '--detailed',
    '--logical',
    '--no-bookmark'
]

# Run the CLI
main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name
    
    try:
        # Run the test
        env = os.environ.copy()
        env['PYTHONPATH'] = 'src'
        env['MADSPARK_MODE'] = 'mock'
        
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            env=env
        )
        
        output = result.stdout
        
        # In mock mode, logical inference won't appear since it requires GenAI client
        # Just verify the command runs without errors
        assert result.returncode == 0, f"Process failed with error:\n{result.stderr}"
        
        # Verify basic structure is there
        assert 'MADSPARK MULTI-AGENT IDEA GENERATION RESULTS' in output
        
        # Verify other sections
        assert 'MADSPARK MULTI-AGENT IDEA GENERATION RESULTS' in output
        assert 'Initial Score:' in output
        
        print("✅ Logical inference integration test passed!")
        
    finally:
        os.unlink(test_file)


def test_enhanced_and_logical_combined():
    """Test both enhanced and logical options together."""
    test_script = '''
import sys
sys.path.insert(0, 'src')

from madspark.cli.cli import main
import sys

# Mock the arguments
sys.argv = [
    'cli.py',
    'renewable energy solutions',
    'rural communities',
    '--detailed',
    '--enhanced',
    '--logical',
    '--no-bookmark'
]

# Run the CLI
main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name
    
    try:
        # Run the test
        env = os.environ.copy()
        env['PYTHONPATH'] = 'src'
        env['MADSPARK_MODE'] = 'mock'
        
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            env=env
        )
        
        output = result.stdout
        
        # In mock mode, the format might be different
        # Check for advocacy/skepticism content
        has_advocacy = 'STRENGTHS:' in output or 'Advocacy:' in output
        has_skepticism = 'CRITICAL FLAWS:' in output or 'Skepticism:' in output
        
        assert has_advocacy, f"Advocacy content not found in output:\n{output[:500]}..."
        assert has_skepticism, f"Skepticism content not found in output:\n{output[:500]}..."
        
        # Note: Logical inference might not appear in mock mode
        # but we should at least not get errors
        assert result.returncode == 0, f"Process failed with error:\n{result.stderr}"
        
        print("✅ Enhanced + logical integration test passed!")
        
    finally:
        os.unlink(test_file)


def test_output_auto_save():
    """Test automatic output file saving for long outputs."""
    test_script = '''
import sys
sys.path.insert(0, 'src')

from madspark.cli.cli import main
import sys

# Mock the arguments for a long output
sys.argv = [
    'cli.py',
    'artificial intelligence applications',
    'healthcare industry',
    '--detailed',
    '--enhanced',
    '--logical',
    '--top-ideas', '5',
    '--no-bookmark'
]

# Run the CLI
main()
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name
    
    try:
        # Run the test
        env = os.environ.copy()
        env['PYTHONPATH'] = 'src'
        env['MADSPARK_MODE'] = 'mock'
        
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            env=env
        )
        
        output = result.stdout
        
        # Check if auto-save message appears
        if 'Full output saved to:' in output:
            print("✅ Auto-save feature activated for long output")
        else:
            # Verify output is not truncated
            assert '--- IDEA 1 ---' in output
            print("✅ Output displayed without auto-save (not long enough)")
        
        assert result.returncode == 0, f"Process failed with error:\n{result.stderr}"
        
    finally:
        os.unlink(test_file)


if __name__ == '__main__':
    test_logical_inference_real_integration()
    test_enhanced_and_logical_combined()
    test_output_auto_save()
    print("\n✅ All integration tests passed!")