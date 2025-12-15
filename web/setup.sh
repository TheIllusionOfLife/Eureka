#!/bin/bash
# MadSpark Web Interface Setup Script
# This script helps first-time users set up the Docker-based web interface
# Note: For CLI setup (mad_spark/ms commands), use ~/Eureka/scripts/setup.sh

set -e  # Exit on error

# Configuration constants
readonly HEALTH_CHECK_MAX_ATTEMPTS=60  # 5 minutes (60 attempts × 5s)
readonly HEALTH_CHECK_INTERVAL=5       # seconds between health checks
readonly MODEL_DOWNLOAD_MAX_TIME=1800  # 30 minutes in seconds
readonly DISK_SPACE_MIN_GB=15          # Minimum disk space required
readonly RAM_MIN_GB=16                 # Recommended RAM

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
REQUIRED_VERSION="2.24.0"
if [ -n "$COMPOSE_VERSION" ]; then
    # Compare versions (works for semantic versioning)
    if printf '%s\n%s' "$REQUIRED_VERSION" "$COMPOSE_VERSION" | sort -V -C 2>/dev/null; then
        : # Version is OK
    else
        echo "⚠️  WARNING: Docker Compose version $COMPOSE_VERSION detected."
        echo "   Version $REQUIRED_VERSION or higher is recommended."
        echo "   Some features may not work correctly with older versions."
        echo ""
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
    if [[ "$(uname -s)" == "Darwin" ]]; then
        # macOS: use -g for 1GB blocks, output is in column 4
        available_space=$(df -g . 2>/dev/null | tail -1 | awk '{print $4}')
    else
        # Linux: use -BG for GB blocks
        available_space=$(df -BG . 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/G//')
    fi

    # Only proceed with check if we got a valid number
    if [[ "$available_space" =~ ^[0-9]+$ ]] && [ "$available_space" -lt "$DISK_SPACE_MIN_GB" ]; then
        echo "⚠️  WARNING: Low disk space detected (~${available_space}GB available)"
        echo "   Ollama requires ~${DISK_SPACE_MIN_GB}GB (~12GB models + overhead)"
        echo "   You may encounter issues during model download."
        echo ""
        read -p "Continue anyway? (y/N): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
            echo "Exiting. Please free up disk space and try again."
            exit 1
        fi
    elif [[ "$available_space" =~ ^[0-9]+$ ]]; then
        echo "✅ Sufficient disk space available (~${available_space}GB)"
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
        echo "This will download ~12GB of models on first startup."
        echo "Download time: 5-15 minutes depending on your internet speed."
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
        export GOOGLE_API_KEY="$api_key"
        echo "✅ API key set"
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

echo ""
echo "🐳 Starting Docker containers..."
echo ""

# Start containers
if [ "$MODE" = "gemini" ]; then
    MADSPARK_MODE="$MADSPARK_MODE" GOOGLE_API_KEY="$GOOGLE_API_KEY" docker compose up -d
else
    MADSPARK_MODE="$MADSPARK_MODE" docker compose up -d
fi

echo ""
echo "✅ Containers started"
echo ""

# If Ollama mode, monitor model download
if [ "$MODE" = "ollama" ]; then
    # Wait for Ollama to be healthy first
    echo -n "⏳ Waiting for Ollama service to start"
    for i in $(seq 1 $HEALTH_CHECK_MAX_ATTEMPTS); do
        if docker compose ps ollama 2>/dev/null | grep -q "healthy"; then
            echo " Done."
            break
        fi
        echo -n "."
        sleep $HEALTH_CHECK_INTERVAL
    done

    # Check if models are already present
    existing_model_count=$(docker compose exec ollama ollama list 2>/dev/null | grep -c "gemma3" || true)
    if [ "$existing_model_count" -ge 2 ]; then
        echo "✅ Ollama models already present, skipping download."
    else
        echo ""
        echo "📥 Downloading Ollama models..."
        echo "You can monitor progress in another terminal with:"
        echo "   docker compose logs -f ollama"
        echo ""
        echo "Waiting for models to download (this may take 5-15 minutes)..."
        echo ""
        echo "⏳ Waiting for model downloads (up to 30 minutes for ~12GB of models)"
        echo "   Using progressive backoff: 10s → 15s → 20s intervals"

        elapsed_time=0
        check_interval=10

        while [ $elapsed_time -lt $MODEL_DOWNLOAD_MAX_TIME ]; do
            model_count=$(docker compose exec ollama ollama list 2>/dev/null | grep -c "gemma3" || true)
            if [ "$model_count" -ge 2 ]; then
                echo ""
                echo "✅ Both Ollama models downloaded successfully!"
                break
            fi

            echo -n "."
            sleep $check_interval
            elapsed_time=$((elapsed_time + check_interval))

            # Progressive backoff: increase interval as time passes
            if [ $elapsed_time -ge 600 ] && [ $check_interval -eq 10 ]; then
                check_interval=15  # After 10 min, increase to 15s
            elif [ $elapsed_time -ge 1200 ] && [ $check_interval -eq 15 ]; then
                check_interval=20  # After 20 min, increase to 20s
            fi
        done
        echo ""
    fi

    # Verify models were actually downloaded
    final_model_count=$(docker compose exec ollama ollama list 2>/dev/null | grep -c "gemma3" || true)
    if [ "$final_model_count" -lt 2 ]; then
        echo "❌ ERROR: Ollama models failed to download after 30 minutes"
        echo ""
        echo "This could be due to:"
        echo "  - Slow internet connection"
        echo "  - Insufficient disk space (~12GB required)"
        echo "  - Docker container issues"
        echo ""
        echo "Check the logs with:"
        echo "  docker compose logs -f ollama"
        echo ""
        echo "Or manually pull models:"
        echo "  docker compose exec ollama ollama pull gemma3:4b"
        echo "  docker compose exec ollama ollama pull gemma3:12b"
        echo ""
        exit 1
    fi
fi

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
    echo "   docker compose exec ollama ollama list"
fi

echo ""
echo "🛠️  Useful commands:"
echo "   Stop services:    docker compose down"
echo "   View logs:        docker compose logs -f"
echo "   Restart services: docker compose restart"
echo ""
echo "📚 For more information, see README.md"
echo ""
