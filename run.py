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

# Import mode detection utilities
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
                print("💡 To use real API: Add your key to src/madspark/.env")
                print("")
        else:
            if not os.getenv("SUPPRESS_MODE_MESSAGE"):
                print("✅ API key found. Running with Google Gemini API...")
                print("")
except ImportError:
    # If imports fail, continue without mode detection
    pass

# Check if running in virtual environment
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

# Now we can run the command
if len(sys.argv) < 2:
    print("MadSpark Multi-Agent System")
    print("\nUsage:")
    print("  ./run.py coordinator                           # Run the coordinator")
    print("  ./run.py cli <topic> <context>                # Run CLI with topic and context")
    print("  ./run.py test                                 # Run tests")
    print("\nExamples:")
    print("  ./run.py coordinator")
    print("  ./run.py cli 'Sustainable transport' 'Low-cost'")
    sys.exit(0)

command = sys.argv[1]

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
else:
    print(f"Unknown command: {command}")
    print("Run './run.py' for usage")
    sys.exit(1)