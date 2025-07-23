# Contributing to MadSpark

Thank you for your interest in contributing to MadSpark! This guide will help you contribute effectively while maintaining code quality and project stability.

## 🎯 Core Principles

1. **Mock-First Development**: Always ensure your code works without API keys
2. **Small PRs**: Keep changes focused and under 20 files
3. **Test-Driven**: Write tests before implementation
4. **Systematic Validation**: Use our automated tools

## 📋 Before You Start

1. **Read the Documentation**
   - [README.md](README.md) - Project overview
   - [CLAUDE.md](CLAUDE.md) - AI assistant guidelines
   - [Architecture docs](docs/) - System design

2. **Set Up Your Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/TheIllusionOfLife/Eureka.git
   cd Eureka
   
   # Install dependencies
   pip install -r config/requirements.txt
   pip install -r config/requirements-dev.txt
   
   # Install pre-commit hooks
   pip install pre-commit
   pre-commit install
   ```

3. **Verify Mock Mode Works**
   ```bash
   export MADSPARK_MODE=mock
   python -m madspark.cli.cli "test" "test"
   ```

## 🔄 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write tests first (TDD approach)
- Keep changes focused and minimal
- Follow existing code patterns

### 3. Run Validation
```bash
# Before committing - run our validation script
./scripts/validate_pr.sh

# Pre-commit hooks will also run automatically
git commit -m "feat: your feature description"
```

### 4. Create a Pull Request
- Use our PR template (automatically loaded)
- Ensure all checklist items are completed
- Keep PR size under limits:
  - ✅ < 20 files
  - ✅ < 500 lines changed

## 📏 PR Size Guidelines

Large PRs are exponentially harder to review. If your change is large:

1. **Split by Feature**
   ```
   PR 1: Core implementation (10 files)
   PR 2: Tests (10 files)
   PR 3: Documentation (5 files)
   ```

2. **Split by Component**
   ```
   PR 1: Backend changes
   PR 2: Frontend changes
   PR 3: Configuration updates
   ```

3. **Use Feature Flags**
   ```python
   if settings.feature_enabled("new_feature"):
       # New implementation
   else:
       # Existing implementation
   ```

## 🧪 Testing Requirements

### Mock Mode is Primary
```python
# Bad - requires API key
def test_feature():
    client = RealAPIClient(api_key=os.getenv("API_KEY"))
    
# Good - works in mock mode
def test_feature():
    os.environ["MADSPARK_MODE"] = "mock"
    client = get_client()  # Returns mock client
```

### Test Coverage
- Aim for 70%+ coverage
- Test edge cases
- Include integration tests

### Running Tests
```bash
# All tests
PYTHONPATH=src pytest tests/ -v

# Specific component
PYTHONPATH=src pytest tests/test_agents.py -v

# With coverage
PYTHONPATH=src pytest tests/ --cov=src --cov-report=html
```

## 🚫 Common Pitfalls to Avoid

### 1. Hardcoding API Requirements
```python
# ❌ Bad
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("API key required")

# ✅ Good
from madspark.config import get_mode
if get_mode() == "direct" and not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("API key required for direct mode")
```

### 2. Using Deprecated Syntax
```bash
# ❌ Bad
docker-compose up

# ✅ Good
docker compose up
```

### 3. Massive PRs
```bash
# ❌ Bad
git add -A  # 100 files changed

# ✅ Good
git add src/feature/*.py tests/test_feature.py  # 5 files
```

## 🔍 Code Review Process

1. **Automated Checks**
   - PR size validation
   - Mock mode testing
   - Security scanning
   - Syntax validation

2. **Manual Review Focus**
   - Logic correctness
   - Performance implications
   - Security considerations
   - Documentation clarity

3. **Post-Merge Validation**
   - Automated validation runs on main
   - Issues create GitHub issues
   - Quick rollback if needed

## 🛠️ Useful Commands

```bash
# Validate your PR before submission
./scripts/validate_pr.sh

# Run post-merge validation locally
./scripts/post_merge_validation.sh

# Check mock mode
MADSPARK_MODE=mock python -m madspark.cli.cli "test" "test"

# Format code
black src/ tests/
ruff check --fix src/ tests/

# Security scan
bandit -r src/
```

## 📚 Documentation

When adding new features:
1. Update relevant docstrings
2. Add usage examples
3. Update README if needed
4. Consider adding to docs/

## 🐛 Reporting Issues

1. Check existing issues first
2. Use issue templates
3. Include:
   - Clear reproduction steps
   - Expected vs actual behavior
   - Environment details
   - Error messages/logs

## 💡 Feature Requests

1. Open a discussion first
2. Explain the use case
3. Consider implementation approach
4. Be open to feedback

## 🤝 Getting Help

- **GitHub Discussions**: General questions
- **Issues**: Bug reports and features
- **PR Comments**: Code-specific questions

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Maintain professional communication

---

Remember: **Quality > Quantity**. A well-tested, focused PR is worth more than a large, complex one. Thank you for contributing to MadSpark!