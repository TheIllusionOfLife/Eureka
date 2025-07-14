"""Custom Error Classes for MadSpark Multi-Agent System.

This module defines custom exception classes for better error handling
and categorization across the MadSpark system.
"""


class MadSparkError(Exception):
    """Base exception class for all MadSpark errors."""
    pass


class AgentError(MadSparkError):
    """Base exception for agent-related errors."""
    pass


class IdeaGenerationError(AgentError):
    """Exception raised when idea generation fails."""
    pass


class CriticError(AgentError):
    """Exception raised when critique process fails."""
    pass


class AdvocateError(AgentError):
    """Exception raised when advocacy process fails."""
    pass


class SkepticError(AgentError):
    """Exception raised when skeptical analysis fails."""
    pass


class CacheError(MadSparkError):
    """Base exception for cache-related errors."""
    pass


class CacheConnectionError(CacheError):
    """Exception raised when cache connection fails."""
    pass


class CacheSerializationError(CacheError):
    """Exception raised when cache serialization fails."""
    pass


class ProcessingError(MadSparkError):
    """Base exception for processing-related errors."""
    pass


class BatchProcessingError(ProcessingError):
    """Exception raised when batch processing fails."""
    pass


class ExportError(ProcessingError):
    """Exception raised when export operations fail."""
    pass


class ValidationError(MadSparkError):
    """Exception raised when input validation fails."""
    pass


class TemperatureError(ValidationError):
    """Exception raised when temperature validation fails."""
    pass


class ConfigurationError(MadSparkError):
    """Exception raised when configuration is invalid."""
    pass


class APIError(MadSparkError):
    """Exception raised when external API calls fail."""
    pass


class FileOperationError(MadSparkError):
    """Exception raised when file operations fail."""
    pass