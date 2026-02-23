#!/bin/bash
# Run MadSpark using the robust Python runner

# Get the directory of the script
DIR="$( cd -- "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Assuming the script is in scripts/, the root is one level up
ROOT_DIR="$DIR/.."

# Path to run.py
RUN_SCRIPT="$ROOT_DIR/run.py"

# Check if run.py exists
if [ ! -f "$RUN_SCRIPT" ]; then
    echo "Error: run.py not found at $RUN_SCRIPT" >&2
    exit 1
fi

# Delegate to run.py, passing all arguments
# run.py handles venv activation and safe .env loading via python-dotenv
exec python3 "$RUN_SCRIPT" "$@"
