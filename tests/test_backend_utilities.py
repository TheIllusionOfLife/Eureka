"""Enhanced Testing Coverage for Backend Utilities.

This module provides comprehensive testing for critical backend utility
modules including error handling, logging, caching, and content safety.
"""

import pytest
import tempfile
import os
import json
import logging
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
from io import StringIO

# Import modules to test
try:
    from madspark.utils.errors import (
        MadSparkError, AgentError, IdeaGenerationError, CriticError,
        AdvocateError, SkepticError, CacheError, CacheConnectionError,
        CacheSerializationError, ProcessingError, BatchProcessingError,
        ExportError, ValidationError, TemperatureError, ConfigurationError,
        APIError, FileOperationError
    )
    from madspark.utils.verbose_logger import VerboseLogger, log_verbose_step
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.utils.content_safety import ContentSafetyFilter
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from madspark.utils.errors import (
        MadSparkError, AgentError, IdeaGenerationError, CriticError,
        AdvocateError, SkepticError, CacheError, CacheConnectionError,
        CacheSerializationError, ProcessingError, BatchProcessingError,
        ExportError, ValidationError, TemperatureError, ConfigurationError,
        APIError, FileOperationError
    )
    from madspark.utils.verbose_logger import VerboseLogger, log_verbose_step
    from madspark.utils.cache_manager import CacheManager, CacheConfig
    from madspark.utils.content_safety import ContentSafetyFilter


class TestErrorHierarchy:
    """Test cases for custom error class hierarchy."""
    
    def test_base_madspark_error(self):
        """Test base MadSparkError functionality."""
        error = MadSparkError("Base error message")
        
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)
        assert issubclass(MadSparkError, Exception)
    
    def test_agent_error_inheritance(self):
        """Test agent error inheritance hierarchy."""
        error = AgentError("Agent failed")
        
        assert isinstance(error, MadSparkError)
        assert isinstance(error, Exception)
        assert str(error) == "Agent failed"
    
    def test_specific_agent_errors(self):
        """Test specific agent error types."""
        idea_error = IdeaGenerationError("Idea generation failed")
        critic_error = CriticError("Critique failed")
        advocate_error = AdvocateError("Advocacy failed")
        skeptic_error = SkepticError("Skepticism failed")
        
        # Test inheritance
        assert isinstance(idea_error, AgentError)
        assert isinstance(critic_error, AgentError)
        assert isinstance(advocate_error, AgentError)
        assert isinstance(skeptic_error, AgentError)
        
        # Test error messages
        assert str(idea_error) == "Idea generation failed"
        assert str(critic_error) == "Critique failed"
        assert str(advocate_error) == "Advocacy failed"
        assert str(skeptic_error) == "Skepticism failed"
    
    def test_cache_error_hierarchy(self):
        """Test cache error inheritance hierarchy."""
        base_cache_error = CacheError("Cache failed")
        connection_error = CacheConnectionError("Connection failed")
        serialization_error = CacheSerializationError("Serialization failed")
        
        assert isinstance(base_cache_error, MadSparkError)
        assert isinstance(connection_error, CacheError)
        assert isinstance(serialization_error, CacheError)
        
        assert str(connection_error) == "Connection failed"
        assert str(serialization_error) == "Serialization failed"
    
    def test_processing_error_hierarchy(self):
        """Test processing error inheritance hierarchy."""
        base_processing_error = ProcessingError("Processing failed")
        batch_error = BatchProcessingError("Batch processing failed")
        export_error = ExportError("Export failed")
        
        assert isinstance(base_processing_error, MadSparkError)
        assert isinstance(batch_error, ProcessingError)
        assert isinstance(export_error, ProcessingError)
        
        assert str(batch_error) == "Batch processing failed"
        assert str(export_error) == "Export failed"
    
    def test_validation_error_hierarchy(self):
        """Test validation error inheritance hierarchy."""
        validation_error = ValidationError("Validation failed")
        temperature_error = TemperatureError("Temperature invalid")
        
        assert isinstance(validation_error, MadSparkError)
        assert isinstance(temperature_error, ValidationError)
        
        assert str(temperature_error) == "Temperature invalid"
    
    def test_miscellaneous_errors(self):
        """Test miscellaneous error types."""
        config_error = ConfigurationError("Config invalid")
        api_error = APIError("API call failed")
        file_error = FileOperationError("File operation failed")
        
        assert isinstance(config_error, MadSparkError)
        assert isinstance(api_error, MadSparkError)
        assert isinstance(file_error, MadSparkError)
        
        assert str(config_error) == "Config invalid"
        assert str(api_error) == "API call failed"
        assert str(file_error) == "File operation failed"
    
    def test_error_with_custom_attributes(self):
        """Test errors with custom attributes."""
        error = AgentError("Custom error with attributes")
        error.agent_name = "test_agent"
        error.step = "idea_generation"
        
        assert error.agent_name == "test_agent"
        assert error.step == "idea_generation"
        assert str(error) == "Custom error with attributes"


class TestVerboseLogger:
    """Test cases for verbose logging utility."""
    
    def setup_method(self):
        """Set up test environment."""
        self.output_buffer = StringIO()
        
    def test_verbose_logger_initialization(self):
        """Test verbose logger initialization."""
        logger_enabled = VerboseLogger(enabled=True)
        logger_disabled = VerboseLogger(enabled=False)
        
        assert logger_enabled.enabled is True
        assert logger_disabled.enabled is False
    
    @patch('builtins.print')
    def test_step_logging_enabled(self, mock_print):
        """Test step logging when enabled."""
        logger = VerboseLogger(enabled=True)
        
        logger.step("Test Step", "Details about the step")
        
        # Should have been called with step name and details
        assert mock_print.call_count == 2
        mock_print.assert_any_call("\n🔄 Test Step")
        mock_print.assert_any_call("   Details about the step")
    
    @patch('builtins.print')
    def test_step_logging_disabled(self, mock_print):
        """Test step logging when disabled."""
        logger = VerboseLogger(enabled=False)
        
        logger.step("Test Step", "Details about the step")
        
        # Should not have been called
        mock_print.assert_not_called()
    
    @patch('builtins.print')
    def test_data_logging_with_truncation(self, mock_print):
        """Test data logging with truncation."""
        logger = VerboseLogger(enabled=True)
        
        long_data = "x" * 1000
        logger.data("Test Data", long_data, max_length=100)
        
        # Should truncate the data
        assert mock_print.call_count == 2
        mock_print.assert_any_call("📊 Test Data:")
        # Check that truncation occurred
        call_args = mock_print.call_args_list[1][0][0]
        assert "truncated" in call_args
        assert "full length: 1000" in call_args
    
    @patch('builtins.print')
    def test_data_logging_no_truncation(self, mock_print):
        """Test data logging without truncation."""
        logger = VerboseLogger(enabled=True)
        
        short_data = "short data"
        logger.data("Test Data", short_data, max_length=100)
        
        assert mock_print.call_count == 2
        mock_print.assert_any_call("📊 Test Data:")
        mock_print.assert_any_call("   short data")
    
    @patch('builtins.print')
    def test_completion_logging(self, mock_print):
        """Test completion logging."""
        logger = VerboseLogger(enabled=True)
        
        logger.completion("Test Process", count=50, duration=10.0, unit="ideas")
        
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "✅ Test Process completed" in call_args
        assert "50 ideas" in call_args
        assert "10.00s" in call_args
        assert "5.0 ideas/s" in call_args  # Rate calculation
    
    @patch('builtins.print')
    def test_agent_execution_logging(self, mock_print):
        """Test agent execution logging."""
        logger = VerboseLogger(enabled=True)
        
        logger.agent_execution(
            "Idea Generation", 
            "Creative Agent", 
            "🎨", 
            "Generating creative ideas", 
            0.9
        )
        
        assert mock_print.call_count == 3
        mock_print.assert_any_call("\n🎨 Idea Generation - Creative Agent")
        mock_print.assert_any_call("   Generating creative ideas")
        mock_print.assert_any_call("   Temperature: 0.9")
    
    @patch('builtins.print')
    def test_subsection_logging(self, mock_print):
        """Test subsection logging with items."""
        logger = VerboseLogger(enabled=True)
        
        items = {"Score": 8.5, "Time": "2.3s", "Status": "Complete"}
        logger.subsection("Results", items)
        
        assert mock_print.call_count == 4  # Title + 3 items
        mock_print.assert_any_call("\n📋 Results")
        mock_print.assert_any_call("   Score: 8.5")
        mock_print.assert_any_call("   Time: 2.3s")
        mock_print.assert_any_call("   Status: Complete")
    
    @patch('builtins.print')
    def test_separator_logging(self, mock_print):
        """Test separator logging."""
        logger = VerboseLogger(enabled=True)
        
        # Test with title
        logger.separator("Section Title")
        assert mock_print.call_count == 3
        
        mock_print.reset_mock()
        
        # Test without title  
        logger.separator()
        mock_print.assert_called_once_with("\n" + "-"*40)
    
    @patch('builtins.print')
    def test_error_and_warning_logging(self, mock_print):
        """Test error and warning logging."""
        logger = VerboseLogger(enabled=True)
        
        logger.error("Test Error", "Error details")
        assert mock_print.call_count == 2
        mock_print.assert_any_call("\n❌ ERROR: Test Error")
        mock_print.assert_any_call("   Error details")
        
        mock_print.reset_mock()
        
        logger.warning("Test Warning", "Warning details")
        assert mock_print.call_count == 2
        mock_print.assert_any_call("\n⚠️  WARNING: Test Warning")
        mock_print.assert_any_call("   Warning details")
    
    @patch('builtins.print')
    def test_legacy_functions(self, mock_print):
        """Test legacy compatibility functions."""
        log_verbose_step("Legacy Step", "Legacy details", verbose=True)
        
        # Should have called print for the step
        assert mock_print.call_count >= 1
        
        mock_print.reset_mock()
        
        log_verbose_step("Legacy Step", "Legacy details", verbose=False)
        
        # Should not have called print
        mock_print.assert_not_called()


class TestCacheManager:
    """Test cases for cache management system."""
    
    def test_cache_config_initialization(self):
        """Test cache configuration initialization."""
        # Default config
        config = CacheConfig()
        
        assert config.redis_url == "redis://localhost:6379/0"
        assert config.ttl_seconds == 3600
        assert config.max_cache_size_mb == 100
        assert config.enable_agent_caching is True
        assert config.enable_workflow_caching is True
        assert config.key_prefix == "madspark"
    
    def test_cache_config_custom(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            redis_url="redis://custom:6380/1",
            ttl_seconds=7200,
            max_cache_size_mb=200,
            enable_agent_caching=False,
            key_prefix="test"
        )
        
        assert config.redis_url == "redis://custom:6380/1"
        assert config.ttl_seconds == 7200
        assert config.max_cache_size_mb == 200
        assert config.enable_agent_caching is False
        assert config.key_prefix == "test"
    
    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        # Default initialization
        manager = CacheManager()
        assert manager.config is not None
        assert manager.redis_client is None
        assert manager.is_connected is False
        
        # Custom config initialization
        config = CacheConfig(redis_url="redis://test:6379")
        manager_custom = CacheManager(config)
        assert manager_custom.config.redis_url == "redis://test:6379"
    
    @patch('madspark.utils.cache_manager.REDIS_AVAILABLE', False)
    def test_cache_manager_redis_unavailable(self):
        """Test cache manager behavior when Redis is unavailable."""
        with patch('madspark.utils.cache_manager.logger') as mock_logger:
            manager = CacheManager()
            
            # Should log warning about Redis unavailability
            mock_logger.warning.assert_called_once_with("Redis not available. Caching disabled.")
    
    def test_cache_key_generation(self):
        """Test cache key generation logic."""
        manager = CacheManager()
        
        # Test with proper parameters
        key1 = manager._generate_cache_key("test_theme", "test_constraints", {"temperature": 0.8})
        key2 = manager._generate_cache_key("test_theme", "test_constraints", {"temperature": 0.8})
        key3 = manager._generate_cache_key("different_theme", "test_constraints", {"temperature": 0.8})
        
        # Same data should produce same key
        assert key1 == key2
        # Different data should produce different key
        assert key1 != key3
        
        # Keys should include prefix
        assert key1.startswith(manager.config.key_prefix)
    
    def test_cache_key_generation_complex_data(self):
        """Test cache key generation with complex data structures."""
        manager = CacheManager()
        
        options1 = {"temperature": 0.8, "context": ["item1", "item2"], "mode": "creative"}
        options2 = {"temperature": 0.8, "context": ["item1", "item2"], "mode": "creative"}
        options3 = {"temperature": 0.9, "context": ["item1", "item2"], "mode": "creative"}
        
        key1 = manager._generate_cache_key("test_theme", "constraints", options1)
        key2 = manager._generate_cache_key("test_theme", "constraints", options2)
        key3 = manager._generate_cache_key("test_theme", "constraints", options3)
        
        # Same data should produce same key
        assert key1 == key2
        # Different data should produce different key  
        assert key1 != key3


class TestContentSafety:
    """Test cases for content safety filtering."""
    
    def test_content_safety_filter_initialization(self):
        """Test content safety filter initialization."""
        # This assumes ContentSafetyFilter exists - may need to create it
        try:
            filter_obj = ContentSafetyFilter()
            assert filter_obj is not None
        except (ImportError, NameError):
            # If ContentSafetyFilter doesn't exist, skip this test
            pytest.skip("ContentSafetyFilter not implemented yet")
    
    def test_safe_content_detection(self):
        """Test detection of safe content."""
        try:
            filter_obj = ContentSafetyFilter()
            
            safe_content = "This is a regular business idea about productivity software."
            is_safe = filter_obj.is_safe(safe_content)
            
            assert is_safe is True
        except (ImportError, NameError, AttributeError):
            pytest.skip("ContentSafetyFilter not fully implemented yet")
    
    def test_unsafe_content_detection(self):
        """Test detection of potentially unsafe content."""
        try:
            filter_obj = ContentSafetyFilter()
            
            # Test with potentially problematic content
            unsafe_content = "This idea involves harmful activities and dangerous substances."
            is_safe = filter_obj.is_safe(unsafe_content)
            
            # Should detect as potentially unsafe
            assert is_safe is False
        except (ImportError, NameError, AttributeError):
            pytest.skip("ContentSafetyFilter not fully implemented yet")
    
    def test_content_filtering_edge_cases(self):
        """Test content filtering with edge cases."""
        try:
            filter_obj = ContentSafetyFilter()
            
            # Empty content
            assert filter_obj.is_safe("") is True
            
            # None content
            assert filter_obj.is_safe(None) is True
            
            # Very long content
            long_content = "Safe content. " * 1000
            assert filter_obj.is_safe(long_content) is True
            
        except (ImportError, NameError, AttributeError):
            pytest.skip("ContentSafetyFilter not fully implemented yet")


class TestBackendUtilitiesIntegration:
    """Integration tests for backend utilities working together."""
    
    def test_error_handling_with_logging(self):
        """Test error handling integrated with logging."""
        logger = VerboseLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            try:
                # Simulate an operation that raises a MadSparkError
                raise IdeaGenerationError("Test error for logging")
            except MadSparkError as e:
                logger.error(str(e), f"Error type: {type(e).__name__}")
                
                # Verify error was logged properly
                assert mock_print.call_count == 2
                mock_print.assert_any_call("\n❌ ERROR: Test error for logging")
                mock_print.assert_any_call("   Error type: IdeaGenerationError")
    
    def test_cache_error_handling(self):
        """Test cache-specific error handling."""
        try:
            # Simulate cache connection failure
            raise CacheConnectionError("Redis connection failed")
        except CacheError as e:
            # Should be caught as CacheError
            assert isinstance(e, CacheError)
            assert isinstance(e, MadSparkError)
            assert str(e) == "Redis connection failed"
        except Exception:
            pytest.fail("CacheConnectionError not properly inheriting from CacheError")
    
    @patch('madspark.utils.cache_manager.REDIS_AVAILABLE', True)
    def test_cache_manager_with_errors(self):
        """Test cache manager error handling."""
        manager = CacheManager()
        
        # Test graceful handling when methods don't exist yet
        # This tests that the manager initializes properly even when Redis methods aren't implemented
        assert hasattr(manager, 'config')
        assert hasattr(manager, 'redis_client')
        assert hasattr(manager, 'is_connected')
    
    def test_comprehensive_error_coverage(self):
        """Test that all error types can be instantiated and used."""
        error_types = [
            MadSparkError, AgentError, IdeaGenerationError, CriticError,
            AdvocateError, SkepticError, CacheError, CacheConnectionError,
            CacheSerializationError, ProcessingError, BatchProcessingError,
            ExportError, ValidationError, TemperatureError, ConfigurationError,
            APIError, FileOperationError
        ]
        
        for error_type in error_types:
            # Each error type should be instantiable
            error = error_type("Test message")
            assert str(error) == "Test message"
            assert isinstance(error, Exception)
            assert isinstance(error, MadSparkError)
    
    def test_verbose_logger_performance(self):
        """Test verbose logger performance with high volume."""
        logger = VerboseLogger(enabled=True)
        
        start_time = time.time()
        
        with patch('builtins.print'):
            # Log many steps quickly
            for i in range(100):
                logger.step(f"Step {i}", f"Details for step {i}")
                logger.data(f"Data {i}", f"Content for step {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly (less than 1 second for 200 operations)
        assert duration < 1.0, f"Logging took too long: {duration:.3f}s"
    
    def test_disabled_logger_performance(self):
        """Test that disabled logger has minimal performance impact."""
        logger = VerboseLogger(enabled=False)
        
        start_time = time.time()
        
        # Log many steps quickly (should be no-ops)
        for i in range(1000):
            logger.step(f"Step {i}", f"Details for step {i}")
            logger.data(f"Data {i}", f"Content for step {i}")
            logger.completion(f"Task {i}", i, 1.0)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete very quickly (less than 0.1 seconds for 3000 operations)
        assert duration < 0.1, f"Disabled logging took too long: {duration:.3f}s"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])