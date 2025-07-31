"""Test to validate pytest markers are properly applied and work as expected."""
import subprocess
import pytest
import os
import sys


class TestMarkerValidation:
    """Validate that performance markers work correctly."""
    
    def test_slow_marker_excludes_tests(self):
        """Test that tests marked with @pytest.mark.slow are excluded with -m 'not slow'."""
        # Run pytest with marker filter
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py::TestWorkflowPerformance::test_workflow_execution_time", 
             "-m", "not slow", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        # Should show test was deselected when slow tests are excluded
        assert "deselected" in result.stdout or "deselected" in result.stderr
    
    def test_integration_marker_selection(self):
        """Test that tests marked with @pytest.mark.integration can be selected."""
        # Run pytest to collect only integration tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py::TestEndToEndWorkflow::test_complete_workflow_integration",
             "-m", "integration", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        # Should show 1 test collected when selecting integration tests
        assert "1 test collected" in result.stdout or "1 item" in result.stdout
    
    def test_combined_markers(self):
        """Test that tests can have multiple markers."""
        # This will validate after we apply markers to a test with both @pytest.mark.integration and @pytest.mark.slow
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py::TestAsyncIntegration::test_async_workflow_integration",
             "-m", "integration and slow", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        # Should show 1 test collected when selecting tests with both markers
        assert "1 collected" in result.stdout or "selected" in result.stdout
    
    def test_unmarked_tests_run_by_default(self):
        """Test that unmarked tests run when no marker filter is applied."""
        # Run a simple unit test that won't be marked
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_utils.py::TestRetryDecorator::test_exponential_backoff_success", 
             "-v"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        # Should pass without any marker issues
        assert "PASSED" in result.stdout
    
    def test_ci_performance_improvement(self):
        """Test that excluding slow tests significantly reduces test execution time."""
        import time
        
        # Time all tests
        start_all = time.time()
        result_all = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        time_all = time.time() - start_all
        
        # Time without slow tests
        start_fast = time.time()
        result_fast = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_integration.py", "-m", "not slow", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONPATH": "src"}
        )
        time_fast = time.time() - start_fast
        
        # Fast tests should take less time (at least 20% improvement expected)
        assert time_fast < time_all * 0.8, f"Expected performance improvement, but got {time_fast:.2f}s vs {time_all:.2f}s"