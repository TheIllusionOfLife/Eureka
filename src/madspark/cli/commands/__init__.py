"""Command handlers for MadSpark CLI.

This package contains modular command handlers extracted from the monolithic
main() function to improve maintainability and testability.
"""

from .base import CommandHandler, CommandResult

__all__ = [
    'CommandHandler',
    'CommandResult',
]

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy import of command handlers."""
    if name == 'WorkflowValidator':
        from .validation import WorkflowValidator
        return WorkflowValidator
    elif name == 'WorkflowExecutor':
        from .workflow_executor import WorkflowExecutor
        return WorkflowExecutor
    elif name == 'BatchHandler':
        from .batch_handler import BatchHandler
        return BatchHandler
    elif name == 'BookmarkHandler':
        from .bookmark_handler import BookmarkHandler
        return BookmarkHandler
    elif name == 'ExportHandler':
        from .export_handler import ExportHandler
        return ExportHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
