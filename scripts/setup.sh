#!/bin/bash
# Enhanced setup script for MadSpark with interactive API key configuration

# Color codes for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to create mock mode .env file
create_mock_env() {
    cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="YOUR_API_KEY_HERE"
GOOGLE_GENAI_MODEL="gemini-3-flash-preview"
# Running in mock mode - no API key configured
MADSPARK_MODE="mock"
EOF
}

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
PIP_INSTALL_SUCCESS=true
./venv/bin/pip install -r config/requirements.txt || PIP_INSTALL_SUCCESS=false

if [ "$PIP_INSTALL_SUCCESS" = false ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Make run.py executable
chmod +x run.py

# Verify critical web backend packages are installed
# Only run verification if initial install succeeded (skip if network was down)
echo -e "${BLUE}🔍 Verifying web backend dependencies...${NC}"

# Define packages and their import names (pip-name=import-name)
# Note: Some pip package names differ from their Python import names:
#   - python-multipart → imports as 'multipart' (not 'python_multipart')
declare -A WEB_DEPS=(
    [fastapi]=fastapi
    [uvicorn]=uvicorn
    [slowapi]=slowapi
    [python-multipart]=multipart  # pip name differs from import name
)
MISSING_DEPS=()

for pkg in "${!WEB_DEPS[@]}"; do
    import_name=${WEB_DEPS[$pkg]}
    if ! ./venv/bin/python -c "import $import_name" 2>/dev/null; then
        MISSING_DEPS+=("$pkg")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing packages: ${MISSING_DEPS[*]}${NC}"
    echo -e "${YELLOW}Retrying installation...${NC}"
    ./venv/bin/pip install "${MISSING_DEPS[@]}" || { echo -e "${RED}❌ Failed to install web backend deps${NC}"; exit 1; }
fi
echo -e "${GREEN}✅ All dependencies verified${NC}"

# Handle .env file and API key configuration
ENV_FILE=".env"
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
    
    # Default to option 2 if no input or non-interactive
    if [ -t 0 ]; then
        read -r -p "Choose option (1 or 2, default=2): " choice
        choice=${choice:-2}  # Default to 2 if empty
    else
        # Non-interactive mode, default to mock
        echo "Non-interactive mode detected, defaulting to mock mode..."
        choice=2
    fi

    case $choice in
        1)
            echo ""
            read -r -s -p "Enter your Google API key: " api_key
            echo ""  # Add newline after hidden input
            # Validate API key format
            if [[ $api_key == AIza* ]] && [ ${#api_key} -gt 30 ]; then
                # Create .env with the provided key
                cat > "$ENV_FILE" << EOF
# Google API Configuration
GOOGLE_API_KEY="$api_key"
GOOGLE_GENAI_MODEL="gemini-3-flash-preview"
EOF
                echo -e "${GREEN}✅ API key configured successfully!${NC}"
                API_KEY_CONFIGURED=true
            else
                echo -e "${RED}❌ Invalid API key format. Keys should start with 'AIza'.${NC}"
                echo -e "${YELLOW}⚠️  Setting up for mock mode instead...${NC}"
                # Create .env for mock mode
                create_mock_env
            fi
            ;;
        *)
            echo -e "${BLUE}🤖 Setting up for mock mode...${NC}"
            # Create .env for mock mode
            create_mock_env
            ;;
    esac
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

# Find project root by looking for README.md or run.py
current = Path(__file__).resolve()
while current != current.parent:
    if (current / "README.md").exists() or (current / "run.py").exists():
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

# Also make config script executable if it exists
if [ -f "src/madspark/bin/mad_spark_config" ]; then
    chmod +x src/madspark/bin/mad_spark_config
fi

# Try to install to system locations
INSTALLED=false
INSTALL_LOCATIONS=(
    "/usr/local/bin"
    "$HOME/.local/bin"
    "$HOME/bin"
)

for loc in "${INSTALL_LOCATIONS[@]}"; do
    if [ -d "$loc" ] && [ -w "$loc" ]; then
        # Calculate relative path from target to source
        SCRIPT_PATH="$(pwd)/src/madspark/bin/mad_spark"
        RELATIVE_PATH=$(python3 -c "import os.path; print(os.path.relpath('$SCRIPT_PATH', '$loc'))")
        
        ln -sf "$RELATIVE_PATH" "$loc/mad_spark" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Installed mad_spark to $loc${NC}"
            INSTALLED=true
            
            # Also create madspark (no underscore) and ms aliases
            ln -sf "$RELATIVE_PATH" "$loc/madspark" 2>/dev/null
            ln -sf "$RELATIVE_PATH" "$loc/ms" 2>/dev/null
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

echo -e "  ${BLUE}mad_spark${NC} 'sustainable energy' 'low cost solutions'      # Topic + Context"

echo ""
echo -e "${PURPLE}Aliases available:${NC} ms"
echo ""

if [ "$API_KEY_CONFIGURED" = false ]; then
    echo -e "${YELLOW}💡 To switch to real AI later, run:${NC} ${BLUE}mad_spark config${NC}"
fi
