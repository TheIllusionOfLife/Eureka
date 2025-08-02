#!/bin/bash
# Direct MadSpark execution script - bypasses any shell timeout wrappers

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Execute the CLI directly with all arguments passed through
exec python -m madspark.cli.cli "$@"