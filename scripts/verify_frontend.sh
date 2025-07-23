#!/bin/bash
# Verify frontend code quality and build
# Prevents CI failures due to TypeScript/React issues

set -e

echo "🔍 Verifying frontend code quality..."

FRONTEND_DIR="web/frontend"
if [[ ! -d "$FRONTEND_DIR" ]]; then
    echo "⚠️  Frontend directory not found: $FRONTEND_DIR"
    exit 0
fi

cd "$FRONTEND_DIR"

# Check if node_modules exists
if [[ ! -d "node_modules" ]]; then
    echo "📦 Installing dependencies..."
    npm ci
fi

echo "🔧 Running TypeScript compilation check..."
if ! npm run build > /dev/null 2>&1; then
    echo "❌ TypeScript compilation failed"
    echo "Run 'npm run build' in $FRONTEND_DIR to see detailed errors"
    exit 1
fi

echo "🧹 Running linting checks..."
if command -v npm run lint > /dev/null 2>&1; then
    if ! npm run lint > /dev/null 2>&1; then
        echo "❌ Linting failed"
        echo "Run 'npm run lint' in $FRONTEND_DIR to see detailed errors"
        exit 1
    fi
fi

echo "🧪 Running frontend tests..."
if ! npm test -- --watchAll=false --passWithNoTests > /dev/null 2>&1; then
    echo "❌ Frontend tests failed"
    echo "Run 'npm test' in $FRONTEND_DIR to see detailed errors"
    exit 1
fi

echo "✅ Frontend verification completed successfully"

# Return to original directory
cd - > /dev/null