#!/bin/bash
# Ollama Model Auto-Pull Script
# This script pulls required Ollama models if they're not already present
# Safe from shell injection as it uses array format for commands

set -euo pipefail  # Exit on error, undefined variables, or pipe failures

# Model list (hardcoded to prevent injection)
readonly MODEL_FAST="gemma3:4b-it-qat"
readonly MODEL_BALANCED="gemma3:12b-it-qat"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Check if a model is already downloaded
model_exists() {
    local model_name="$1"
    ollama list | grep -q "^${model_name}" && return 0 || return 1
}

# Pull a model with error handling
pull_model() {
    local model_name="$1"

    if model_exists "$model_name"; then
        log "Model ${model_name} already exists, skipping download"
        return 0
    fi

    log "Pulling ${model_name}..."
    if ollama pull "$model_name"; then
        log "Successfully pulled ${model_name}"
        return 0
    else
        error "Failed to pull ${model_name}"
        error "Check network connection, disk space (~13GB required), and Ollama logs"
        return 1
    fi
}

# Main execution
main() {
    log "Starting Ollama model auto-pull"

    # Start Ollama service in background
    log "Starting Ollama service..."
    ollama serve &
    local ollama_pid=$!

    # Wait for Ollama to be ready (with timeout)
    log "Waiting for Ollama service to start..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if ollama list >/dev/null 2>&1; then
            log "Ollama service ready after $((attempt * 2)) seconds"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        error "Ollama service failed to start after 60 seconds"
        kill $ollama_pid 2>/dev/null || true
        exit 1
    fi

    # Pull required models
    local failed=0

    if ! pull_model "$MODEL_FAST"; then
        failed=1
    fi

    if ! pull_model "$MODEL_BALANCED"; then
        failed=1
    fi

    if [ $failed -eq 1 ]; then
        error "One or more models failed to download"
        kill $ollama_pid 2>/dev/null || true
        exit 1
    fi

    log "All models downloaded successfully"
    log "Waiting for Ollama service (PID: ${ollama_pid})..."

    # Keep Ollama running (wait for the background process)
    wait $ollama_pid
}

# Execute main function
main "$@"
