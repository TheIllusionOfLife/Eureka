# Testing Guide for MadSpark

Comprehensive guide for writing and maintaining tests in the MadSpark Multi-Agent System.

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Test Categories & Markers](#test-categories--markers)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Mocking Strategies](#mocking-strategies)
- [Coverage Guidelines](#coverage-guidelines)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)
- [Debugging Tests](#debugging-tests)

---

## Testing Philosophy

- **Test-Driven Development (TDD)**: Write tests first, implementation second
- **Mock by Default**: Use mock mode to avoid external dependencies
- **Fast Feedback**: Tests should run quickly (< 5 seconds per test)
- **Clear Intent**: Test names should describe what they verify
- **Isolation**: Tests should not depend on each other

---

## Test Categories & Markers

We use pytest markers to categorize tests for better organization and CI performance optimization.

### Available Markers

#### `@pytest.mark.unit` (default)
Fast, isolated component tests. No marking needed - this is the default category.

**Characteristics**:
- Single function/method tests
- Simple mock-based tests
- Tests that execute in < 0.5 seconds
- Isolated component tests

#### `@pytest.mark.integration`
Tests that involve multiple components working together.

**Examples**:
- End-to-end workflow tests
- Tests with complex mocking setups (3+ mocked dependencies)
- Web API integration tests
- Docker-related tests
- Tests that use multiple modules/components

#### `@pytest.mark.slow`
Tests that take more than 1 second to execute. These are excluded from PR builds to speed up CI.

**Examples**:
- Tests that measure execution time
- Tests that measure memory usage
- Tests with intentional timeouts or delays (e.g., `time.sleep()`)
- Performance benchmarking tests
- Tests that process large amounts of data

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

# Generate coverage report
pytest tests/ --cov=src --cov-report=html
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

---

## Test Structure

### Directory Organization
```
tests/
├── test_agents.py          # Agent-specific tests
├── test_coordinator.py     # Core coordination logic
├── test_utils.py          # Utility function tests
├── test_cli.py            # CLI interface tests
├── test_integration.py    # End-to-end workflows
├── test_system_integration.py  # Full system tests
└── fixtures/              # Test data and fixtures
```

### Test File Naming
- Unit tests: `test_<module>.py`
- Integration tests: `test_integration_<feature>.py`
- System tests: `test_system_<component>.py`

---

## Writing Tests

### Basic Test Structure
```python
import pytest
from unittest.mock import Mock, patch
import os

# Module imports
from madspark.core.coordinator import Coordinator

class TestCoordinator:
    """Test suite for Coordinator class."""

    @pytest.fixture
    def coordinator(self):
        """Create a coordinator instance for testing."""
        return Coordinator()

    def test_initialization(self, coordinator):
        """Test coordinator initializes with correct defaults."""
        assert coordinator.status == "idle"
        assert coordinator.agents == []
        assert coordinator.results == {}
```

### Mock Mode Testing
```python
@pytest.mark.skipif(
    os.getenv("MADSPARK_MODE") != "mock",
    reason="This test only runs in mock mode"
)
def test_mock_specific_behavior(self, coordinator):
    """Test behavior specific to mock mode."""
    # Test implementation
```

### Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation(self, coordinator):
    """Test asynchronous coordinator operations."""
    result = await coordinator.process_async("test")
    assert result is not None
```

---

## Mocking Strategies

### 1. External API Mocking
```python
@patch('madspark.agents.idea_generator.genai')
def test_idea_generation(self, mock_genai):
    """Test idea generation with mocked API."""
    # Configure mock
    mock_genai.generate_text.return_value = Mock(
        result="Generated idea"
    )

    # Test implementation
    generator = IdeaGenerator()
    result = generator.generate("prompt")

    # Assertions
    assert result == "Generated idea"
    mock_genai.generate_text.assert_called_once()
```

### 2. File System Mocking
```python
@patch('builtins.open', new_callable=mock_open, read_data='test data')
def test_file_reading(self, mock_file):
    """Test file operations with mocked filesystem."""
    result = read_config('config.txt')
    assert result == 'test data'
```

### 3. Environment Variable Mocking
```python
@patch.dict('os.environ', {'MADSPARK_MODE': 'test'})
def test_with_env_var(self):
    """Test with specific environment variables."""
    assert os.getenv('MADSPARK_MODE') == 'test'
```

---

## Coverage Guidelines

### Target Coverage
- Overall: 90%+
- Critical paths: 95%+
- New code: 100%

### Running Coverage
```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage
open htmlcov/index.html

# Coverage with specific markers
pytest tests/ -m "not slow" --cov=src
```

### Coverage Configuration
`.coveragerc`:
```ini
[run]
source = src
omit =
    */tests/*
    */migrations/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if TYPE_CHECKING:
    raise NotImplementedError
```

---

## Performance Testing

### Timing Tests
```python
import time

@pytest.mark.slow
def test_performance(self):
    """Ensure operation completes within time limit."""
    start = time.time()
    result = expensive_operation()
    duration = time.time() - start

    assert duration < 1.0  # Must complete in 1 second
```

### Memory Testing
```python
import psutil
import os

@pytest.mark.slow
def test_memory_usage(self):
    """Test memory usage stays within bounds."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Run operation
    result = memory_intensive_operation()

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Should not use more than 100MB
    assert memory_increase < 100 * 1024 * 1024
```

---

## Best Practices

### Fixtures and Test Data

#### Using Fixtures
```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        'topic': 'AI Ethics',
        'context': 'Modern AI systems',
        'expected_ideas': 5
    }

def test_with_fixture(self, sample_data):
    """Test using fixture data."""
    result = process_topic(sample_data['topic'])
    assert len(result) >= sample_data['expected_ideas']
```

#### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(self, input, expected):
    """Test uppercase conversion with multiple inputs."""
    assert input.upper() == expected
```

### Error Testing

#### Expected Exceptions
```python
def test_invalid_input_raises_error(self):
    """Test appropriate error is raised for invalid input."""
    with pytest.raises(ValueError, match="Invalid topic"):
        process_topic(None)
```

#### Error Messages
```python
def test_error_message_clarity(self):
    """Test error messages are helpful."""
    try:
        invalid_operation()
    except Exception as e:
        assert "specific helpful message" in str(e)
        assert "suggestion for fix" in str(e)
```

### CI/CD Considerations

#### Skip Conditions
```python
@pytest.mark.skipif(
    not os.path.exists('/usr/local/bin/docker'),
    reason="Docker not available"
)
def test_docker_integration(self):
    """Test requiring Docker."""
    # Test implementation
```

### Best Practices Checklist

- [ ] Tests are independent and can run in any order
- [ ] Mock external dependencies
- [ ] Use descriptive test names
- [ ] Test both success and failure paths
- [ ] Include edge cases
- [ ] Keep tests fast (< 5 seconds)
- [ ] Use fixtures for common setup
- [ ] Assert specific values, not just truthiness
- [ ] Clean up resources in teardown
- [ ] Document complex test logic
- [ ] Mark tests appropriately with markers
- [ ] Run all tests before creating PR
- [ ] Update markers if test characteristics change

---

## Debugging Tests

### Using pytest debugging
```python
def test_complex_logic(self):
    """Test with debugging capabilities."""
    result = complex_function()

    # Drop into debugger on failure
    if not result:
        import pdb; pdb.set_trace()

    assert result is not None
```

### Verbose Output
```bash
# Run with verbose output
pytest -vv tests/test_specific.py::test_function

# Show print statements
pytest -s tests/

# Show local variables on failure
pytest -l tests/

# Run specific test with debugging
pytest tests/test_file.py::test_function -vv -s
```

---

## Common Anti-patterns

### 1. Testing Implementation Details
❌ **Bad**: Testing private methods directly
✅ **Good**: Test public interface behavior

### 2. Overly Complex Tests
❌ **Bad**: Tests with multiple concerns
✅ **Good**: One test, one assertion

### 3. Brittle Tests
❌ **Bad**: Tests that break with minor changes
✅ **Good**: Test behavior, not structure

### 4. Slow Tests
❌ **Bad**: Tests that take minutes
✅ **Good**: Mock slow operations, mark with `@pytest.mark.slow`

### 5. Flaky Tests
❌ **Bad**: Tests that sometimes pass/fail
✅ **Good**: Deterministic test outcomes

---

**Last Updated**: 2025-11-06
**Related**: See `CI_CD_GUIDE.md` for CI integration details