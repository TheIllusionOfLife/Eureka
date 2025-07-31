# Testing Guide

This guide covers testing practices for the MadSpark Multi-Agent System, including the use of pytest markers for test categorization and performance optimization.

## Test Markers

We use pytest markers to categorize tests for better organization and CI performance optimization.

### Available Markers

#### `@pytest.mark.slow`
Tests that take more than 1 second to execute. These are excluded from PR builds to speed up CI.

Examples:
- Tests that measure execution time
- Tests that measure memory usage
- Tests with intentional timeouts or delays
- Performance benchmarking tests

#### `@pytest.mark.integration`
Tests that involve multiple components working together.

Examples:
- End-to-end workflow tests
- Tests with complex mocking setups
- Web API integration tests
- Docker-related tests

#### `@pytest.mark.unit` (default)
Fast, isolated component tests. No marking needed - this is the default category.

### Running Tests by Category

```bash
# Run all tests (default)
pytest tests/

# Run only fast tests (exclude slow tests)
pytest tests/ -m "not slow"

# Run only integration tests
pytest tests/ -m integration

# Run only slow tests
pytest tests/ -m slow

# Run unit tests (unmarked tests)
pytest tests/ -m "not integration and not slow"

# Combine markers
pytest tests/ -m "integration and not slow"
```

### CI Behavior

The CI pipeline uses markers to optimize test execution:

- **PR/Feature Branches**: Run fast tests only (`-m "not slow"`)
  - Typical execution time: 1-2 minutes
  - Excludes performance and long-running integration tests
  
- **Main Branch**: Run all tests
  - Full test coverage maintained
  - Typical execution time: 2-3 minutes

### Adding Markers to Tests

When writing new tests, add appropriate markers:

```python
import pytest

@pytest.mark.integration
def test_workflow_integration():
    """Test that involves multiple components."""
    pass

@pytest.mark.slow
def test_performance_metric():
    """Test that measures performance over time."""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_complex_integration():
    """Test with both markers - complex and slow."""
    pass
```

### Performance Impact

With marker-based test selection:
- PR CI builds are 30-50% faster
- Developers can run fast test suite locally in <30 seconds
- No test coverage loss on main branch
- Clear categorization helps identify test types

### Best Practices

1. **Mark tests appropriately** when creating new tests
2. **Use `not slow` locally** for rapid development feedback
3. **Run all tests** before creating a PR to catch any issues
4. **Update markers** if test characteristics change
5. **Monitor CI times** to ensure markers remain effective

### Marker Guidelines

When to use `@pytest.mark.slow`:
- Test execution time > 1 second
- Tests with `time.sleep()` or intentional delays
- Performance measurement tests
- Memory usage tests
- Tests that process large amounts of data

When to use `@pytest.mark.integration`:
- Tests that use multiple modules/components
- Tests with 3+ mocked dependencies
- End-to-end workflow tests
- API endpoint tests
- Docker or external service tests

When NOT to mark (unit tests):
- Single function/method tests
- Simple mock-based tests
- Tests that execute in < 0.5 seconds
- Isolated component tests