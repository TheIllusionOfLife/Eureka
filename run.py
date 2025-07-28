#!/usr/bin/env python3
"""
Simple runner script for MadSpark that handles environment setup automatically.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Check if running in virtual environment FIRST
if not hasattr(sys, 'prefix') or sys.prefix == sys.base_prefix:
    venv_python = project_root / "venv" / "bin" / "python"
    if venv_python.exists():
        # Re-run this script with venv Python
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    else:
        print("⚠️  Virtual environment not found. Please run:")
        print("   python -m venv venv")
        print("   ./venv/bin/pip install -r config/requirements.txt")
        sys.exit(1)

# Now in venv, do mode detection
try:
    from madspark.agents.genai_client import get_mode, is_api_key_configured, load_env_file
    
    # Load environment variables from .env
    load_env_file()
    
    # Auto-detect mode if not explicitly set
    if not os.getenv("MADSPARK_MODE"):
        mode = get_mode()
        if mode == "mock":
            os.environ["MADSPARK_MODE"] = "mock"
            if not os.getenv("SUPPRESS_MODE_MESSAGE"):
                print("🤖 No API key found. Running in mock mode...")
                print("💡 To use real API: Run 'mad_spark config'")
                print("")
        else:
            if not os.getenv("SUPPRESS_MODE_MESSAGE"):
                print("✅ API key found. Running with Google Gemini API...")
                print("")
except (ImportError, ModuleNotFoundError, Exception) as e:
    # If imports fail, continue without mode detection
    # This handles more error types than just ImportError
    if "MADSPARK_DEBUG" in os.environ:
        print(f"Mode detection error: {e}")

# Now we can run the command
if len(sys.argv) < 2:
    print("MadSpark Multi-Agent System")
    print("\nUsage:")
    print("  mad_spark                              # Show this help")
    print("  mad_spark coordinator                  # Run the coordinator")
    print("  mad_spark 'topic' ['context']         # Generate ideas (simplified!)")
    print("  mad_spark test                         # Run tests")
    print("  mad_spark config                       # Configure API key")
    print("\nExamples:")
    print("  mad_spark 'consciousness' 'what is it?'")
    print("  mad_spark 'sustainable cities'")
    print("  mad_spark coordinator")
    print("\nAliases: mad_spark, madspark, ms")
    sys.exit(0)

# Handle simplified syntax - if first arg is not a command, treat as topic
command = sys.argv[1]
if command not in ['coordinator', 'cli', 'test', 'config', '--help', '-h', '--version']:
    # This is a topic, not a command - convert to CLI format
    topic = command
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    
    # Convert to CLI command format
    sys.argv = [sys.argv[0], 'cli', topic, context]
    command = 'cli'

if command == "coordinator":
    try:
        import runpy
        runpy.run_module('madspark.core.coordinator', run_name='__main__')
    except ImportError as e:
        print(f"❌ Failed to import coordinator module: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Coordinator execution failed: {e}")
        sys.exit(1)
elif command == "cli":
    if len(sys.argv) < 4:
        print("Error: CLI requires topic and context arguments")
        print("Usage: ./run.py cli <topic> <context>")
        sys.exit(1)
    try:
        import runpy
        sys.argv = ['cli', sys.argv[2], sys.argv[3]]
        runpy.run_module('madspark.cli.cli', run_name='__main__')
    except ImportError as e:
        print(f"❌ Failed to import CLI module: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI execution failed: {e}")
        sys.exit(1)
elif command == "test":
    subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"])
elif command == "config":
    # Run the configuration tool
    config_script = project_root / "src" / "madspark" / "bin" / "mad_spark_config"
    if config_script.exists():
        subprocess.run([sys.executable, str(config_script)])
    else:
        print("❌ Configuration tool not found")
        sys.exit(1)
else:
    print(f"Unknown command: {command}")
    print("Run './run.py' for usage")
    sys.exit(1)