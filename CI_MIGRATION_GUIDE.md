# CI/CD Migration Guide

## Overview
This guide explains how to migrate from the basic CI to the enhanced CI/CD pipeline with coverage reporting and PR checks.

## Current State
- **ci.yml**: Basic CI with minimal testing
- **ci-enhanced.yml**: Full-featured CI with coverage
- **pr-checks.yml**: Automated PR analysis
- **codecov.yml**: Coverage reporting configuration

## Migration Steps

### Step 1: Backup Existing CI
```bash
cd .github/workflows
cp ci.yml ci-basic.yml.bak
```

### Step 2: Choose Migration Approach

#### Option A: Gradual Migration (Recommended for Active Projects)
1. Keep both workflows running initially
2. Monitor the enhanced CI for stability
3. After 1-2 weeks, disable the old CI

```yaml
# Add to top of old ci.yml
name: CI (Legacy)
on:
  workflow_dispatch:  # Manual trigger only
```

#### Option B: Immediate Migration
```bash
# Replace old CI with enhanced version
mv ci-enhanced.yml ci.yml
```

### Step 3: Configure Codecov (Optional but Recommended)

1. **Sign up at [codecov.io](https://codecov.io)**
2. **Add your repository**
3. **Get the upload token**
4. **Add to GitHub Secrets**:
   - Go to: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Your token from Codecov

### Step 4: Update Branch Protection Rules

1. Go to Settings → Branches
2. Edit protection rules for `main`
3. Add required status checks:
   - `backend-test (3.10)`
   - `backend-test (3.11)`
   - `backend-test (3.12)`
   - `frontend-test`
   - `code-quality`
   - `pr-size`

### Step 5: Test the New Pipeline

1. Create a test PR:
```bash
git checkout -b test/ci-migration
echo "# CI Test" >> test.md
git add test.md
git commit -m "test: verify enhanced CI pipeline"
git push origin test/ci-migration
```

2. Open a PR and verify:
   - PR checks comment appears
   - All CI jobs run
   - Coverage is reported

## Workflow Features Comparison

| Feature | Basic CI | Enhanced CI |
|---------|----------|-------------|
| Python versions | 3.10-3.13 | 3.10-3.12 |
| Backend tests | Basic imports | Full pytest suite |
| Frontend tests | ❌ | ✅ Jest + React Testing |
| Coverage reporting | ❌ | ✅ Codecov integration |
| PR size analysis | ❌ | ✅ Automatic |
| Security scanning | Basic Bandit | ✅ Enhanced Bandit |
| Docker builds | ❌ | ✅ Multi-stage |
| API docs testing | ❌ | ✅ OpenAPI validation |
| Type checking | Optional mypy | ✅ Required mypy |
| Linting | Optional ruff | ✅ ruff + black + isort |

## Troubleshooting

### Issue: Coverage upload fails
**Solution**: Ensure CODECOV_TOKEN is set in GitHub Secrets

### Issue: Frontend tests fail
**Solution**: Check Node.js version matches (v18)

### Issue: Python tests fail on import
**Solution**: Ensure all test dependencies are in requirements.txt

### Issue: PR checks don't appear
**Solution**: Verify pr-checks.yml is in .github/workflows/

## Benefits of Migration

1. **Better Code Quality**: Enforced linting and type checking
2. **Coverage Visibility**: Track test coverage over time
3. **PR Quality Gates**: Automatic size and quality checks
4. **Faster Feedback**: Parallel job execution
5. **Security**: Automated vulnerability scanning
6. **Documentation**: API docs are tested

## Rollback Plan

If issues arise, rollback is simple:
```bash
cd .github/workflows
mv ci-basic.yml.bak ci.yml
rm ci-enhanced.yml pr-checks.yml
```

## Next Steps

After successful migration:
1. Set coverage targets in codecov.yml
2. Add custom PR check rules
3. Configure deployment workflows
4. Add performance benchmarks