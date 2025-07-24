#!/bin/bash
# Enhanced setup script for MadSpark with interactive API key configuration

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚀 Setting up MadSpark Multi-Agent System...${NC}"
echo ""

# Check Python version
python3 --version >/dev/null 2>&1 || { echo -e "${RED}❌ Python 3 is required but not installed.${NC}"; exit 1; }

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Install dependencies
echo -e "${BLUE}📚 Installing dependencies...${NC}"
./venv/bin/pip install -r config/requirements.txt >/dev/null 2>&1 || ./venv/bin/pip install -r config/requirements.txt

# Make run.py executable
chmod +x run.py

# Handle .env file and API key configuration
ENV_FILE="src/madspark/.env"
API_KEY_CONFIGURED=false

if [ -f "$ENV_FILE" ]; then
    # Check if API key is already configured
    if grep -q 'GOOGLE_API_KEY="AIza' "$ENV_FILE" 2>/dev/null; then
        API_KEY_CONFIGURED=true
        echo -e "${GREEN}✅ API key already configured${NC}"
    fi
fi

# Interactive API key setup
if [ "$API_KEY_CONFIGURED" = false ]; then
    echo ""
    echo -e "${YELLOW}🔑 API Key Configuration${NC}"
    echo "To use the Google Gemini API, you'll need an API key."
    echo "Get your key from: https://makersuite.google.com/app/apikey"
    echo ""
    echo -e "${BLUE}Would you like to:${NC}"
    echo "  1) Enter your API key now"
    echo "  2) Use mock mode (no API key required)"
    echo ""
    read -p "Choose option (1 or 2): " choice

    case $choice in
        1)
            echo ""
            read -p "Enter your Google API key: " api_key
            # Validate API key format
            if [[ $api_key == AIza* ]] && [ ${#api_key} -gt 30 ]; then
                # Create .env with the provided key
                cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="$api_key"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
EOF
                echo -e "${GREEN}✅ API key configured successfully!${NC}"
                API_KEY_CONFIGURED=true
            else
                echo -e "${RED}❌ Invalid API key format. Keys should start with 'AIza'.${NC}"
                echo -e "${YELLOW}⚠️  Setting up for mock mode instead...${NC}"
                # Create .env for mock mode
                cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
# Running in mock mode - no API key configured
MADSPARK_MODE="mock"
EOF
            fi
            ;;
        *)
            echo -e "${BLUE}🤖 Setting up for mock mode...${NC}"
            # Create .env for mock mode
            cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
# Running in mock mode - no API key configured
MADSPARK_MODE="mock"
EOF
            ;;
    esac
else
    # .env exists but no valid API key
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
GOOGLE_GENAI_MODEL="gemini-2.5-flash"
EOF
    fi
fi

# Create mad_spark command
echo ""
echo -e "${BLUE}🔨 Installing mad_spark command...${NC}"

# Create bin directory if it doesn't exist
mkdir -p src/madspark/bin

# Create mad_spark script
cat > src/madspark/bin/mad_spark << 'EOF'
#!/usr/bin/env python3
"""
mad_spark - Simplified command interface for MadSpark Multi-Agent System
"""
import os
import sys
from pathlib import Path

# Find project root by looking for setup.sh
current = Path(__file__).resolve()
while current != current.parent:
    if (current / "setup.sh").exists():
        project_root = current
        break
    current = current.parent
else:
    print("❌ Could not find MadSpark project root")
    sys.exit(1)

# Add src to Python path
sys.path.insert(0, str(project_root / "src"))

# Run the main script
run_py = project_root / "run.py"
if run_py.exists():
    os.execv(sys.executable, [sys.executable, str(run_py)] + sys.argv[1:])
else:
    print(f"❌ Could not find {run_py}")
    sys.exit(1)
EOF

# Make it executable
chmod +x src/madspark/bin/mad_spark

# Try to install to system locations
INSTALLED=false
INSTALL_LOCATIONS=(
    "/usr/local/bin"
    "$HOME/.local/bin"
    "$HOME/bin"
)

for loc in "${INSTALL_LOCATIONS[@]}"; do
    if [ -d "$loc" ] && [ -w "$loc" ]; then
        ln -sf "$(pwd)/src/madspark/bin/mad_spark" "$loc/mad_spark" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Installed mad_spark to $loc${NC}"
            INSTALLED=true
            
            # Also create madspark (no underscore) and ms aliases
            ln -sf "$(pwd)/src/madspark/bin/mad_spark" "$loc/madspark" 2>/dev/null
            ln -sf "$(pwd)/src/madspark/bin/mad_spark" "$loc/ms" 2>/dev/null
            break
        fi
    fi
done

if [ "$INSTALLED" = false ]; then
    echo -e "${YELLOW}⚠️  Could not install mad_spark to system PATH${NC}"
    echo "You can still use: ./src/madspark/bin/mad_spark"
fi

# Success message
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${PURPLE}Quick start:${NC}"

if [ "$API_KEY_CONFIGURED" = true ]; then
    echo -e "  ${BLUE}mad_spark${NC} 'consciousness' 'what is it?'    # Generate ideas with AI"
else
    echo -e "  ${BLUE}mad_spark${NC} 'consciousness' 'what is it?'    # Generate ideas (mock mode)"
fi

echo -e "  ${BLUE}mad_spark coordinator${NC}                      # Run the coordinator"
echo -e "  ${BLUE}mad_spark test${NC}                            # Run tests"
echo ""
echo -e "${PURPLE}Aliases available:${NC} mad_spark, madspark, ms"
echo ""

if [ "$API_KEY_CONFIGURED" = false ]; then
    echo -e "${YELLOW}💡 To use real AI later, add your API key to: src/madspark/.env${NC}"
fi