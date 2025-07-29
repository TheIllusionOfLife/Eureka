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

# Handle early help/version commands BEFORE mode detection
if len(sys.argv) >= 2 and sys.argv[1] in ['--help', '-h', '--version']:
    # Suppress mode message for help/version commands
    os.environ["SUPPRESS_MODE_MESSAGE"] = "1"
    
    # For help, pass to CLI module
    if sys.argv[1] in ['--help', '-h']:
        try:
            import runpy
            sys.argv = ['cli'] + sys.argv[1:]
            runpy.run_module('madspark.cli.cli', run_name='__main__')
            sys.exit(0)
        except Exception as e:
            print(f"❌ Failed to show help: {e}")
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
            if not os.getenv("SUPPRESS_MODE_MESSAGE"):
                print("🤖 No API key found. Running in mock mode...")
                print("💡 To use real API: Run 'mad_spark config'")
                print("")
        else:
            # Don't set MADSPARK_MODE - let get_mode() handle it dynamically
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

# Handle help commands (already handled above, but kept for other flows)
if command in ['--help', '-h']:
    try:
        import runpy
        # Pass all original arguments to CLI help
        sys.argv = ['cli'] + sys.argv[1:]
        runpy.run_module('madspark.cli.cli', run_name='__main__')
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Failed to import CLI module: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI execution failed: {e}")
        sys.exit(1)

# List of reserved commands (not topics)
reserved_commands = ['coordinator', 'cli', 'test', 'config', '--help', '-h', '--version']
if command not in reserved_commands:
    # This is a topic, not a command - convert to CLI format
    topic = command
    
    # Find where the topic arguments end and flags begin
    # Look for the first argument that starts with '--'
    flag_start_idx = 2  # Default: no flags
    for i in range(2, len(sys.argv)):
        if sys.argv[i].startswith('--'):
            flag_start_idx = i
            break
    
    # Extract context (if present before flags)
    context = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else ""
    
    # Collect any remaining flags
    flags = sys.argv[flag_start_idx:] if flag_start_idx < len(sys.argv) else []
    
    # Convert to CLI command format, preserving flags
    # Only include context if it's not empty
    cli_args = [sys.argv[0], 'cli', topic]
    if context:  # Only add context if it's not empty
        cli_args.append(context)
    cli_args.extend(flags)
    sys.argv = cli_args
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
    # Check for at least a topic (context is optional)
    if len(sys.argv) < 3:
        print("Error: CLI requires at least a topic argument")
        print("Usage: ./run.py cli <topic> [context]")
        sys.exit(1)
    try:
        import runpy
        # Pass all arguments after 'cli' to the CLI module
        # Filter out empty strings to avoid argparse issues
        cli_args = [arg for arg in sys.argv[2:] if arg]
        sys.argv = ['cli'] + cli_args
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