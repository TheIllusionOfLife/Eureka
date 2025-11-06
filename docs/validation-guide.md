# Validation Guide for MadSpark

Comprehensive guide covering validation tools, scripts, and quick reference commands to ensure code quality and CI/CD reliability.

## Table of Contents
- [Pre-PR Checklist](#pre-pr-checklist)
- [Validation Scripts](#validation-scripts)
- [Specific Validation Tasks](#specific-validation-tasks)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Quick Reference Commands](#quick-reference-commands)

---

## Pre-PR Checklist

Before creating any pull request, run these commands:

```bash
# 1. Run comprehensive validation
./scripts/validate_pr.sh

# 2. Check dependencies
./scripts/check_dependencies.sh

# 3. Run pre-commit hooks manually
pre-commit run --all-files

# 4. Verify PR size
git diff main... --stat  # Should be under 20 files, 500 lines
```

---

## Pre-commit Hooks

The project uses pre-commit hooks to catch issues before they reach CI. Install them with:

```bash
pip install pre-commit
pre-commit install
```

### Available Hooks

1. **Python Requirements Check** - Verifies all Python dependencies can be installed
2. **NPM Lockfile Consistency** - Ensures package-lock.json is in sync
3. **Docker Compose Syntax** - Checks for deprecated docker-compose commands
4. **Code Formatting** (Black) - Auto-formats Python code
5. **Linting** (Ruff) - Catches code quality issues
6. **Security Scanning** (Bandit) - Identifies security vulnerabilities
7. **Frontend Linting** - TypeScript and React code validation

## Validation Scripts

### PR Validation (`scripts/validate_pr.sh`)

Run comprehensive checks before creating a PR:

```bash
./scripts/validate_pr.sh
```

This script runs:
- Uncommitted changes check
- Code linting (Ruff)
- Type checking (mypy)
- Test suite
- PR size validation
- Security scanning

### Dependency Verification

#### Python Dependencies (`scripts/verify_python_deps.sh`)
```bash
./scripts/verify_python_deps.sh
```
- Checks all requirements files can be installed
- Warns if not in a virtual environment
- Uses pip dry-run to test resolution

#### NPM Dependencies (`scripts/verify_npm_deps.sh`)
```bash
./scripts/verify_npm_deps.sh
```
- Verifies package-lock.json files exist
- Checks dependencies are in sync
- Validates across all package.json files

#### Frontend Build (`scripts/verify_frontend.sh`)
```bash
./scripts/verify_frontend.sh
```
- Runs TypeScript compilation
- Executes React linting
- Validates build process

### Check Dependencies (`scripts/check_dependencies.sh`)
```bash
./scripts/check_dependencies.sh
```
Comprehensive dependency validation:
- Python package verification
- npm package consistency
- Frontend build validation
- Docker syntax checking

## CI/CD Integration

These validation tools are integrated into our CI/CD pipeline:

1. **Pre-commit Stage**: Runs on every commit locally
2. **PR Validation**: GitHub Actions runs all checks
3. **Post-merge Validation**: Ensures main branch stays healthy

## Best Practices

1. **Run Before PR**: Always run `./scripts/validate_pr.sh` before creating a PR
2. **Fix Issues Early**: Address pre-commit hook failures immediately
3. **Keep Dependencies Updated**: Regularly update lock files
4. **Monitor CI Status**: Check GitHub Actions for any failures

## Troubleshooting

### Common Issues

1. **Python dependency conflicts**
   ```bash
   # Reset virtual environment
   python -m venv venv --clear
   source venv/bin/activate
   pip install -r config/requirements.txt
   ```

2. **NPM lockfile out of sync**
   ```bash
   cd web/frontend
   rm package-lock.json
   npm install
   ```

3. **Pre-commit hook failures**
   ```bash
   # Update hooks
   pre-commit autoupdate
   pre-commit run --all-files
   ```

## Adding New Validation

To add new validation checks:

1. Create script in `scripts/` directory
2. Make it executable: `chmod +x scripts/new_check.sh`
3. Add to `.pre-commit-config.yaml` if needed
4. Update this documentation

## Security Considerations

- Bandit scans for common security issues
- Dependencies are checked for known vulnerabilities
- Secrets scanning prevents credential leaks
- All validation runs in isolated environments

---

## Specific Validation Tasks

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

### Testing Commands
```bash
# All tests with coverage
PYTHONPATH=src pytest tests/ -v --cov=src

# Quick test run (fail fast)
PYTHONPATH=src MADSPARK_MODE=mock pytest tests/ -x

# Specific test file
PYTHONPATH=src pytest tests/test_agents.py -v

# Skip slow tests (for rapid feedback)
PYTHONPATH=src pytest -m "not slow"

# Only integration tests
PYTHONPATH=src pytest -m integration
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

### PR Size Check
```bash
# Check current changes against main
git diff main... --stat

# File count
git diff main... --name-only | wc -l

# Line count
git diff main... | wc -l
```

---

## Troubleshooting

### Common Issues

1. **Python dependency conflicts**
   ```bash
   # Reset virtual environment
   python -m venv venv --clear
   source venv/bin/activate
   pip install -r config/requirements.txt
   ```

2. **NPM lockfile out of sync**
   ```bash
   cd web/frontend
   rm package-lock.json
   npm install
   ```

3. **Pre-commit hook failures**
   ```bash
   # Update hooks
   pre-commit autoupdate
   pre-commit run --all-files
   ```

4. **Import Errors**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

5. **Mock Mode Issues**
   ```bash
   export MADSPARK_MODE=mock
   ```

### Emergency Commands

#### Revert Changes
```bash
# Undo last commit (keep changes)
git reset HEAD~1

# Discard all changes
git reset --hard HEAD
```

#### Fix Broken State
```bash
# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reset git state
git clean -fd
git reset --hard
```

#### Check CI Status
```bash
# Recent runs
gh run list --limit 5

# Specific run details
gh run view <run_id> --log

# Re-run failed jobs
gh run rerun <run_id>
```

---

## Quick Reference Commands

### CI Simulation
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

### Useful Shell Aliases

Add to your `.bashrc` or `.zshrc`:
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

---

## Best Practices

1. **Run Before PR**: Always run `./scripts/validate_pr.sh` before creating a PR
2. **Fix Issues Early**: Address pre-commit hook failures immediately
3. **Keep Dependencies Updated**: Regularly update lock files
4. **Monitor CI Status**: Check GitHub Actions for any failures
5. **Keep PRs Small**: Under 20 files, 500 lines
6. **Mock Mode for Tests**: Always set `MADSPARK_MODE=mock` for CI tests
7. **Check Dependencies**: Ensure clean installs work
8. **Document Changes**: Update relevant docs

---

**Last Updated**: 2025-11-06
**Related**: See `CI_CD_GUIDE.md` and `TESTING_GUIDE.md` for more details