"""Custom exceptions for batch API operations.

This module defines specific exception types for different batch failure modes,
improving error handling and debugging capabilities.
"""

from typing import Optional, Dict, Any


class BatchOperationError(Exception):
    """Base exception for all batch operation errors."""
    
    def __init__(self, message: str, batch_type: str, items_count: int = 0, details: Optional[Dict[str, Any]] = None):
        """Initialize batch operation error.
        
        Args:
            message: Error message
            batch_type: Type of batch operation (advocate, skeptic, improve, etc.)
            items_count: Number of items in the failed batch
            details: Additional error details
        """
        super().__init__(message)
        self.batch_type = batch_type
        self.items_count = items_count
        self.details = details or {}


class BatchAPIError(BatchOperationError):
    """Exception raised when the batch API call fails."""
    pass


class BatchParsingError(BatchOperationError):
    """Exception raised when parsing batch API response fails."""
    
    def __init__(self, message: str, batch_type: str, items_count: int = 0, 
                 raw_response: Optional[str] = None, parse_error: Optional[Exception] = None):
        """Initialize batch parsing error.
        
        Args:
            message: Error message
            batch_type: Type of batch operation
            items_count: Number of items in the batch
            raw_response: The raw API response that failed to parse
            parse_error: The underlying parsing exception
        """
        details = {}
        if raw_response:
            details["raw_response"] = raw_response[:500]  # Truncate for safety
        if parse_error:
            details["parse_error"] = str(parse_error)
        
        super().__init__(message, batch_type, items_count, details)
        self.raw_response = raw_response
        self.parse_error = parse_error


class BatchValidationError(BatchOperationError):
    """Exception raised when batch response validation fails."""
    
    def __init__(self, message: str, batch_type: str, items_count: int = 0,
                 expected_count: Optional[int] = None, actual_count: Optional[int] = None):
        """Initialize batch validation error.
        
        Args:
            message: Error message
            batch_type: Type of batch operation
            items_count: Number of items in the batch
            expected_count: Expected number of responses
            actual_count: Actual number of responses received
        """
        details = {}
        if expected_count is not None:
            details["expected_count"] = expected_count
        if actual_count is not None:
            details["actual_count"] = actual_count
            
        super().__init__(message, batch_type, items_count, details)
        self.expected_count = expected_count
        self.actual_count = actual_count


class BatchTimeoutError(BatchOperationError):
    """Exception raised when batch operation times out."""
    
    def __init__(self, message: str, batch_type: str, items_count: int = 0, timeout_seconds: Optional[float] = None):
        """Initialize batch timeout error.
        
        Args:
            message: Error message
            batch_type: Type of batch operation
            items_count: Number of items in the batch
            timeout_seconds: Timeout duration in seconds
        """
        details = {}
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
            
        super().__init__(message, batch_type, items_count, details)
        self.timeout_seconds = timeout_seconds


class BatchRateLimitError(BatchOperationError):
    """Exception raised when hitting API rate limits."""
    
    def __init__(self, message: str, batch_type: str, items_count: int = 0, 
                 retry_after: Optional[int] = None, rate_limit_info: Optional[Dict[str, Any]] = None):
        """Initialize batch rate limit error.
        
        Args:
            message: Error message
            batch_type: Type of batch operation
            items_count: Number of items in the batch
            retry_after: Seconds to wait before retrying (from API response)
            rate_limit_info: Additional rate limit information from API
        """
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        if rate_limit_info:
            details["rate_limit_info"] = rate_limit_info
            
        super().__init__(message, batch_type, items_count, details)
        self.retry_after = retry_after
        self.rate_limit_info = rate_limit_info