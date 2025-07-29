"""Tests for automatic bookmarking behavior."""
import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch
import argparse

# Import after adding to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from madspark.cli.cli import main


class TestAutomaticBookmarking:
    """Test automatic bookmarking functionality."""
    
    @pytest.fixture
    def temp_bookmark_file(self):
        """Create a temporary bookmark file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @pytest.fixture
    def mock_coordinator_response(self):
        """Mock coordinator response."""
        return [{
            'idea': 'Test idea for automatic bookmarking',
            'initial_score': 7.5,
            'initial_critique': 'Good idea',
            'improved_idea': 'Improved test idea for automatic bookmarking',
            'improved_score': 8.5
        }]
    
    @pytest.mark.skip(reason="Test needs refactoring for new CLI structure")
    def test_bookmarking_happens_by_default(self, temp_bookmark_file, mock_coordinator_response):
        """Test that bookmarking happens automatically without --bookmark-results flag."""
        # Note: This test will fail until we implement automatic bookmarking
        test_args = argparse.Namespace(
            theme='test topic',
            constraints='test context',
            bookmark_results=True,  # This should be True by default (currently fails)
            bookmark_file=temp_bookmark_file,
            bookmark_tags=[],
            no_bookmark=False,  # This flag doesn't exist yet
            output_file=None,
            output_format='text',
            verbose=False
        )
        
        # Mock the argument parser to return our test args
        with patch('argparse.ArgumentParser.parse_args', return_value=test_args):
            with patch('madspark.core.coordinator.run_multistep_workflow', return_value=mock_coordinator_response):
                with patch('madspark.cli.cli.BookmarkManager') as mock_bookmark_manager:
                    # Mock the bookmark manager instance
                    mock_manager_instance = Mock()
                    mock_manager_instance.save_bookmark.return_value = 'bookmark_123'
                    mock_bookmark_manager.return_value = mock_manager_instance
                    
                    # Mock os.path.exists for logs directory
                    with patch('os.path.exists', return_value=True):
                        # Mock print to avoid output
                        with patch('builtins.print'):
                            # Run main without --bookmark-results flag
                            with pytest.raises(SystemExit) as exc_info:
                                main()
                            
                            # Should exit successfully
                            assert exc_info.value.code == 0 or exc_info.value.code is None
                            
                            # Verify bookmark was saved (this currently fails)
                            mock_manager_instance.save_bookmark.assert_called_once()
    
    @pytest.mark.skip(reason="Test needs refactoring for new CLI structure")
    def test_no_bookmark_flag_prevents_bookmarking(self, temp_bookmark_file, mock_coordinator_response):
        """Test that --no-bookmark flag prevents bookmarking."""
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--no-bookmark']):
            with patch('madspark.core.coordinator.run_multistep_workflow', return_value=mock_coordinator_response):
                with patch('madspark.cli.cli.BookmarkManager') as mock_bookmark_manager:
                    # Mock the bookmark manager instance
                    mock_manager_instance = Mock()
                    mock_bookmark_manager.return_value = mock_manager_instance
                    
                    # Run main with --no-bookmark flag
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    # Should exit successfully
                    assert exc_info.value.code == 0 or exc_info.value.code is None
                    
                    # Verify bookmark was NOT attempted
                    mock_manager_instance.save_bookmark.assert_not_called()
    
    @pytest.mark.skip(reason="Test needs refactoring for new CLI structure")
    def test_bookmark_file_is_created_and_updated(self, temp_bookmark_file, mock_coordinator_response):
        """Test that bookmark file is actually created and updated."""
        # Remove the temp file to test creation
        os.unlink(temp_bookmark_file)
        
        with patch('sys.argv', ['cli', 'test topic', 'test context', '--bookmark-file', temp_bookmark_file]):
            with patch('madspark.core.coordinator.run_multistep_workflow', return_value=mock_coordinator_response):
                # Run main - should create bookmark file
                with pytest.raises(SystemExit):
                    main()
                
                # Verify file was created
                assert os.path.exists(temp_bookmark_file)
                
                # Verify content
                with open(temp_bookmark_file, 'r') as f:
                    bookmarks = json.load(f)
                    assert len(bookmarks) == 1
                    
                    # Get the first bookmark
                    bookmark_id = list(bookmarks.keys())[0]
                    bookmark = bookmarks[bookmark_id]
                    
                    # Verify bookmark content
                    assert bookmark['text'] == 'Improved test idea for automatic bookmarking'
                    assert bookmark['theme'] == 'test topic'
                    assert bookmark['score'] == 8.5


class TestOptionalContext:
    """Test that context is optional (ms 'query' should work)."""
    
    @pytest.mark.skip(reason="Test needs refactoring for new CLI structure")
    def test_missing_context_gets_default_value(self):
        """Test that missing context gets a default value."""
        with patch('sys.argv', ['cli', 'test topic']):
            # Mock the parser to capture the namespace
            with patch('madspark.core.coordinator.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                
                try:
                    main()
                except SystemExit:
                    pass
                
                # Get the args passed to the workflow
                args, _ = mock_workflow.call_args
                config = args[0]
                
                # Verify context has default value
                assert config['constraints'] == "Generate practical and innovative ideas"
    
    @pytest.mark.skip(reason="Test needs refactoring for new CLI structure")
    def test_empty_context_gets_default_value(self):
        """Test that empty context gets replaced with default value."""
        with patch('sys.argv', ['cli', 'test topic', '']):
            # Mock the parser to capture the namespace
            with patch('madspark.core.coordinator.run_multistep_workflow') as mock_workflow:
                mock_workflow.return_value = []
                
                try:
                    main()
                except SystemExit:
                    pass
                
                # Get the args passed to the workflow
                args, _ = mock_workflow.call_args
                config = args[0]
                
                # Verify empty context was replaced with default
                assert config['constraints'] == "Generate practical and innovative ideas"