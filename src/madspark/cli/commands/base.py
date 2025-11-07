"""Base class for CLI command handlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import argparse
import logging


@dataclass
class CommandResult:
    """Result of command execution.

    Attributes:
        success: Whether the command executed successfully
        exit_code: Exit code for the command (0 for success, non-zero for failure)
        message: Optional message about the execution
        data: Optional data payload returned by the command
    """
    success: bool
    exit_code: int = 0
    message: Optional[str] = None
    data: Optional[Any] = None


class CommandHandler(ABC):
    """Abstract base class for command handlers.

    All command handlers should inherit from this class and implement
    the execute() method to define their specific behavior.
    """

    def __init__(self, args: argparse.Namespace, logger: logging.Logger):
        """Initialize command handler.

        Args:
            args: Parsed command-line arguments
            logger: Logger instance for the handler
        """
        self.args = args
        self.logger = logger

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command.

        Returns:
            CommandResult with success status and optional data
        """
        pass

    def log_info(self, message: str) -> None:
        """Log info message.

        Args:
            message: Message to log
        """
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        """Log error message.

        Args:
            message: Message to log
        """
        self.logger.error(message)

    def log_warning(self, message: str) -> None:
        """Log warning message.

        Args:
            message: Message to log
        """
        self.logger.warning(message)
