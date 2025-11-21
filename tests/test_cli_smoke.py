"""Smoke tests for CLI execution."""
import subprocess
import sys
from pathlib import Path

def test_cli_help_smoke():
    """Test that the CLI help command runs without crashing (imports verify)."""
    result = subprocess.run(
        [sys.executable, "-m", "madspark.cli.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "usage: ms" in result.stdout or "usage: cli.py" in result.stdout
