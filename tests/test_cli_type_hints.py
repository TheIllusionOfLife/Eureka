"""
Tests for CLI type hint coverage and correctness.

This test module validates that all CLI functions have proper type hints
and that mypy can verify them without errors.
"""

import subprocess
from pathlib import Path


def test_mypy_cli_module_passes():
    """Test that mypy passes on the CLI module with --ignore-missing-imports."""
    cli_path = Path("src/madspark/cli")

    result = subprocess.run(
        ["mypy", str(cli_path), "--ignore-missing-imports"],
        capture_output=True,
        text=True
    )

    # Check for CLI-specific errors (ignore errors in other modules)
    cli_errors = [line for line in result.stdout.split('\n') if 'src/madspark/cli/' in line]

    assert len(cli_errors) == 0, "mypy CLI errors:\n" + "\n".join(cli_errors)


def test_batch_metrics_has_proper_optional_type():
    """Test that batch_metrics.py uses Optional[str] for log_file parameter."""
    from madspark.cli.batch_metrics import load_metrics_from_file
    import inspect

    sig = inspect.signature(load_metrics_from_file)
    log_file_param = sig.parameters.get('log_file')

    assert log_file_param is not None, "log_file parameter not found"

    # Check annotation exists
    annotation = log_file_param.annotation
    assert annotation != inspect.Parameter.empty, "log_file has no type annotation"

    # Check it's Optional (Union with None)
    annotation_str = str(annotation)
    assert 'Optional' in annotation_str or 'None' in annotation_str, \
        f"log_file should be Optional[str], got {annotation_str}"


def test_cli_main_functions_have_return_types():
    """Test that main CLI functions have return type annotations."""
    from madspark.cli import cli
    import inspect

    functions_to_check = [
        'main',
        'determine_num_candidates',
        'list_bookmarks_command',
        'search_bookmarks_command',
        'remove_bookmark_command',
    ]

    for func_name in functions_to_check:
        func = getattr(cli, func_name, None)
        assert func is not None, f"Function {func_name} not found"

        sig = inspect.signature(func)
        assert sig.return_annotation != inspect.Signature.empty, \
            f"Function {func_name} is missing return type annotation"


def test_interactive_mode_has_return_types():
    """Test that interactive mode functions have return type annotations."""
    from madspark.cli.interactive_mode import run_interactive_mode, InteractiveSession
    import inspect

    # Check run_interactive_mode
    sig = inspect.signature(run_interactive_mode)
    assert sig.return_annotation != inspect.Signature.empty, \
        "run_interactive_mode is missing return type annotation"

    # Check InteractiveSession methods
    session_methods = [
        'clear_screen',
        'print_header',
        'print_section',
        '_safe_input',
    ]

    for method_name in session_methods:
        method = getattr(InteractiveSession, method_name, None)
        if method:
            sig = inspect.signature(method)
            assert sig.return_annotation != inspect.Signature.empty, \
                f"InteractiveSession.{method_name} is missing return type annotation"


def test_type_definitions_exist():
    """Test that common type definitions are created."""
    try:
        from madspark.cli.types import (
            SessionData,
            WorkflowConfig,
            OutputFormat,
            ExportFormat,
            MetricsData
        )

        # Verify they are proper types
        assert SessionData is not None
        assert WorkflowConfig is not None
        assert OutputFormat is not None
        assert ExportFormat is not None
        assert MetricsData is not None

    except ImportError as e:
        raise AssertionError(f"Type definitions not found: {e}")


def test_formatter_factory_has_proper_types():
    """Test that formatter factory has proper type annotations."""
    from madspark.cli.formatters.factory import FormatterFactory
    import inspect

    # Check create method
    sig = inspect.signature(FormatterFactory.create)
    assert sig.return_annotation != inspect.Signature.empty, \
        "FormatterFactory.create is missing return type annotation"


def test_validation_handler_has_return_types():
    """Test that validation handler functions have return types."""
    from madspark.cli.commands.validation import WorkflowValidator
    import inspect

    # Check execute method
    sig = inspect.signature(WorkflowValidator.execute)
    assert sig.return_annotation != inspect.Signature.empty, \
        "WorkflowValidator.execute is missing return type annotation"
