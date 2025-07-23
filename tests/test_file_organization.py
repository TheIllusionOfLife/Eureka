"""Test file organization and imports after reorganization."""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_moved_files_exist():
    """Test that moved files exist in their new locations."""
    # Test files should be in tests/
    assert os.path.exists("tests/test_edge_cases.py")
    assert os.path.exists("tests/test_mock_vs_api.py")
    
    # Data files should be in examples/data/
    assert os.path.exists("examples/data/bookmarks.json")
    assert os.path.exists("examples/data/sample_batch.csv")
    
    # Documentation should be organized
    assert os.path.exists("docs/guides/DEPLOYMENT_GUIDE.md")
    assert os.path.exists("docs/archive/CI_MIGRATION_GUIDE.md")


def test_imports_still_work():
    """Test that imports in moved files still work."""
    try:
        # This should work without errors
        from madspark.utils.bookmark_system import BookmarkManager
        # Test that BookmarkManager uses the new default path
        manager = BookmarkManager()
        assert "examples/data/bookmarks.json" in manager.bookmark_file
        return True
    except ImportError as e:
        assert False, f"Import failed: {e}"


def test_cli_examples_updated():
    """Test that CLI help examples reference correct paths."""
    import madspark.cli.cli as cli_module
    
    # Read the CLI source to check for updated paths
    import inspect
    source = inspect.getsource(cli_module)
    
    # Should reference the new data file location in help text
    assert "examples/data/sample_batch.csv" in source


if __name__ == "__main__":
    test_moved_files_exist()
    test_imports_still_work()
    test_cli_examples_updated()
    print("✅ All file organization tests passed")