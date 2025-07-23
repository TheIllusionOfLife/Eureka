#!/usr/bin/env python3
"""Test script for EOF handling in interactive mode."""

import sys
import os
from unittest.mock import patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.cli.interactive_mode import InteractiveSession


def test_eof_handling():
    """Test that EOF is handled gracefully."""
    session = InteractiveSession()
    
    # Test EOFError handling
    with patch('builtins.input', side_effect=EOFError()):
        try:
            session.get_input_with_default("Test prompt", "default")
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 0
    
    # Test KeyboardInterrupt handling  
    with patch('builtins.input', side_effect=KeyboardInterrupt()):
        try:
            session.get_yes_no("Test prompt")
            assert False, "Should have exited"
        except SystemExit as e:
            assert e.code == 0
    
    print("✅ EOF handling tests passed!")


def test_normal_input():
    """Test that normal input still works."""
    session = InteractiveSession()
    
    # Test normal input
    with patch('builtins.input', return_value='test input'):
        result = session.get_input_with_default("Test prompt", "default")
        assert result == "test input"
    
    # Test default value
    with patch('builtins.input', return_value=''):
        result = session.get_input_with_default("Test prompt", "default")
        assert result == "default"
    
    # Test yes/no input
    with patch('builtins.input', return_value='y'):
        result = session.get_yes_no("Test prompt")
        assert result is True
    
    with patch('builtins.input', return_value='n'):
        result = session.get_yes_no("Test prompt")
        assert result is False
    
    print("✅ Normal input tests passed!")


if __name__ == "__main__":
    test_eof_handling()
    test_normal_input()
    print("🎉 All interactive mode tests passed!")