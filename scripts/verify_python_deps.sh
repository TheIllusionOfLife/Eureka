#!/bin/bash
# Verify Python dependencies can be installed without conflicts
# Prevents CI failures due to dependency resolution issues

set -e

echo "🔍 Verifying Python dependencies..."

# Check if requirements files exist
REQUIREMENTS_FILES=()
for req_file in "config/requirements.txt" "web/backend/requirements.txt" "requirements.txt"; do
    if [[ -f "$req_file" ]]; then
        REQUIREMENTS_FILES+=("$req_file")
    fi
done

if [[ ${#REQUIREMENTS_FILES[@]} -eq 0 ]]; then
    echo "⚠️  No requirements files found"
    exit 0
fi

# Create temporary virtual environment for verification
TEMP_VENV=$(mktemp -d)
python3 -m venv "$TEMP_VENV"
source "$TEMP_VENV/bin/activate"

# Upgrade pip to avoid installation issues
pip install --upgrade pip > /dev/null 2>&1

echo "📦 Testing dependency installation..."

# Test each requirements file
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    echo "  Checking $req_file..."
    
    # Try dry-run installation first
    if ! pip install --dry-run -r "$req_file" > /dev/null 2>&1; then
        echo "❌ Dependency conflict detected in $req_file"
        echo "Run 'pip install -r $req_file' locally to debug"
        deactivate
        rm -rf "$TEMP_VENV"
        exit 1
    fi
    
    # Test actual installation in clean environment
    if ! pip install -r "$req_file" > /dev/null 2>&1; then
        echo "❌ Installation failed for $req_file"
        echo "Dependencies may have conflicts or unavailable packages"
        deactivate
        rm -rf "$TEMP_VENV"
        exit 1
    fi
    
    echo "  ✅ $req_file verified"
    
    # Reset environment for next file
    pip uninstall -y -r "$req_file" > /dev/null 2>&1 || true
done

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo "✅ All Python dependencies verified successfully"