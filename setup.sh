#!/bin/bash
# Simple setup script for MadSpark

echo "🚀 Setting up MadSpark Multi-Agent System..."

# Check Python version
python3 --version >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Install dependencies
echo "📚 Installing dependencies..."
./venv/bin/pip install -r config/requirements.txt

# Make run.py executable
chmod +x run.py

# Create .env file if it doesn't exist
if [ ! -f "src/madspark/.env" ]; then
    echo "🔧 Creating .env file..."
    cat > src/madspark/.env << EOF
# Google API Configuration
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
EOF
    echo "⚠️  Please edit src/madspark/.env and add your Google API key"
fi

echo "✅ Setup complete!"
echo ""
echo "Quick start:"
echo "  ./run.py coordinator                    # Run the coordinator"
echo "  ./run.py cli 'topic' 'context'         # Run CLI"
echo ""
echo "Or run without API key in mock mode."