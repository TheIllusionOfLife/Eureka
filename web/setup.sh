#!/bin/bash
# MadSpark Web Interface Setup Script
# This script helps first-time users set up the web interface with Ollama

set -e  # Exit on error

echo "🚀 MadSpark Web Interface Setup"
echo "================================"
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
        read -p "Enter your Gemini API key: " api_key
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
    echo "⏳ Waiting for Ollama service to start..."
    sleep 30

    # Check if models are being downloaded
    for i in {1..90}; do  # Wait up to 15 minutes
        model_count=$(docker exec web-ollama-1 ollama list 2>/dev/null | grep -c "gemma3" || true)
        if [ "$model_count" -ge 2 ]; then
            echo ""
            echo "✅ Both Ollama models downloaded successfully!"
            break
        fi
        echo -n "."
        sleep 10
    done
    echo ""
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
    echo "   docker exec web-ollama-1 ollama list"
fi

echo ""
echo "🛠️  Useful commands:"
echo "   Stop services:    docker compose down"
echo "   View logs:        docker compose logs -f"
echo "   Restart services: docker compose restart"
echo ""
echo "📚 For more information, see README.md"
echo ""
