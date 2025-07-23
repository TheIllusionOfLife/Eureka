#!/bin/bash
# Verify npm package.json and package-lock.json consistency
# Prevents CI failures due to dependency mismatches

set -e

echo "🔍 Verifying npm dependencies consistency..."

# Check if we're in a directory with npm files
FRONTEND_DIR="web/frontend"
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "⚠️  Frontend directory not found: $FRONTEND_DIR"
    exit 0
fi

cd "$FRONTEND_DIR"

# Check if required files exist
if [[ ! -f "package.json" ]]; then
    echo "⚠️  package.json not found in $FRONTEND_DIR"
    exit 0
fi

if [[ ! -f "package-lock.json" ]]; then
    echo "⚠️  package-lock.json not found - run 'npm install' first"
    exit 1
fi

echo "📦 Testing npm dependency consistency..."

# Check lock file integrity
if ! npm ci --dry-run > /dev/null 2>&1; then
    echo "❌ package-lock.json is inconsistent with package.json"
    echo ""
    echo "🔧 To fix this issue:"
    echo "   1. Delete package-lock.json and node_modules/"
    echo "   2. Run 'npm install' to regenerate lock file"
    echo "   3. Commit the updated package-lock.json"
    echo ""
    echo "Or run 'npm install' if you intended to update dependencies"
    exit 1
fi

# Verify audit for security issues
echo "🔐 Checking for security vulnerabilities..."
if ! npm audit --audit-level=moderate > /dev/null 2>&1; then
    echo "⚠️  Security vulnerabilities detected"
    echo "Run 'npm audit' to see details and 'npm audit fix' to attempt fixes"
    # Don't fail on audit issues, just warn
fi

# Check for outdated dependencies (informational)
if command -v npm-check-updates > /dev/null 2>&1; then
    echo "📊 Checking for outdated dependencies..."
    ncu -u --dry-run | head -10 || true
fi

echo "✅ npm dependencies verified successfully"

# Return to original directory
cd - > /dev/null