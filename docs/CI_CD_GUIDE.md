# CI/CD Guide for MadSpark

Comprehensive guide to the MadSpark continuous integration and deployment pipeline, covering policy, best practices, and workflows.

## Table of Contents
- [Overview](#overview)
- [Core Principles](#core-principles)
- [Workflow Architecture](#workflow-architecture)
- [Policy & Guidelines](#policy--guidelines)
- [Performance Optimization](#performance-optimization)
- [Best Practices](#best-practices)
- [Testing Strategy](#testing-strategy)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Overview

Our CI/CD system uses GitHub Actions with a streamlined, performance-optimized workflow structure designed to catch issues early while maintaining fast feedback loops. Target: **< 5 minute total CI time** for standard PRs.

### Core Principles

1. **Efficiency First**: Every CI job must provide clear value
2. **No Duplication**: Each test runs exactly once per trigger
3. **Fail Fast**: Quick checks run first to catch obvious issues
4. **Mock by Default**: All CI tests use mock mode unless testing specific integrations
5. **Clear Purpose**: Every workflow has a single, well-defined responsibility

---

## Workflow Architecture

### Primary Workflows

#### 1. Main CI Pipeline (`ci.yml`)
**Trigger**: Push to main/feature branches, PRs
**Purpose**: Comprehensive testing and validation
**Target Time**: 4-5 minutes

**Phased Approach**:

**Phase 1: Quick Syntax Check** (< 30s)
- Python syntax validation
- YAML/JSON validation
- Import verification
- Deprecated pattern detection

**Phase 2: Test Suite** (2-3 min)
- Backend unit tests with coverage
- Frontend tests
- Integration tests (PR and main only)
- Mock mode validation

**Phase 3: Code Quality** (1-2 min)
- Linting (ruff, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning (Bandit)

**Phase 4: Integration** (2-3 min)
- Docker build verification
- API endpoint testing
- Full system validation

#### 2. PR Validation (`pr-validation.yml`)
**Trigger**: PR events only
**Purpose**: PR size limits and automated checklists

**Checks**:
- File count limits (20 files, 500 lines)
- PR description quality
- Test inclusion verification
- Automated checklist generation
- Dependency change detection

**PR Size Limits**:
- **Max Files**: 20
- **Max Lines**: 500 (warning at 300)
- **Max Additions**: 300
- **Large File Threshold**: 1MB

Override with PR description:
```
SIZE_LIMIT_OVERRIDE: Large refactoring required
```

#### 3. Post-merge Validation (`post-merge-validation.yml`)
**Trigger**: Push to main branch
**Purpose**: Catch issues that slip through PR review

**Actions**:
- Performance benchmarks
- Full system integration test
- CLI smoke test
- Create issues for failures
- Slack notifications (if configured)

### AI-Powered Workflows

#### 4. Claude Review (`claude.yml`)
**Trigger**: Manual via @claude comment
**Purpose**: On-demand AI code review

**Usage**:
```
@claude review this implementation
```

**Keep because**: Human-triggered, no automatic overhead

#### 5. Claude Auto-review (`claude-code-review.yml`)
**Trigger**: PR opened
**Purpose**: Automatic AI review for new PRs

**Keep because**: Provides unique insights not covered by linting

---

## Policy & Guidelines

### When to Add CI Tests

#### ✅ Add a CI test when:

1. **Preventing Regression**: A bug was fixed and needs a regression test
2. **New Critical Path**: Adding functionality that could break existing features
3. **Security Concern**: New code handles sensitive data or authentication
4. **Integration Point**: New external service or API integration
5. **Performance Critical**: Code that could impact system performance

#### ❌ Don't add a CI test when:

1. **Already Covered**: Existing tests already validate the behavior
2. **Local Only**: The test only makes sense in development environment
3. **Flaky by Nature**: The test would be unreliable in CI environment
4. **Excessive Time**: Test takes > 2 minutes to run
5. **External Dependency**: Requires external services not mockable

### When to Modify CI Tests

**Modify existing tests when**:
1. **API Changes**: Update mocks to match new API contracts
2. **Performance**: Optimize slow tests (target < 30s per test file)
3. **Flakiness**: Fix intermittent failures
4. **Consolidation**: Combine similar tests to reduce duplication

**Process for modification**:
```bash
# 1. Run locally first
PYTHONPATH=src pytest tests/test_to_modify.py -v

# 2. Verify in CI environment
docker run -v $(pwd):/app python:3.11.5-slim bash -c "cd /app && pip install -r config/requirements-dev.txt && PYTHONPATH=src pytest tests/test_to_modify.py"

# 3. Update with clear commit message
git commit -m "test: improve X test performance from 45s to 15s"
```

### When to Remove CI Tests

**Remove tests when**:
1. **Feature Removed**: The code being tested no longer exists
2. **Redundant Coverage**: Another test provides better coverage
3. **Maintenance Burden**: Test requires constant updates for minimal value
4. **False Positives**: Test fails frequently for non-issues

**Removal checklist**:
- [ ] Verify no unique coverage lost
- [ ] Check test wasn't catching real issues
- [ ] Document reason in commit message
- [ ] Update coverage requirements if needed

### Required CI Checks

These checks must ALWAYS pass before merge:

1. **Python Syntax**: All Python files compile
2. **Mock Mode**: CLI works without API keys
3. **Unit Tests**: Core functionality tests pass
4. **Security Scan**: No high-severity vulnerabilities
5. **PR Size**: Within file and line limits

---

## Performance Optimization

### Target Metrics

- **Total CI Time**: < 5 minutes for standard PR
- **Quick Checks**: < 30 seconds
- **Unit Tests**: < 2 minutes
- **Integration Tests**: < 3 minutes
- **Frontend Build**: < 1 minute

### Optimization Strategies

1. **Parallelize**: Use matrix builds for independent tests
2. **Cache Aggressively**: Dependencies, build artifacts, test data
3. **Skip Unchanged**: Use path filters for component-specific tests
4. **Mock External Services**: Never call real APIs in CI
5. **Fail Fast**: Stop on first failure in quick checks

### Cache Configuration

```yaml
# Python caching
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

# Node caching
- uses: actions/cache@v3
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### Success Metrics (Based on PR #101 improvements)

| Metric | Before | After |
|--------|--------|-------|
| CI Failure Rate | 75% | <5% |
| Average Feedback Time | 60+ min | 10-15 min |
| Dependency Issues | Weekly | Rare |
| Security Vulnerabilities | Manual check | Automated |

---

## Best Practices

### Development Workflow

#### 1. Before Starting Work

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Verify current state
./scripts/check_dependencies.sh
```

#### 2. During Development

```bash
# Pre-commit hooks run automatically on commit
git commit -m "feat: add new feature"

# Manual verification if needed
pre-commit run --all-files
```

#### 3. Before Creating PR

```bash
# Final verification
./scripts/check_dependencies.sh

# Run local tests
PYTHONPATH=src pytest tests/ -v  # Backend
cd web/frontend && npm test      # Frontend
```

#### 4. PR Review Process

- ✅ Pre-commit hooks passed
- ✅ All CI phases completed
- ✅ Code coverage maintained
- ✅ Security scans passed
- ✅ No deprecated dependencies

### Environment Variables

**Required for CI**:
```bash
MADSPARK_MODE=mock          # Always use mock mode in CI
PYTHONPATH=src              # For module imports
```

**Optional**:
```bash
SKIP_SLOW_TESTS=true        # Skip long-running tests
COVERAGE_THRESHOLD=80       # Minimum coverage percentage
```

### Secret Management

- NEVER commit secrets
- Use GitHub Secrets for API keys
- Mock mode for all automated tests
- Document required secrets in README

**GitHub Secrets used**:
- `CLAUDE_API_KEY`: For AI reviews (optional)
- `SLACK_WEBHOOK`: For notifications (optional)

### Commit Messages

Follow conventional commits:
```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add test coverage
ci: update CI configuration
```

### Branch Protection

Main branch requires:
- All CI checks passing
- At least one approval
- No merge conflicts
- Up-to-date with main

---

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
def test_with_real_api():
    # This test will be skipped in CI
    pass
```

### Pre-commit Hooks

Prevents issues before they reach CI (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: npm-lockfile-consistency
        name: Verify npm package-lock.json consistency
        entry: scripts/verify_npm_deps.sh
        language: script
        files: (package\.json|package-lock\.json)$
```

**Benefits**:
- Catches dependency issues locally
- Reduces CI failures by 80%+
- Fast feedback loop for developers

---

## Troubleshooting

### Common CI Failures

#### 1. Import Errors
**Symptom**: `ModuleNotFoundError`
**Fix**: Ensure `PYTHONPATH=src` is set in workflow

#### 2. Dependency Mismatches
**Symptom**: package.json and package-lock.json out of sync
**Fix**: Use pre-commit hooks for automated validation
```bash
./scripts/verify_npm_deps.sh
```

#### 3. Timeout Failures
**Symptom**: Tests exceed 10-minute limit
**Fix**: Add timeout handling or skip slow tests

#### 4. Mock Mode Failures
**Symptom**: Tests expect real API responses
**Fix**: Add appropriate `@pytest.mark.skipif` decorators

#### 5. Coverage Drops
**Symptom**: Coverage below threshold
**Fix**: Add tests for uncovered code paths

#### 6. Docker Build Failures
**Symptom**: Container build errors
**Fix**: Check Dockerfile syntax and dependencies

#### 7. Deprecated GitHub Actions (Systematic failures)
**Symptom**: Using outdated action versions
**Fix**: Dependabot for Actions, version pinning

### Debugging Tools

#### View CI Logs
```bash
# List recent runs
gh run list --limit 5

# View specific run
gh run view <run-id>

# View logs with details
gh run view <run-id> --log

# Download logs
gh run download <run-id>
```

#### Run CI Locally
```bash
# Simulate CI environment
export MADSPARK_MODE=mock
export PYTHONPATH=src
export CI=true

# Run same commands as CI
ruff check src/ tests/
pytest tests/ -v
cd web/frontend && npm test
```

#### Debug Specific Job
```yaml
# Add to workflow for debugging
- name: Debug Environment
  run: |
    echo "Python: $(python --version)"
    echo "Pip: $(pip --version)"
    echo "Node: $(node --version)"
    echo "Working Dir: $(pwd)"
    echo "PYTHONPATH: $PYTHONPATH"
    ls -la
```

### Verification Scripts

#### 1. Comprehensive Dependency Check
```bash
./scripts/check_dependencies.sh
```

**Checks**:
- Python requirements installation
- npm lockfile consistency
- GitHub Actions deprecation
- Docker configuration validity
- Common security issues

#### 2. Quick Development Verification
```bash
# Python dependencies
./scripts/verify_python_deps.sh

# Frontend dependencies
./scripts/verify_npm_deps.sh

# Frontend build and tests
./scripts/verify_frontend.sh
```

### Dependency Resolution Failures

```bash
# Python
pip install --dry-run -r requirements.txt
pip-compile requirements.in  # If using pip-tools

# npm
npm ci --dry-run
rm package-lock.json && npm install  # Reset lock file
```

---

## Security Considerations

### 1. Secret Management
- Never commit API keys
- Use GitHub Secrets for CI
- Mock external services in tests
- Regular secret rotation

### 2. Dependency Security
```bash
# Python security check
safety check
bandit -r src/

# npm security check
npm audit
npm audit fix
```

### 3. Container Security
```dockerfile
# Use specific versions, not 'latest'
FROM python:3.11.5-slim

# Run as non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
```

---

## Maintenance

### Weekly Tasks
- Review CI run times
- Check for flaky tests
- Update dependencies
- Clear old workflow runs
- Check CI performance metrics

### Monthly Tasks
- Audit workflow permissions
- Update action versions
- Review and consolidate tests
- Update this policy document
- Audit security alerts
- Benchmark performance

### Automated Dependency Management

Dependabot configuration (`.github/dependabot.yml`):

```yaml
- package-ecosystem: "github-actions"
  schedule:
    interval: "weekly"
  ignore:
    - dependency-name: "fastapi"
      update-types: ["version-update:semver-major"]
```

**Benefits**:
- Automatic security updates
- Prevents deprecated action issues
- Controlled major version updates

---

## Monitoring and Alerts

### 1. CI Health Monitoring

Track these metrics:
- Build success rate by branch
- Average build time trends
- Flaky test identification
- Dependency update success rate

### 2. Alert Configuration

Set up notifications for:
- Multiple consecutive CI failures
- Long-running builds (>30 min)
- Security vulnerability detection
- Dependency conflict resolution failures

---

## Quick Reference

```bash
# Validate CI changes locally
./scripts/validate_pr.sh

# Test specific workflow
act -W .github/workflows/ci.yml

# Check current CI status
gh run list --limit 5

# Debug failed CI run
gh run view <run-id> --log

# Pre-commit validation
pre-commit run --all-files
```

---

## Implementation Checklist

When implementing CI changes:

- [ ] Follow single responsibility principle
- [ ] Add clear job names and descriptions
- [ ] Include proper error messages
- [ ] Test locally first
- [ ] Document in commit message
- [ ] Update this guide if needed

---

## Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/essential-features-of-github-actions)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Dependabot Configuration](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)

---

**Last Updated**: 2025-11-06
**Next Review**: 2025-12-06

For CI/CD questions or improvements:
- Open a GitHub issue with `ci` label
- Discuss in PR comments
- Update this guide via PR
