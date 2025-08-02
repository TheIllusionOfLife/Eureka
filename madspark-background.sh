#!/bin/bash
# Background MadSpark execution script - bypasses terminal timeout

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Create output directory if it doesn't exist
mkdir -p output/structured/reports

# Create output filename with timestamp
OUTPUT_FILE="output/structured/reports/madspark_output_$(date +%Y%m%d_%H%M%S).txt"

echo "🚀 Starting MadSpark in background..."
echo "📄 Output will be saved to: $OUTPUT_FILE"
echo "📊 Use 'tail -f $OUTPUT_FILE' to monitor progress"
echo "🎯 Using structured output format for clean results"

# Run in background with nohup
nohup bash -c 'source venv/bin/activate && export PYTHONPATH="${PYTHONPATH}:$(pwd)/src" && python -m madspark.cli.cli "$@"' -- "$@" > "$OUTPUT_FILE" 2>&1 &

# Get the process ID
PID=$!
echo "🔄 Process ID: $PID"
echo ""
echo "To check if it's still running: ps -p $PID"
echo "To view output: tail -f $OUTPUT_FILE"