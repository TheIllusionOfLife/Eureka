#!/bin/bash
# Run integration tests and final polish checks

set -e

echo "🧪 Running MadSpark Integration Tests"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project root
cd "$(dirname "$0")/.."

# Backend tests
echo -e "\n${YELLOW}Running Python backend tests...${NC}"
cd src
PYTHONPATH=. python3 -m pytest ../tests/ -v
BACKEND_STATUS=$?
cd ..

# Check backend test status
if [ $BACKEND_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests passed${NC}"
else
    echo -e "${RED}❌ Backend tests failed${NC}"
fi

# API documentation test
echo -e "\n${YELLOW}Testing API documentation...${NC}"
cd web/backend
if python3 test_openapi.py; then
    echo -e "${GREEN}✅ API documentation tests passed${NC}"
    API_STATUS=0
else
    echo -e "${RED}❌ API documentation tests failed${NC}"
    API_STATUS=1
fi
cd ../..

# Frontend tests
echo -e "\n${YELLOW}Running React frontend tests...${NC}"
cd web/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Run tests
npm test -- --watchAll=false --passWithNoTests
FRONTEND_STATUS=$?

if [ $FRONTEND_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend tests passed${NC}"
else
    echo -e "${RED}❌ Frontend tests failed${NC}"
fi

# Type checking
echo -e "\n${YELLOW}Running TypeScript type checking...${NC}"
npm run typecheck
TYPECHECK_STATUS=$?

if [ $TYPECHECK_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ TypeScript type checking passed${NC}"
else
    echo -e "${RED}❌ TypeScript type checking failed${NC}"
fi

cd ../..

# Python type checking
echo -e "\n${YELLOW}Running Python type checking...${NC}"
cd src
if command -v mypy &> /dev/null; then
    mypy madspark/
    MYPY_STATUS=$?
    if [ $MYPY_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ Python type checking passed${NC}"
    else
        echo -e "${RED}❌ Python type checking failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  mypy not installed, skipping Python type checking${NC}"
    MYPY_STATUS=0
fi
cd ..

# Linting
echo -e "\n${YELLOW}Running Python linting...${NC}"
cd src
if command -v ruff &> /dev/null; then
    ruff check .
    RUFF_STATUS=$?
    if [ $RUFF_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ Python linting passed${NC}"
    else
        echo -e "${RED}❌ Python linting failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  ruff not installed, skipping Python linting${NC}"
    RUFF_STATUS=0
fi
cd ..

# Docker build test
echo -e "\n${YELLOW}Testing Docker builds...${NC}"
cd web

# Test backend Docker build
echo "Building backend Docker image..."
docker build -f backend/Dockerfile -t madspark-backend:test .
DOCKER_BACKEND_STATUS=$?

# Test frontend Docker build
echo "Building frontend Docker image..."
docker build -f frontend/Dockerfile -t madspark-frontend:test .
DOCKER_FRONTEND_STATUS=$?

if [ $DOCKER_BACKEND_STATUS -eq 0 ] && [ $DOCKER_FRONTEND_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Docker builds successful${NC}"
else
    echo -e "${RED}❌ Docker builds failed${NC}"
fi

cd ..

# Summary
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}Integration Test Summary:${NC}"
echo -e "${GREEN}======================================${NC}"

TOTAL_STATUS=$((BACKEND_STATUS + API_STATUS + FRONTEND_STATUS + TYPECHECK_STATUS + MYPY_STATUS + RUFF_STATUS + DOCKER_BACKEND_STATUS + DOCKER_FRONTEND_STATUS))

if [ $TOTAL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "\n${GREEN}The MadSpark Multi-Agent System is ready for deployment.${NC}"
else
    echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
    exit 1
fi

# Polish checks
echo -e "\n${YELLOW}Running final polish checks...${NC}"

# Check for TODOs
echo "Checking for TODO comments..."
TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX" --include="*.py" --include="*.ts" --include="*.tsx" src/ web/ 2>/dev/null | wc -l)
if [ $TODO_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $TODO_COUNT TODO/FIXME comments${NC}"
else
    echo -e "${GREEN}✅ No TODO comments found${NC}"
fi

# Check for console.log statements
echo "Checking for console.log statements..."
CONSOLE_COUNT=$(grep -r "console\.log" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" web/frontend/src 2>/dev/null | wc -l)
if [ $CONSOLE_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Found $CONSOLE_COUNT console.log statements${NC}"
else
    echo -e "${GREEN}✅ No console.log statements found${NC}"
fi

# Check for hardcoded API keys
echo "Checking for hardcoded secrets..."
SECRET_COUNT=$(grep -r -E "(api_key|apikey|api-key|secret|password|token)" --include="*.py" --include="*.ts" --include="*.tsx" src/ web/ 2>/dev/null | grep -v -E "(test|mock|example|sample|\.env)" | wc -l)
if [ $SECRET_COUNT -gt 0 ]; then
    echo -e "${RED}❌ Potential secrets found! Please review.${NC}"
else
    echo -e "${GREEN}✅ No hardcoded secrets found${NC}"
fi

echo -e "\n${GREEN}Integration testing complete!${NC}"