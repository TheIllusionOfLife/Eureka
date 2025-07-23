# CI/CD Guide

Comprehensive guide to the MadSpark continuous integration and deployment pipeline.

## Overview

Our CI/CD system uses GitHub Actions with a streamlined, performance-optimized workflow structure designed to catch issues early while maintaining fast feedback loops.

## Workflow Architecture

### Primary Workflows

#### 1. Main CI Pipeline (`ci.yml`)
**Trigger**: Push to main, PRs
**Purpose**: Core validation pipeline with phased approach

**Phases**:
1. **Quick Syntax Check** (< 30s)
   - Python syntax validation
   - YAML/JSON validation
   - Import verification

2. **Test Suite** (2-3 min)
   - Backend tests with coverage
   - Frontend tests
   - Integration tests

3. **Code Quality** (1-2 min)
   - Ruff linting
   - Type checking (mypy)
   - Security scanning (Bandit)

4. **Integration** (2-3 min)
   - Docker build verification
   - API endpoint testing
   - Mock mode validation

#### 2. PR Validation (`pr-validation.yml`)
**Trigger**: PR events
**Purpose**: PR-specific checks

**Features**:
- Size limit enforcement (20 files, 500 lines)
- Automated PR checklist
- Dependency change detection
- Test coverage validation

#### 3. Post-merge Validation (`post-merge-validation.yml`)
**Trigger**: Push to main
**Purpose**: Ensure main branch health

**Actions**:
- CLI smoke test
- Core functionality validation
- Issue creation on failure
- Slack notifications (if configured)

### AI-Powered Workflows

#### 4. Claude Review (`claude.yml`)
**Trigger**: Manual via @claude comment
**Purpose**: AI-powered code review

**Usage**:
```
@claude review this implementation
```

#### 5. Claude Auto-review (`claude-code-review.yml`)
**Trigger**: New PRs
**Purpose**: Automatic AI analysis

## Performance Optimization

### Target: < 5 minute total CI time

**Strategies**:
1. **Parallel Execution**: Independent jobs run concurrently
2. **Fail Fast**: Quick checks first to catch obvious issues
3. **Caching**: 
   - Python dependencies (pip)
   - Node modules (npm)
   - Docker layers
4. **Mock Mode**: All tests use mock mode to avoid API calls
5. **Selective Testing**: Only run affected test suites

### Cache Configuration

```yaml
# Python caching
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

# Node caching
- uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
```

## Configuration

### Environment Variables

Required for CI:
```bash
MADSPARK_MODE=mock          # Always use mock mode in CI
PYTHONPATH=src              # For module imports
```

Optional:
```bash
SKIP_SLOW_TESTS=true        # Skip long-running tests
COVERAGE_THRESHOLD=80       # Minimum coverage percentage
```

### Secrets Management

GitHub Secrets used:
- `CLAUDE_API_KEY`: For AI reviews (optional)
- `SLACK_WEBHOOK`: For notifications (optional)

## PR Size Limits

Enforced via `pr-validation.yml`:
- **Max Files**: 20
- **Max Lines**: 500 (warning at 300)
- **Max Additions**: 300
- **Large File Threshold**: 1MB

Override with PR description:
```
SIZE_LIMIT_OVERRIDE: Large refactoring required
```

## Testing Strategy

### Test Categories

1. **Unit Tests** (`test_*.py`)
   - Fast, isolated component tests
   - Must run in < 10s each
   - 90%+ coverage target

2. **Integration Tests** (`test_integration.py`)
   - End-to-end workflow validation
   - Mock external dependencies
   - Skip in SKIP_SLOW_TESTS mode

3. **System Tests** (`test_system_integration.py`)
   - Full system validation
   - Docker integration
   - Web API testing

### Mock Mode Testing

All CI tests run in mock mode:
```python
@pytest.mark.skipif(
    os.getenv("MADSPARK_MODE") == "mock",
    reason="Real API calls not available in mock mode"
)
```

## Common CI Failures

### 1. Import Errors
**Symptom**: `ModuleNotFoundError`
**Fix**: Ensure `PYTHONPATH=src` is set

### 2. Timeout Failures
**Symptom**: Tests exceed 10-minute limit
**Fix**: Add timeout handling or skip slow tests

### 3. Mock Mode Failures
**Symptom**: Tests expect real API responses
**Fix**: Add appropriate `@pytest.mark.skipif` decorators

### 4. Coverage Drops
**Symptom**: Coverage below threshold
**Fix**: Add tests for uncovered code paths

### 5. Docker Build Failures
**Symptom**: Container build errors
**Fix**: Check Dockerfile syntax and dependencies

## Best Practices

### 1. Pre-push Validation
Always run locally before pushing:
```bash
./scripts/validate_pr.sh
```

### 2. Commit Messages
Follow conventional commits:
```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add test coverage
ci: update CI configuration
```

### 3. Branch Protection
Main branch requires:
- All CI checks passing
- At least one approval
- No merge conflicts
- Up-to-date with main

### 4. Monitoring

Check CI status:
```bash
gh run list --limit 5
gh run view <run-id> --log
```

## Debugging CI Issues

### 1. View Logs
```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# Download logs
gh run download <run-id>
```

### 2. Run CI Locally
```bash
# Simulate CI environment
export MADSPARK_MODE=mock
export PYTHONPATH=src
export CI=true

# Run same commands as CI
ruff check src/ tests/
pytest tests/ -v
```

### 3. Debug Specific Job
```yaml
# Add to workflow for debugging
- name: Debug Environment
  run: |
    echo "Python: $(python --version)"
    echo "Pip: $(pip --version)"
    echo "Working Dir: $(pwd)"
    echo "PYTHONPATH: $PYTHONPATH"
```

## Maintenance

### Weekly Tasks
- Review CI run times
- Check for flaky tests
- Update dependencies
- Clear old workflow runs

### Monthly Tasks
- Audit security alerts
- Update GitHub Actions versions
- Review and optimize caching
- Benchmark performance

## Future Enhancements

1. **Deployment Pipeline**: Automated deployment to staging/production
2. **Performance Testing**: Load testing integration
3. **Visual Regression**: Screenshot comparison for UI
4. **Dependency Updates**: Automated PR creation for updates
5. **Multi-environment Testing**: Test against multiple Python/Node versions