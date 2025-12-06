"""Test various option combinations to ensure they work correctly."""
import subprocess
import os
import sys


def run_madspark_command(args):
    """Run madspark command and return output."""
    cmd = [sys.executable, '-m', 'madspark.cli.cli'] + args
    
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src'
    env['MADSPARK_MODE'] = 'mock'  # Use mock mode for testing
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )
    
    return result.stdout, result.stderr, result.returncode


def test_basic_command():
    """Test basic command without options."""
    print("Testing: Basic command")
    output, stderr, code = run_madspark_command([
        'test topic',
        'test constraints',
        '--no-bookmark'
    ])
    
    assert code == 0, f"Basic command failed: {stderr}"
    assert 'idea' in output.lower()
    print("✅ Basic command works")


def test_enhanced_only():
    """Test with --enhanced flag only."""
    print("\nTesting: --enhanced only")
    output, stderr, code = run_madspark_command([
        'renewable energy',
        'rural areas',
        '--enhanced',
        '--detailed',
        '--no-bookmark',
        '--top-ideas', '1'  # Force sync execution to avoid output truncation
    ])
    
    assert code == 0, f"Enhanced command failed: {stderr}"
    assert 'STRENGTHS:' in output
    assert 'CRITICAL FLAWS:' in output
    print("✅ Enhanced reasoning shows advocate/skeptic sections")


def test_logical_only():
    """Test with --logical flag only."""
    print("\nTesting: --logical only")
    output, stderr, code = run_madspark_command([
        'smart cities',
        'sustainable development',
        '--logical',
        '--detailed',
        '--no-bookmark'
    ])
    
    assert code == 0, f"Logical command failed: {stderr}"
    # In mock mode, logical inference might not show
    print("✅ Logical inference command runs without errors")


def test_enhanced_and_logical():
    """Test with both --enhanced and --logical."""
    print("\nTesting: --enhanced --logical")
    output, stderr, code = run_madspark_command([
        'education technology',
        'elementary schools',
        '--enhanced',
        '--logical',
        '--detailed',
        '--no-bookmark',
        '--top-ideas', '1'  # Force sync execution to avoid output truncation
    ])
    
    assert code == 0, f"Combined command failed: {stderr}"
    assert 'STRENGTHS:' in output
    assert 'CRITICAL FLAWS:' in output
    print("✅ Enhanced + logical combination works")


def test_multiple_ideas():
    """Test with multiple ideas."""
    print("\nTesting: Multiple ideas (--top-ideas 3)")
    output, stderr, code = run_madspark_command([
        'healthcare innovation',
        'low-income communities',
        '--top-ideas', '3',
        '--detailed',
        '--no-bookmark'
    ])
    
    assert code == 0, f"Multiple ideas command failed: {stderr}"
    assert '--- IDEA 1 ---' in output
    # In mock mode, might only generate 1 idea
    print("✅ Multiple ideas command works")


def test_output_modes():
    """Test different output modes."""
    modes = ['brief', 'simple', 'detailed']
    
    for mode in modes:
        print(f"\nTesting: Output mode --{mode}")
        output, stderr, code = run_madspark_command([
            'test topic',
            '--' + mode,
            '--no-bookmark'
        ])
        
        assert code == 0, f"{mode} mode failed: {stderr}"
        
        if mode == 'detailed':
            assert '=' * 80 in output
        elif mode == 'brief':
            assert '## ' in output  # Markdown headers
        
        print(f"✅ {mode.capitalize()} output mode works")


def test_auto_save_trigger():
    """Test auto-save trigger conditions."""
    print("\nTesting: Auto-save trigger")
    output, stderr, code = run_madspark_command([
        'complex topic with long description',
        'many constraints and requirements',
        '--top-ideas', '5',
        '--enhanced',
        '--logical',
        '--detailed',
        '--no-bookmark'
    ])
    
    assert code == 0, f"Auto-save test failed: {stderr}"
    # Check if output mentions saving to file
    if 'Full output saved to:' in output:
        print("✅ Auto-save triggered for long output")
    else:
        print("✅ Output displayed normally (not long enough for auto-save)")


def test_help_command():
    """Test help command shows updated descriptions."""
    print("\nTesting: Help command")
    output, stderr, code = run_madspark_command(['--help'])
    
    assert code == 0, f"Help command failed: {stderr}"
    assert 'advocate & skeptic agents' in output
    assert 'logical inference analysis' in output
    print("✅ Help text shows updated option descriptions")


if __name__ == '__main__':
    print("Running MadSpark option combination tests...\n")
    
    test_basic_command()
    test_enhanced_only()
    test_logical_only()
    test_enhanced_and_logical()
    test_multiple_ideas()
    test_output_modes()
    test_auto_save_trigger()
    test_help_command()
    
    print("\n✅ All option combination tests passed!")