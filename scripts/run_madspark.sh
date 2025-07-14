#!/bin/bash
# Run MadSpark with environment variables loaded

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file
# set -a enables automatic export of all variables
# set +a disables it after sourcing
set -a
source .env
set +a

# Run the CLI with all arguments passed through
python cli.py "$@"