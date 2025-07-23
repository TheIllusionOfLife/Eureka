# Validation Quick Reference

Quick commands for common validation tasks in MadSpark.

## Pre-PR Checklist

```bash
# 1. Run comprehensive validation
./scripts/validate_pr.sh

# 2. Check dependencies
./scripts/check_dependencies.sh

# 3. Run pre-commit hooks manually
pre-commit run --all-files
```

## Specific Checks

### Python Code Quality
```bash
# Linting
ruff check src/ tests/ web/backend/ --fix

# Type checking
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ web/backend/

# Format code
black src/ tests/ web/backend/
```

### Testing
```bash
# All tests with coverage
PYTHONPATH=src pytest tests/ -v --cov=src

# Quick test run
PYTHONPATH=src MADSPARK_MODE=mock pytest tests/ -x

# Specific test file
PYTHONPATH=src pytest tests/test_agents.py -v

# Skip slow tests
PYTHONPATH=src pytest -m "not slow"
```

### Frontend Validation
```bash
# TypeScript check
cd web/frontend && npm run typecheck

# Linting
cd web/frontend && npm run lint

# Tests
cd web/frontend && npm test

# Build verification
cd web/frontend && npm run build
```

### Docker & Integration
```bash
# Docker build test
cd web && docker compose build

# Docker syntax check
python tests/test_docker_compose_syntax.py

# Run web stack
cd web && docker compose up
```

## PR Size Check
```bash
# Check current changes
git diff main... --stat

# File count
git diff main... --name-only | wc -l

# Line count
git diff main... | wc -l
```

## CI Simulation
```bash
# Set CI environment
export CI=true
export MADSPARK_MODE=mock
export PYTHONPATH=src

# Run CI checks locally
ruff check src/ tests/
pytest tests/ -v
cd web/frontend && npm test
```

## Common Fixes

### Import Errors
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Mock Mode Issues
```bash
export MADSPARK_MODE=mock
```

### Dependency Conflicts
```bash
# Python
pip install -r config/requirements.txt --upgrade

# Frontend
cd web/frontend && rm -rf node_modules package-lock.json && npm install
```

### Pre-commit Issues
```bash
# Update hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install
```

## Emergency Commands

### Revert Changes
```bash
# Undo last commit (keep changes)
git reset HEAD~1

# Discard all changes
git reset --hard HEAD
```

### Fix Broken State
```bash
# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reset git state
git clean -fd
git reset --hard
```

### Check CI Status
```bash
# Recent runs
gh run list --limit 5

# Specific run details
gh run view <run_id> --log

# Re-run failed jobs
gh run rerun <run_id>
```

## Useful Aliases

Add to your shell config:
```bash
# MadSpark validation
alias msvalidate='./scripts/validate_pr.sh'
alias mscheck='./scripts/check_dependencies.sh'
alias mstest='PYTHONPATH=src MADSPARK_MODE=mock pytest tests/ -v'
alias mslint='ruff check src/ tests/ --fix'

# Git helpers
alias prsize='git diff main... --stat'
alias prfiles='git diff main... --name-only | wc -l'
```

## Remember

1. **Always validate before PR**: Run `./scripts/validate_pr.sh`
2. **Keep PRs small**: Under 20 files, 500 lines
3. **Mock mode for tests**: Set `MADSPARK_MODE=mock`
4. **Check dependencies**: Ensure clean installs work
5. **Document changes**: Update relevant docs