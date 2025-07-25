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