# MadSpark Multi-Agent System Makefile
.PHONY: help install test test-basic test-docker clean lint format docker-build docker-test docker-dev run

# Default target
help:
	@echo "MadSpark Multi-Agent System"
	@echo "Available commands:"
	@echo "  run          - Run MadSpark coordinator (main program)"
	@echo "  install      - Set up virtual environment and install dependencies"
	@echo "  test         - Run comprehensive test suite"
	@echo "  test-basic   - Run basic functionality tests"
	@echo "  test-docker  - Run tests in Docker container"
	@echo "  lint         - Run linting (if available)"
	@echo "  format       - Format code (if available)"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-test  - Test with Docker"
	@echo "  docker-dev   - Start development container"
	@echo "  clean        - Clean up generated files"

# Setup virtual environment
install:
	@echo "Setting up virtual environment..."
	python3 -m venv test_env
	test_env/bin/pip install --upgrade pip
	test_env/bin/pip install -r requirements.txt
	@echo "✅ Virtual environment ready!"

# Run MadSpark coordinator
run:
	@echo "Running MadSpark coordinator..."
	@if [ -d "test_env" ]; then \
		test_env/bin/python coordinator.py; \
	else \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi

# Run basic tests
test-basic:
	@echo "Running basic functionality tests..."
	@if [ -d "test_env" ]; then \
		test_env/bin/python test_basic.py; \
	else \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi

# Run comprehensive tests
test:
	@echo "Running comprehensive test suite..."
	@if [ -d "test_env" ]; then \
		test_env/bin/python test_runner.py; \
	else \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi

# Docker build
docker-build:
	@echo "Building Docker image..."
	docker build -t madspark-multiagent .

# Test with Docker
docker-test: docker-build
	@echo "Running tests in Docker container..."
	docker run --rm madspark-multiagent python test_basic.py

# Development with Docker
docker-dev:
	@echo "Starting development environment..."
	docker-compose --profile dev up -d dev

# Linting (optional)
lint:
	@echo "Running linting..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
	else \
		echo "Ruff not available, install with: pip install ruff"; \
	fi

# Code formatting (optional)
format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black .; \
	else \
		echo "Black not available, install with: pip install black"; \
	fi

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete
	@echo "✅ Cleanup complete!"

# Show environment info
info:
	@echo "Environment Information:"
	@echo "Python version: $(shell python --version)"
	@echo "Current directory: $(shell pwd)"
	@echo "Virtual environment: $(shell test -d test_env && echo "✅ Available" || echo "❌ Not found")"
	@echo "Docker: $(shell which docker >/dev/null 2>&1 && echo "✅ Available" || echo "❌ Not found")"