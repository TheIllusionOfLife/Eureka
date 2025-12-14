#!/bin/bash
# Ollama Model Auto-Pull Script
# This script pulls required Ollama models if they're not already present
# Safe from shell injection as it uses array format for commands

set -euo pipefail  # Exit on error, undefined variables, or pipe failures

# Model list (hardcoded to prevent injection)
readonly MODEL_FAST="gemma3:4b-it-qat"
readonly MODEL_BALANCED="gemma3:12b-it-qat"

# Configuration constants
readonly DISK_SPACE_MIN_GB=15           # Minimum disk space required (13GB models + 2GB overhead)
readonly MAX_RETRIES=2                   # Number of retry attempts for failed downloads
readonly RETRY_DELAY=10                  # Initial retry delay in seconds

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

# Check available disk space
check_disk_space() {
    log "Checking available disk space..."

    if command -v df &> /dev/null; then
        local available_space
        # Detect OS and use appropriate df command
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS: use -g for 1GB blocks
            available_space=$(df -g . 2>/dev/null | tail -1 | awk '{print $4}')
        else
            # Linux: use -BG for GB blocks
            available_space=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
        fi

        # Validate that available_space is a number
        if ! [[ "$available_space" =~ ^[0-9]+$ ]]; then
            log "Warning: Could not parse disk space, continuing anyway"
            return 0
        fi

        if [ "$available_space" -lt "$DISK_SPACE_MIN_GB" ]; then
            error "Insufficient disk space: ${available_space}GB available, ${DISK_SPACE_MIN_GB}GB required"
            error "Please free up disk space and try again"
            return 1
        else
            log "Sufficient disk space available: ${available_space}GB"
            return 0
        fi
    else
        log "Warning: Cannot check disk space (df command not available)"
        return 0  # Continue anyway, will fail later if truly insufficient
    fi
}

# Check if a model is already downloaded
model_exists() {
    local model_name="$1"
    ollama list | grep -q "^${model_name}" && return 0 || return 1
}

# Validate that a model is complete and functional
validate_model() {
    local model_name="$1"

    log "Validating ${model_name}..."

    # Verify the model can generate a response (check exit code)
    if echo "Test" | ollama run "$model_name" > /dev/null 2>&1; then
        log "Model ${model_name} validated successfully"
        return 0
    else
        error "Model ${model_name} validation failed - may be corrupted or incomplete"
        return 1
    fi
}

# Remove a model (cleanup partial/corrupted downloads)
remove_model() {
    local model_name="$1"

    log "Removing potentially corrupted model ${model_name}..."
    if ollama rm "$model_name" 2>/dev/null; then
        log "Successfully removed ${model_name}"
        return 0
    else
        log "No model to remove or removal failed (this is OK)"
        return 0  # Don't fail the script if removal fails
    fi
}

# Pull a model with error handling, validation, and retry logic
pull_model() {
    local model_name="$1"
    local attempt=0

    # Check if model already exists and is valid
    if model_exists "$model_name"; then
        log "Model ${model_name} already exists, validating..."
        if validate_model "$model_name"; then
            log "Model ${model_name} is valid, skipping download"
            return 0
        else
            log "Existing model ${model_name} is corrupted, will re-download"
            remove_model "$model_name"
        fi
    fi

    # Attempt download with retries
    while [ $attempt -le $MAX_RETRIES ]; do
        if [ $attempt -gt 0 ]; then
            local delay=$((RETRY_DELAY * attempt))
            log "Retry attempt $attempt of $MAX_RETRIES after ${delay}s delay..."
            sleep $delay
        fi

        log "Pulling ${model_name} (attempt $((attempt + 1)) of $((MAX_RETRIES + 1)))..."

        # Attempt to pull the model
        if ollama pull "$model_name"; then
            log "Successfully downloaded ${model_name}"

            # Validate the downloaded model
            if validate_model "$model_name"; then
                log "Successfully pulled and validated ${model_name}"
                return 0
            else
                error "Model ${model_name} downloaded but validation failed"
                remove_model "$model_name"  # Clean up corrupted download
            fi
        else
            error "Failed to pull ${model_name} (attempt $((attempt + 1)))"
        fi

        attempt=$((attempt + 1))
    done

    # All retries exhausted
    error "Failed to pull ${model_name} after $((MAX_RETRIES + 1)) attempts"
    error "Possible causes:"
    error "  - Network connectivity issues"
    error "  - Insufficient disk space (need ~15GB free)"
    error "  - Disk space exhausted during download"
    error "  - Ollama service issues"
    error ""
    error "Troubleshooting steps:"
    error "  1. Check network: curl -I https://ollama.com"
    error "  2. Check disk space: df -h"
    error "  3. Check Ollama logs: docker compose logs ollama"
    error "  4. Try manual pull: docker compose exec ollama ollama pull ${model_name}"
    return 1
}

# Main execution
main() {
    log "Starting Ollama model auto-pull"

    # Pre-flight check: verify sufficient disk space
    if ! check_disk_space; then
        error "Pre-flight check failed: insufficient disk space"
        exit 1
    fi

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

    # Pull required models with enhanced error handling
    # At least one model must be available for the system to work
    local fast_ok=0
    local balanced_ok=0

    if pull_model "$MODEL_FAST"; then
        fast_ok=1
        log "Fast tier model ready"
    else
        log "Warning: Fast tier model not available"
    fi

    if pull_model "$MODEL_BALANCED"; then
        balanced_ok=1
        log "Balanced tier model ready"
    else
        log "Warning: Balanced tier model not available"
    fi

    # Continue if at least one model is available
    if [ $fast_ok -eq 0 ] && [ $balanced_ok -eq 0 ]; then
        error "No models available - cannot start Ollama service"
        error "See troubleshooting steps above for guidance"
        kill $ollama_pid 2>/dev/null || true
        exit 1
    fi

    if [ $fast_ok -eq 1 ] && [ $balanced_ok -eq 1 ]; then
        log "All models downloaded and validated successfully"
    else
        log "Warning: Some models unavailable, but service can still run"
    fi
    log "Waiting for Ollama service (PID: ${ollama_pid})..."

    # Keep Ollama running (wait for the background process)
    wait $ollama_pid
}

# Execute main function
main "$@"
