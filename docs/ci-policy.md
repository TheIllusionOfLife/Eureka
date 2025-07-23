# CI/CD Test Management Policy

## Overview

This document defines our policy for managing CI/CD tests in the MadSpark project. The goal is to maintain a fast, reliable, and efficient CI pipeline that catches issues early without overwhelming developers or consuming excessive resources.

## Core Principles

1. **Efficiency First**: Every CI job must provide clear value
2. **No Duplication**: Each test runs exactly once per trigger
3. **Fail Fast**: Quick checks run first to catch obvious issues
4. **Mock by Default**: All CI tests use mock mode unless testing specific integrations
5. **Clear Purpose**: Every workflow has a single, well-defined responsibility

## Workflow Structure

### 1. Primary Workflows

#### `ci.yml` - Main CI Pipeline
- **Triggers**: Push to main/feature branches, PRs
- **Purpose**: Comprehensive testing and validation
- **Phases**:
  1. Quick checks (syntax, deprecated patterns)
  2. Unit tests with coverage
  3. Frontend tests
  4. Security and quality checks
  5. Integration tests (PR and main branch only)
  6. Mock mode validation

#### `pr-validation.yml` - PR-Specific Checks
- **Triggers**: PR events only
- **Purpose**: PR size limits and automated checklists
- **Checks**:
  - File count limits (20 files, 500 lines)
  - PR description quality
  - Test inclusion verification
  - Automated checklist generation

#### `post-merge-validation.yml` - Post-Merge Health Check
- **Triggers**: Push to main branch
- **Purpose**: Catch issues that slip through PR review
- **Actions**:
  - Performance benchmarks
  - Full system integration test
  - Create issues for failures

### 2. Specialized Workflows

#### `claude.yml` - Manual Code Review
- **Triggers**: Issue/PR comments with @claude
- **Purpose**: On-demand AI code review
- **Keep because**: Human-triggered, no automatic overhead

#### `claude-code-review.yml` - Automated PR Review
- **Triggers**: PR opened
- **Purpose**: Automatic AI review for new PRs
- **Keep because**: Provides unique insights not covered by linting

## When to Add CI Tests

### ✅ Add a CI test when:

1. **Preventing Regression**: A bug was fixed and needs a regression test
2. **New Critical Path**: Adding functionality that could break existing features
3. **Security Concern**: New code handles sensitive data or authentication
4. **Integration Point**: New external service or API integration
5. **Performance Critical**: Code that could impact system performance

### ❌ Don't add a CI test when:

1. **Already Covered**: Existing tests already validate the behavior
2. **Local Only**: The test only makes sense in development environment
3. **Flaky by Nature**: The test would be unreliable in CI environment
4. **Excessive Time**: Test takes > 2 minutes to run
5. **External Dependency**: Requires external services not mockable

## When to Modify CI Tests

### Modify existing tests when:

1. **API Changes**: Update mocks to match new API contracts
2. **Performance**: Optimize slow tests (target < 30s per test file)
3. **Flakiness**: Fix intermittent failures
4. **Consolidation**: Combine similar tests to reduce duplication

### Process for modification:

```bash
# 1. Run locally first
PYTHONPATH=src pytest tests/test_to_modify.py -v

# 2. Verify in CI environment
docker run -v $(pwd):/app python:3.10 bash -c "cd /app && pip install -r config/requirements-dev.txt && PYTHONPATH=src pytest tests/test_to_modify.py"

# 3. Update with clear commit message
git commit -m "test: improve X test performance from 45s to 15s"
```

## When to Remove CI Tests

### Remove tests when:

1. **Feature Removed**: The code being tested no longer exists
2. **Redundant Coverage**: Another test provides better coverage
3. **Maintenance Burden**: Test requires constant updates for minimal value
4. **False Positives**: Test fails frequently for non-issues

### Removal checklist:

- [ ] Verify no unique coverage lost
- [ ] Check test wasn't catching real issues
- [ ] Document reason in commit message
- [ ] Update coverage requirements if needed

## Performance Guidelines

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

## Required CI Checks

These checks must ALWAYS pass before merge:

1. **Python Syntax**: All Python files compile
2. **Mock Mode**: CLI works without API keys
3. **Unit Tests**: Core functionality tests pass
4. **Security Scan**: No high-severity vulnerabilities
5. **PR Size**: Within file and line limits

## CI Configuration Rules

### Environment Variables

```yaml
env:
  MADSPARK_MODE: mock  # Always use mock in CI
  PYTHON_VERSION: '3.10'  # Consistent Python version
  NODE_VERSION: '18'  # Consistent Node version
```

### Caching Strategy

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Secret Management

- NEVER commit secrets
- Use GitHub Secrets for API keys
- Mock mode for all automated tests
- Document required secrets in README

## Monitoring and Maintenance

### Weekly Review

- Check CI performance metrics
- Review flaky test reports
- Update deprecated actions
- Clean up old cache entries

### Monthly Tasks

- Audit workflow permissions
- Update action versions
- Review and consolidate tests
- Update this policy document

## Implementation Checklist

When implementing CI changes:

- [ ] Follow single responsibility principle
- [ ] Add clear job names and descriptions
- [ ] Include proper error messages
- [ ] Test locally first
- [ ] Document in commit message
- [ ] Update this policy if needed

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
```

## Contact

For CI/CD questions or improvements:
- Open a GitHub issue with `ci` label
- Discuss in PR comments
- Update this policy via PR