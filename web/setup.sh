#!/bin/bash
# MadSpark Web Interface Setup Script
# This script helps first-time users set up the Docker-based web interface
# Note: For CLI setup (mad_spark/ms commands), use ~/Eureka/scripts/setup.sh

set -e  # Exit on error

# Configuration constants
readonly MODEL_DOWNLOAD_MAX_TIME=1800  # 30 minutes in seconds
readonly DISK_SPACE_MIN_GB=15          # Minimum disk space required
readonly RAM_MIN_GB=16                 # Recommended RAM
readonly REQUIRED_COMPOSE_MAJOR=2
readonly REQUIRED_COMPOSE_MINOR=24

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

echo "🚀 MadSpark Web Interface Setup"
echo "================================"
echo "Note: This sets up the web interface at http://localhost:3000"
echo "For CLI commands (mad_spark/ms), use ~/Eureka/scripts/setup.sh"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

# Check Docker Compose version (v2.24+ required for env_file.required syntax)
COMPOSE_VERSION=$(docker compose version --short 2>/dev/null | sed 's/^v//')
if [ -n "$COMPOSE_VERSION" ]; then
    # Extract major.minor (portable - no sort -V which doesn't exist on macOS)
    MAJOR=$(echo "$COMPOSE_VERSION" | cut -d. -f1)
    MINOR=$(echo "$COMPOSE_VERSION" | cut -d. -f2)
    # Validate extracted values are integers before comparison
    if [[ "$MAJOR" =~ ^[0-9]+$ && "$MINOR" =~ ^[0-9]+$ ]]; then
        if (( MAJOR > REQUIRED_COMPOSE_MAJOR || (MAJOR == REQUIRED_COMPOSE_MAJOR && MINOR >= REQUIRED_COMPOSE_MINOR) )); then
            : # Version is OK
        else
            echo "❌ Docker Compose version $COMPOSE_VERSION is too old."
            echo "   Version ${REQUIRED_COMPOSE_MAJOR}.${REQUIRED_COMPOSE_MINOR}+ is required."
            echo "   Please upgrade Docker Compose: https://docs.docker.com/compose/install/"
            exit 1
        fi
    else
        echo "⚠️  Could not parse Docker Compose version: $COMPOSE_VERSION"
        echo "   Continuing anyway..."
    fi
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Pre-flight checks for system resources
echo "🔍 Checking system resources..."
echo ""

# Check available disk space (need ~15GB for Ollama)
if command -v df &> /dev/null; then
    # Detect OS and use appropriate df command
    if [ "$(uname -s)" = "Darwin" ]; then
        # macOS: use -g for 1GB blocks, output is in column 4
        available_space=$(df -g . 2>/dev/null | tail -1 | awk '{print $4}')
    else
        # Linux: use -BG for GB blocks
        available_space=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
    fi

    # Only proceed with check if we got a valid number
    if [ -n "$available_space" ] && [ "$available_space" -eq "$available_space" ] 2>/dev/null; then
        if [ "$available_space" -lt "$DISK_SPACE_MIN_GB" ]; then
            echo "⚠️  WARNING: Low disk space detected (~${available_space}GB available)"
            echo "   Ollama requires ~${DISK_SPACE_MIN_GB}GB (~12GB models + overhead)"
            echo "   You may encounter issues during model download."
            echo ""
            read -p "Continue anyway? (y/N): " continue_anyway
            if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
                echo "Exiting. Please free up disk space and try again."
                exit 1
            fi
        else
            echo "✅ Sufficient disk space available (~${available_space}GB)"
        fi
    else
        echo "⚠️  Could not determine available disk space, continuing anyway..."
    fi
fi

# Check system RAM (recommend 16GB for Ollama)
if command -v free &> /dev/null; then
    # Linux
    total_ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram_gb" -lt "$RAM_MIN_GB" ]; then
        echo "⚠️  WARNING: Low system RAM detected (~${total_ram_gb}GB)"
        echo "   Ollama models require ~${RAM_MIN_GB}GB RAM for optimal performance"
        echo "   Your system may experience slowdowns or swapping to disk."
        echo ""
    else
        echo "✅ Sufficient RAM available (~${total_ram_gb}GB)"
    fi
elif command -v sysctl &> /dev/null; then
    # macOS
    total_ram_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo "0")
    total_ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))
    if [ "$total_ram_gb" -lt "$RAM_MIN_GB" ]; then
        echo "⚠️  WARNING: Low system RAM detected (~${total_ram_gb}GB)"
        echo "   Ollama models require ~${RAM_MIN_GB}GB RAM for optimal performance"
        echo "   Your system may experience slowdowns or swapping to disk."
        echo ""
    else
        echo "✅ Sufficient RAM available (~${total_ram_gb}GB)"
    fi
fi

echo ""

# Helper function to ensure .env file exists with proper permissions
ensure_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        echo "# MadSpark environment configuration" > "$ENV_FILE"
        echo "# Generated by web/setup.sh on $(date)" >> "$ENV_FILE"
        chmod 600 "$ENV_FILE"
    fi
}

# Helper function to set or update a key in .env file
set_env_var() {
    local key="$1"
    local value="$2"
    ensure_env_file
    # Remove existing key if present (avoids sed injection with special chars in value)
    grep -v "^${key}=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null || true
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
    # Append new value
    echo "${key}=${value}" >> "$ENV_FILE"
    chmod 600 "$ENV_FILE"
}

# Ask user which mode they want
echo "Choose your setup mode:"
echo "1) Ollama (Free, Local) - Recommended for most users"
echo "2) Gemini (Cloud, Requires API Key)"
echo "3) Mock (Testing only, no real AI)"
echo ""
read -p "Enter choice (1-3): " mode_choice

case $mode_choice in
    1)
        MODE="ollama"
        MADSPARK_MODE="api"
        echo ""
        echo "📦 Setting up with Ollama (free local inference)"

        # Check if native Ollama is installed on host
        if ! command -v ollama &> /dev/null; then
            echo ""
            echo "❌ Ollama is not installed on your system."
            echo ""
            echo "Please install Ollama first:"
            echo "   macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh"
            echo "   Or visit: https://ollama.com/download"
            echo ""
            echo "After installing, run this setup script again."
            exit 1
        fi

        # Check if Ollama is running
        if ! ollama list &> /dev/null; then
            echo ""
            echo "⚠️  Ollama is installed but not running."
            echo "   Starting Ollama..."
            # Try to start ollama serve in background
            if [ "$(uname -s)" = "Darwin" ]; then
                # macOS: ollama should auto-start, but let's try
                open -a Ollama 2>/dev/null || ollama serve &> /dev/null &
            else
                # Linux: start serve in background
                ollama serve &> /dev/null &
            fi
            sleep 3

            if ! ollama list &> /dev/null; then
                echo "❌ Failed to start Ollama. Please start it manually:"
                echo "   ollama serve"
                exit 1
            fi
        fi

        echo "✅ Ollama is installed and running"

        # Check if models are already present
        existing_model_count=$(ollama list 2>/dev/null | grep -c "gemma3" || echo "0")
        if [ "$existing_model_count" -ge 2 ]; then
            echo "✅ Ollama models already present, skipping download."
        else
            echo ""
            echo "📥 Downloading Ollama models..."
            echo "This will download ~12GB of models (gemma3:4b + gemma3:12b)"
            echo "Download time: 5-15 minutes depending on your internet speed."
            echo ""

            # Pull models
            echo "Pulling gemma3:4b (fast model, ~3.3GB)..."
            ollama pull gemma3:4b

            echo ""
            echo "Pulling gemma3:12b (balanced model, ~8.1GB)..."
            ollama pull gemma3:12b

            echo ""
            echo "✅ Both Ollama models downloaded successfully!"
        fi
        ;;
    2)
        MODE="gemini"
        MADSPARK_MODE="api"
        echo ""
        read -s -p "Enter your Gemini API key: " api_key
        echo ""  # New line after hidden input
        if [ -z "$api_key" ]; then
            echo "❌ API key cannot be empty"
            exit 1
        fi

        # Persist API key to .env file
        set_env_var "GOOGLE_API_KEY" "$api_key"
        echo "✅ API key saved to .env file"

        # Also export for current docker compose up
        export GOOGLE_API_KEY="$api_key"
        ;;
    3)
        MODE="mock"
        MADSPARK_MODE="mock"
        echo ""
        echo "🧪 Setting up in mock mode (testing only)"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Ensure .env file exists (docker compose needs it even if empty)
ensure_env_file

echo ""
echo "🐳 Starting Docker containers..."
echo ""

# Change to script directory for docker compose
cd "$SCRIPT_DIR"

# Start containers
if [ "$MODE" = "gemini" ]; then
    MADSPARK_MODE="$MADSPARK_MODE" GOOGLE_API_KEY="$GOOGLE_API_KEY" docker compose up -d
else
    MADSPARK_MODE="$MADSPARK_MODE" docker compose up -d
fi

echo ""
echo "✅ Containers started"
echo ""

echo "🎉 Setup complete!"
echo ""
echo "📍 Access the interface at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"

if [ "$MODE" = "ollama" ]; then
    echo "   Ollama API: http://localhost:11434"
    echo ""
    echo "💡 To verify Ollama models:"
    echo "   ollama list"
fi

echo ""
echo "🛠️  Useful commands:"
echo "   Stop services:    docker compose down"
echo "   View logs:        docker compose logs -f"
echo "   Restart services: docker compose restart"
echo ""
echo "📚 For more information, see README.md"
echo ""
