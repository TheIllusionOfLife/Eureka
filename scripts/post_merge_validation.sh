#!/usr/bin/env bash
# Post-merge validation script

# Don't use set -e to allow all checks to run and report

echo "🔍 Running post-merge validation..."

# Set up environment
export PYTHONPATH="${PYTHONPATH}${PYTHONPATH:+:}src"
export MADSPARK_MODE="mock"

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

# 1. Check Python imports
echo "📦 Checking Python imports..."
python -c "
try:
    from madspark.core.coordinator import run_multistep_workflow
    from madspark.agents.idea_generator import generate_ideas
    from madspark.agents.critic import evaluate_ideas
    from madspark.agents.advocate import advocate_idea
    from madspark.agents.skeptic import criticize_idea
    print('All imports successful')
except ImportError as e:
    print(f'Import error: {e}')
    exit(1)
"
check_result "Import validation"

# 2. Test CLI in mock mode
echo "🖥️  Testing CLI functionality..."
python -m madspark.cli.cli "test topic" "test context" > /dev/null
check_result "CLI mock mode test"

# 3. Run core unit tests
echo "🧪 Running core unit tests..."
pytest tests/test_agents.py tests/test_coordinators.py -v --tb=short
check_result "Core unit tests"

# 4. Check for deprecated syntax
echo "🔍 Checking for deprecated syntax..."
python tests/test_docker_compose_syntax.py
check_result "Deprecated syntax check"

# 5. Verify configuration files
echo "📄 Verifying configuration files..."
for file in "config/requirements.txt" "config/requirements-dev.txt" ".pre-commit-config.yaml"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo -e "  ${RED}✗ $file missing${NC}"
        FAILURES=$((FAILURES + 1))
    fi
done

# 6. Check Docker setup (if Docker is available)
if command -v docker &> /dev/null; then
    echo "🐳 Checking Docker configuration..."
    (cd web && docker compose config > /dev/null 2>&1)
    check_result "Docker configuration validation"
else
    echo -e "${YELLOW}⚠️  Docker not available, skipping Docker checks${NC}"
fi

# Summary
echo
echo "======================================"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All post-merge validations passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES validation(s) failed${NC}"
    echo "Please review the failures above and fix them."
    exit 1
fi