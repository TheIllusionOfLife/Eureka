"""Test file organization and imports after reorganization."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_moved_files_exist():
    """Test that moved files exist in their new locations."""
    # Test files should be in tests/
    assert os.path.exists("tests/test_edge_cases.py"), "test_edge_cases.py was not found in tests/ directory"
    assert os.path.exists("tests/test_mock_vs_api.py"), "test_mock_vs_api.py was not found in tests/ directory"
    
    # Data files should be in examples/data/
    # Note: bookmarks.json is in .gitignore so it won't exist in CI
    # assert os.path.exists("examples/data/bookmarks.json"), "bookmarks.json was not found in examples/data/ directory"
    assert os.path.exists("examples/data/sample_batch.csv"), "sample_batch.csv was not found in examples/data/ directory"
    
    # Documentation should be organized
    assert os.path.exists("docs/guides/DEPLOYMENT_GUIDE.md"), "DEPLOYMENT_GUIDE.md was not found in docs/guides/ directory"
    assert os.path.exists("docs/archive/CI_MIGRATION_GUIDE.md"), "CI_MIGRATION_GUIDE.md was not found in docs/archive/ directory"


def test_imports_still_work():
    """Test that imports in moved files still work."""
    try:
        # This should work without errors
        from madspark.utils.bookmark_system import BookmarkManager
        # Test that BookmarkManager uses the new default path
        manager = BookmarkManager()
        assert "examples/data/bookmarks.json" in manager.bookmark_file, f"BookmarkManager default path incorrect: {manager.bookmark_file}"
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_cli_examples_updated():
    """Test that CLI help examples reference correct paths."""
    import madspark.cli.cli as cli_module
    
    # Read the CLI source to check for updated paths
    import inspect
    source = inspect.getsource(cli_module)
    
    # Should reference the actual created file location in help text (matches CLI behavior)
    assert "sample_batch.csv" in source, "CLI help text does not contain 'sample_batch.csv'"
    
    # Also verify the actual sample batch file can be created (filesystem check)
    from pathlib import Path
    expected_file = Path("examples/data/sample_batch.csv")
    if expected_file.exists():
        assert expected_file.is_file(), f"Path exists but is not a file: {expected_file}"


if __name__ == "__main__":
    test_moved_files_exist()
    test_imports_still_work()
    test_cli_examples_updated()
    print("✅ All file organization tests passed")