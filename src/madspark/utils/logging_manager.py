"""Centralized logging configuration management.

This module provides standardized logging setup and management to eliminate
duplicate logging configuration across the codebase.
"""
import os
import logging
import datetime
from typing import Optional, Dict
from pathlib import Path


class LoggingManager:
    """Centralized logging configuration manager."""
    
    _configured_loggers: Dict[str, logging.Logger] = {}
    _file_handler: Optional[logging.FileHandler] = None
    _console_handler: Optional[logging.StreamHandler] = None
    
    @classmethod
    def setup_logging(
        cls, 
        verbose: bool = False, 
        log_file: Optional[str] = None,
        enable_file_logging: bool = True
    ) -> logging.Logger:
        """Configure standardized logging setup.
        
        Args:
            verbose: Enable verbose (DEBUG) logging
            log_file: Specific log file path (optional)
            enable_file_logging: Whether to enable file logging
            
        Returns:
            Configured root logger
        """
        # Determine log level
        log_level = logging.DEBUG if verbose else logging.INFO
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Create console handler
        if not cls._console_handler:
            cls._console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            cls._console_handler.setFormatter(console_formatter)
        
        cls._console_handler.setLevel(log_level)
        root_logger.addHandler(cls._console_handler)
        
        # Create file handler if requested
        if enable_file_logging:
            if not log_file:
                log_file = cls.create_timestamped_log_file()
            
            if log_file and not cls._file_handler:
                try:
                    # Ensure log directory exists
                    log_path = Path(log_file)
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    cls._file_handler = logging.FileHandler(log_file)
                    file_formatter = logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                    )
                    cls._file_handler.setFormatter(file_formatter)
                    cls._file_handler.setLevel(logging.DEBUG)  # Always capture debug in files
                    
                    root_logger.addHandler(cls._file_handler)
                    root_logger.info(f"File logging enabled: {log_file}")
                    
                except Exception as e:
                    root_logger.warning(f"Failed to setup file logging: {e}")
        
        return root_logger
    
    @classmethod
    def get_logger(cls, name: str, verbose: bool = False) -> logging.Logger:
        """Get a configured logger instance.
        
        Args:
            name: Logger name (usually __name__)
            verbose: Enable verbose logging for this logger
            
        Returns:
            Configured logger instance
        """
        if name not in cls._configured_loggers:
            logger = logging.getLogger(name)
            
            # Ensure proper level
            if verbose:
                logger.setLevel(logging.DEBUG)
            
            # Store in cache
            cls._configured_loggers[name] = logger
        
        return cls._configured_loggers[name]
    
    @classmethod
    def create_timestamped_log_file(cls, prefix: str = "madspark", directory: str = "logs") -> str:
        """Create timestamped log file path.
        
        Args:
            prefix: Log file prefix
            directory: Log directory name
            
        Returns:
            Full path to timestamped log file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{prefix}_{timestamp}.log"
        
        # Try different base directories
        possible_bases = [
            os.getcwd(),
            os.path.expanduser("~"),
            "/tmp"
        ]
        
        for base_dir in possible_bases:
            try:
                log_dir = os.path.join(base_dir, directory)
                os.makedirs(log_dir, exist_ok=True)
                
                # Test write permissions
                test_file = os.path.join(log_dir, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                
                return os.path.join(log_dir, log_filename)
                
            except (OSError, PermissionError):
                continue
        
        # Fallback to current directory
        try:
            os.makedirs(directory, exist_ok=True)
            return os.path.join(directory, log_filename)
        except (OSError, PermissionError):
            # Last resort - return just filename (will use current directory)
            return log_filename
    
    @classmethod
    def setup_agent_logging(cls, agent_name: str, verbose: bool = False) -> logging.Logger:
        """Setup logging specifically for agent modules.
        
        Args:
            agent_name: Name of the agent
            verbose: Enable verbose logging
            
        Returns:
            Configured logger for the agent
        """
        logger_name = f"madspark.agents.{agent_name}"
        logger = cls.get_logger(logger_name, verbose)
        
        # Set specific agent logging preferences
        if verbose:
            logger.debug(f"Verbose logging enabled for {agent_name} agent")
        
        return logger
    
    @classmethod
    def setup_coordinator_logging(cls, coordinator_type: str, verbose: bool = False) -> logging.Logger:
        """Setup logging specifically for coordinator modules.
        
        Args:
            coordinator_type: Type of coordinator (sync/async/batch)
            verbose: Enable verbose logging
            
        Returns:
            Configured logger for the coordinator
        """
        logger_name = f"madspark.core.{coordinator_type}_coordinator"
        logger = cls.get_logger(logger_name, verbose)
        
        if verbose:
            logger.debug(f"Verbose logging enabled for {coordinator_type} coordinator")
        
        return logger
    
    @classmethod
    def setup_cli_logging(cls, verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
        """Setup logging specifically for CLI operations.
        
        Args:
            verbose: Enable verbose logging
            log_file: Optional log file path
            
        Returns:
            Configured logger for CLI
        """
        # Setup base logging
        root_logger = cls.setup_logging(verbose, log_file, enable_file_logging=bool(log_file))
        
        # Get CLI-specific logger
        cli_logger = cls.get_logger("madspark.cli", verbose)
        
        if verbose:
            cli_logger.debug("CLI verbose logging enabled")
        
        return cli_logger
    
    @classmethod
    def configure_suppressed_loggers(cls, suppress_below: str = "WARNING"):
        """Configure suppressed logging for noisy third-party modules.
        
        Args:
            suppress_below: Log level below which to suppress messages
        """
        suppress_level = getattr(logging, suppress_below.upper(), logging.WARNING)
        
        # Common noisy modules
        noisy_modules = [
            'urllib3.connectionpool',
            'requests.packages.urllib3',
            'httpcore.connection',
            'httpx._client'
        ]
        
        for module in noisy_modules:
            logger = logging.getLogger(module)
            logger.setLevel(suppress_level)
    
    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """Get current log file path if file logging is enabled.
        
        Returns:
            Path to current log file or None
        """
        if cls._file_handler:
            return cls._file_handler.baseFilename
        return None
    
    @classmethod
    def close_handlers(cls):
        """Close all logging handlers (useful for testing)."""
        if cls._file_handler:
            cls._file_handler.close()
            cls._file_handler = None
        
        if cls._console_handler:
            cls._console_handler.close()
            cls._console_handler = None
        
        cls._configured_loggers.clear()
    
    @classmethod
    def reset(cls):
        """Reset logging configuration (useful for testing)."""
        cls.close_handlers()
        
        # Reset root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)


# Convenience functions for backward compatibility
def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """Convenience function for setting up logging."""
    return LoggingManager.setup_logging(verbose, log_file)


def get_logger(name: str, verbose: bool = False) -> logging.Logger:
    """Convenience function for getting a logger."""
    return LoggingManager.get_logger(name, verbose)