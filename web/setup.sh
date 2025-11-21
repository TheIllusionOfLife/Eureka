#!/bin/bash
# MadSpark Web Interface Setup Script
# This script helps first-time users set up the Docker-based web interface
# Note: For CLI setup (mad_spark/ms commands), use ~/Eureka/scripts/setup.sh

set -e  # Exit on error

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

echo "✅ Docker and Docker Compose are installed"
echo ""

# Pre-flight checks for system resources
echo "🔍 Checking system resources..."
echo ""

# Check available disk space (need ~15GB for Ollama)
if command -v df &> /dev/null; then
    available_space=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$available_space" -lt 15 ]; then
        echo "⚠️  WARNING: Low disk space detected (~${available_space}GB available)"
        echo "   Ollama requires ~15GB (13GB models + 2GB Docker overhead)"
        echo "   You may encounter issues during model download."
        echo ""
        read -p "Continue anyway? (y/N): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
            echo "Exiting. Please free up disk space and try again."
            exit 1
        fi
    else
        echo "✅ Sufficient disk space available (~${available_space}GB)"
    fi
fi

# Check system RAM (recommend 16GB for Ollama)
if command -v free &> /dev/null; then
    # Linux
    total_ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram_gb" -lt 16 ]; then
        echo "⚠️  WARNING: Low system RAM detected (~${total_ram_gb}GB)"
        echo "   Ollama models require ~16GB RAM for optimal performance"
        echo "   Your system may experience slowdowns or swapping to disk."
        echo ""
    else
        echo "✅ Sufficient RAM available (~${total_ram_gb}GB)"
    fi
elif command -v sysctl &> /dev/null; then
    # macOS
    total_ram_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo "0")
    total_ram_gb=$((total_ram_bytes / 1024 / 1024 / 1024))
    if [ "$total_ram_gb" -lt 16 ]; then
        echo "⚠️  WARNING: Low system RAM detected (~${total_ram_gb}GB)"
        echo "   Ollama models require ~16GB RAM for optimal performance"
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
        echo "This will download ~13GB of models on first startup."
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
    echo "📥 Downloading Ollama models..."
    echo "You can monitor progress in another terminal with:"
    echo "   docker compose logs -f ollama"
    echo ""
    echo "Waiting for models to download (this may take 5-15 minutes)..."
    echo ""

    # Wait for Ollama to be healthy and models to be downloaded
    echo -n "⏳ Waiting for Ollama service to start"
    # Poll for healthy status instead of fixed sleep
    for i in {1..60}; do  # Wait up to 5 minutes for startup
        if docker compose ps ollama 2>/dev/null | grep -q "healthy"; then
            echo " Done."
            break
        fi
        echo -n "."
        sleep 5
    done

    # Check if models are being downloaded
    for i in {1..180}; do  # Wait up to 30 minutes (13GB download + slow connections)
        model_count=$(docker compose exec ollama ollama list 2>/dev/null | grep -c "gemma3" || true)
        if [ "$model_count" -ge 2 ]; then
            echo ""
            echo "✅ Both Ollama models downloaded successfully!"
            break
        fi
        echo -n "."
        sleep 10
    done
    echo ""

    # Verify models were actually downloaded
    final_model_count=$(docker compose exec ollama ollama list 2>/dev/null | grep -c "gemma3" || true)
    if [ "$final_model_count" -lt 2 ]; then
        echo "❌ ERROR: Ollama models failed to download after 30 minutes"
        echo ""
        echo "This could be due to:"
        echo "  - Slow internet connection"
        echo "  - Insufficient disk space (~13GB required)"
        echo "  - Docker container issues"
        echo ""
        echo "Check the logs with:"
        echo "  docker compose logs -f ollama"
        echo ""
        echo "Or manually pull models:"
        echo "  docker compose exec ollama ollama pull gemma3:4b-it-qat"
        echo "  docker compose exec ollama ollama pull gemma3:12b-it-qat"
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
