#!/bin/bash
# Run all tests with coverage reporting

set -e

echo "🧪 Running MadSpark Test Suite with Coverage"
echo "==========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

# Python tests
echo -e "\n${YELLOW}Running Python backend tests...${NC}"
cd src
PYTHONPATH=. python3 -m pytest ../tests/ -v --cov=madspark --cov-report=term-missing --cov-report=html

# Frontend tests
echo -e "\n${YELLOW}Running React frontend tests...${NC}"
cd ../web/frontend
npm test -- --coverage --watchAll=false --passWithNoTests

# API documentation test
echo -e "\n${YELLOW}Testing API documentation...${NC}"
cd ../backend
if python3 test_openapi.py; then
    echo -e "${GREEN}✅ API documentation tests passed${NC}"
else
    echo -e "${RED}❌ API documentation tests failed${NC}"
fi

# Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Test Coverage Summary:${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Backend coverage report: htmlcov/index.html"
echo "Frontend coverage report: web/frontend/coverage/lcov-report/index.html"
echo ""
echo "View coverage reports in your browser for detailed information."