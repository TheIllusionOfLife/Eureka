#!/usr/bin/env bash
# PR validation script - runs checks before creating a PR

set -e

echo "🔍 Running PR validation checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to check command result
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 passed${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi
}

# 1. Check for uncommitted changes
echo "📝 Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    git status --short
fi

# 2. Run linting
echo "🧹 Running code linting..."
if command -v ruff &> /dev/null; then
    ruff check src/ tests/ web/backend/ --fix
    check_result "Linting"
else
    echo -e "${YELLOW}⚠️  Ruff not installed, skipping linting${NC}"
fi

# 3. Run type checking
echo "🔤 Running type checking..."
if command -v mypy &> /dev/null; then
    mypy src/ --ignore-missing-imports
    check_result "Type checking"
else
    echo -e "${YELLOW}⚠️  Mypy not installed, skipping type checking${NC}"
fi

# 4. Run tests
echo "🧪 Running tests..."
export PYTHONPATH="src"
export MADSPARK_MODE="mock"
pytest tests/ -v --tb=short
check_result "Tests"

# 5. Check PR size
echo "📊 Checking PR size..."
FILES_CHANGED=$(git diff --name-only main... | wc -l || echo "0")
LINES_CHANGED=$(git diff --numstat main... | awk '{added+=$1; deleted+=$2} END {print added+deleted+0}')

echo "Files changed: $FILES_CHANGED"
echo "Lines changed: $LINES_CHANGED"

if [ "$FILES_CHANGED" -gt 20 ]; then
    echo -e "${RED}❌ PR has too many files ($FILES_CHANGED > 20)${NC}"
    FAILURES=$((FAILURES + 1))
fi

if [ "$LINES_CHANGED" -gt 500 ]; then
    echo -e "${RED}❌ PR is too large ($LINES_CHANGED > 500 lines)${NC}"
    FAILURES=$((FAILURES + 1))
elif [ "$LINES_CHANGED" -gt 300 ]; then
    echo -e "${YELLOW}⚠️  Warning: PR is getting large ($LINES_CHANGED > 300 lines)${NC}"
fi

# 6. Check for security issues
echo "🔒 Running security checks..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -ll
    check_result "Security scan"
else
    echo -e "${YELLOW}⚠️  Bandit not installed, skipping security scan${NC}"
fi

# Summary
echo
echo "======================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All PR validation checks passed!${NC}"
    echo "Your PR is ready to be created."
    exit 0
else
    echo -e "${RED}❌ $FAILURES check(s) failed${NC}"
    echo "Please fix the issues before creating a PR."
    exit 1
fi