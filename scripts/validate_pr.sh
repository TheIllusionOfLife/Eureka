#!/bin/bash
# Comprehensive PR validation script
# Run this before creating a PR to catch issues early

set -euo pipefail

echo "🔍 MadSpark PR Validation"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to check a condition
check() {
    local name=$1
    local command=$2
    
    echo -n "Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Function to run a test with output
run_test() {
    local name=$1
    local command=$2
    
    echo -e "\n📋 Running: $name"
    echo "Command: $command"
    if eval "$command"; then
        echo -e "${GREEN}✓ Passed${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Environment checks
echo -e "\n🌍 Environment Checks"
check "Python installed" "python3 --version"
check "Docker installed" "docker --version"
check "Git installed" "git --version"

# 2. Mock mode validation
echo -e "\n🎭 Mock Mode Validation"
export MADSPARK_MODE=mock
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"

check "CLI works in mock mode" "timeout 60 python3 -m madspark.cli.cli 'test' 'test'"
check "No API key required" "[[ -z \${GOOGLE_API_KEY:-} ]] || [[ \${GOOGLE_API_KEY} == mock* ]]"

# 3. Syntax checks
echo -e "\n🔧 Syntax Checks"
check "No old docker-compose syntax" "! grep -r 'docker-compose' --include='*.md' --include='*.yml' --include='*.sh' . | grep -v 'docker-compose.yml' | grep -v '.git'"
check "Python syntax valid" "python3 -m py_compile src/madspark/**/*.py"

# 4. Test execution
echo -e "\n🧪 Test Execution"
run_test "Core agent tests" "pytest tests/test_agents.py -v --tb=short"
run_test "Coordinator tests" "pytest tests/test_coordinator.py -v --tb=short"

# 5. Security checks
echo -e "\n🔒 Security Checks"
if command -v bandit > /dev/null 2>&1; then
    check "No high severity issues" "bandit -r src/ -ll -f json | jq -e '.results | length == 0'"
else
    echo -e "${YELLOW}⚠ Bandit not installed, skipping security check${NC}"
fi

# 6. Code quality
echo -e "\n📊 Code Quality"
if command -v ruff > /dev/null 2>&1; then
    check "Ruff linting passes" "ruff check src/ tests/"
else
    echo -e "${YELLOW}⚠ Ruff not installed, skipping linting${NC}"
fi

# 7. Docker validation
echo -e "\n🐳 Docker Validation"
check "Docker compose config valid" "docker compose -f web/docker-compose.yml config"

# 8. PR size check
echo -e "\n📏 PR Size Analysis"
if [ -d .git ]; then
    FILES_CHANGED=$(git diff --name-only main...HEAD 2>/dev/null | wc -l || echo "0")
    LINES_CHANGED=$(git diff --stat main...HEAD 2>/dev/null | tail -1 | awk '{print $4 + $6}' || echo "0")
    
    echo "Files changed: $FILES_CHANGED"
    echo "Lines changed: $LINES_CHANGED"
    
    if [ "$FILES_CHANGED" -gt 20 ]; then
        echo -e "${RED}⚠️  Warning: PR has $FILES_CHANGED files (recommended: < 20)${NC}"
        FAILED=$((FAILED + 1))
    fi
    
    if [ "$LINES_CHANGED" -gt 500 ]; then
        echo -e "${RED}⚠️  Warning: PR has $LINES_CHANGED line changes (recommended: < 500)${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${YELLOW}Not in a git repository, skipping size check${NC}"
fi

# Summary
echo -e "\n📊 Validation Summary"
echo "===================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Your PR is ready.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED checks failed. Please fix before creating PR.${NC}"
    echo -e "\nRun individual failed commands to see detailed errors."
    exit 1
fi