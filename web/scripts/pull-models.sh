#!/bin/bash
# Ollama Model Auto-Pull Script
# This script pulls required Ollama models if they're not already present
# Safe from shell injection as it uses array format for commands

set -euo pipefail  # Exit on error, undefined variables, or pipe failures

# Model list (hardcoded to prevent injection)
# NOTE: Using non-quantized models for reliable JSON output
# Quantized (-it-qat) models fail to produce valid JSON for structured output
readonly MODEL_FAST="gemma3:4b"
readonly MODEL_BALANCED="gemma3:12b"

# Configuration constants
readonly DISK_SPACE_MIN_GB=15           # Minimum disk space required (~12GB models + overhead)
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
        # Detect OS and use appropriate df command (using uname -s for POSIX compatibility)
        if [[ "$(uname -s)" == "Darwin" ]]; then
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
    # Use exact literal string match with grep -F for security (no regex metacharacter interpretation)
    # Then filter with awk for exact first-column match to avoid partial matches
    ollama list 2>/dev/null | awk -v model="$model_name" '$1 == model {found=1; exit} END {exit !found}'
}

# Validate that a model is complete and functional
validate_model() {
    local model_name="$1"

    log "Validating ${model_name}..."

    # Fast validation: check model exists in ollama list (no inference, ~0.1s vs ~15s)
    # Full inference validation is too slow for startup (10-30s per model)
    # Use awk for exact first-column match (security: no regex metacharacter interpretation)
    if ollama list 2>/dev/null | awk -v model="$model_name" '$1 == model {found=1; exit} END {exit !found}'; then
        log "Model ${model_name} validated successfully (found in model list)"
        return 0
    else
        error "Model ${model_name} validation failed - not found in ollama list"
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

    # Wait for Ollama to be ready (with exponential backoff for faster startup on quick systems)
    log "Waiting for Ollama service to start..."
    local max_wait_seconds=60
    local elapsed=0
    local wait_time=0.5  # Start with 0.5 seconds
    local max_wait_time=4  # Cap at 4 seconds between attempts

    while [ "$elapsed" -lt "$max_wait_seconds" ]; do
        if ollama list >/dev/null 2>&1; then
            log "Ollama service ready after ${elapsed} seconds"
            break
        fi

        # Sleep with current wait time
        sleep "$wait_time"
        elapsed=$((elapsed + ${wait_time%.*}))  # Handle decimal for elapsed calculation
        elapsed=$((elapsed < 1 ? 1 : elapsed))  # Minimum 1 second increment

        # Exponential backoff: double wait time up to max
        wait_time=$(awk "BEGIN {t=$wait_time * 2; print (t > $max_wait_time ? $max_wait_time : t)}")
    done

    if [ "$elapsed" -ge "$max_wait_seconds" ]; then
        error "Ollama service failed to start after ${max_wait_seconds} seconds"
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
