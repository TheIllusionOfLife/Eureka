"""Test the new mad_spark config command."""
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_config_command_in_run_py():
    """Test that run.py recognizes the config command."""
    run_py = Path(__file__).parent.parent / "run.py"
    
    # Read run.py content
    with open(run_py, 'r') as f:
        content = f.read()
    
    # Check that config is in the list of valid commands
    assert "'config'" in content
    assert "mad_spark config" in content
    
def test_config_script_exists():
    """Test that the config script exists and is executable."""
    config_script = Path(__file__).parent.parent / "src" / "madspark" / "bin" / "mad_spark_config"
    
    assert config_script.exists()
    assert os.access(config_script, os.X_OK)  # Check if executable

def test_config_script_functions():
    """Test config script utility functions."""
    # Import the config script as a module
    config_script = Path(__file__).parent.parent / "src" / "madspark" / "bin" / "mad_spark_config"
    
    # Read and exec the script to test its functions
    with open(config_script, 'r') as f:
        script_content = f.read()
    
    # Create a namespace to execute the script
    namespace = {}
    exec(script_content, namespace)
    
    # Test validate_api_key
    validate_api_key = namespace['validate_api_key']
    assert validate_api_key("AIzaSyD-test-key-with-more-than-30-chars") is True
    assert not validate_api_key("YOUR_API_KEY_HERE")
    assert not validate_api_key("short")
    assert not validate_api_key("NotStartingWithAIza-but-long-enough-key")
    
    # Test read_env_file with mock data
    test_env_content = '''
# Google API Configuration
GOOGLE_API_KEY="AIzaSyD-test-key"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
MADSPARK_MODE="mock"
'''
    
    read_env_file = namespace['read_env_file']
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=test_env_content)):
            config = read_env_file(Path("test.env"))
            assert config["GOOGLE_API_KEY"] == "AIzaSyD-test-key"
            assert config["GOOGLE_GENAI_MODEL"] == "gemini-2.5-flash"
            assert config["MADSPARK_MODE"] == "mock"

def test_setup_default_behavior():
    """Test that setup.sh defaults to mock mode on empty input."""
    setup_sh = Path(__file__).parent.parent / "scripts" / "setup.sh"
    
    # Read the script
    with open(setup_sh, 'r') as f:
        content = f.read()
    
    # Check for default behavior
    assert "default=2" in content
    assert "${choice:-2}" in content
    assert "Non-interactive mode detected" in content

def test_readme_mentions_config():
    """Test that README mentions the config command."""
    readme = Path(__file__).parent.parent / "README.md"
    
    with open(readme, 'r') as f:
        content = f.read()
    
    assert "mad_spark config" in content
    assert "Configure your API key" in content