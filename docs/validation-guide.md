# Validation Guide

This guide covers the validation tools and scripts available in the MadSpark project to ensure code quality and CI/CD reliability.

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