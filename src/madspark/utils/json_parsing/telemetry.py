"""Telemetry for JSON parsing strategy effectiveness.

This module provides tracking and analytics for JSON parsing strategy usage.
It helps identify:
- Which fallback strategies are actually used in production
- Performance characteristics of each strategy
- Potential dead code (unused strategies)
- Optimization opportunities

The telemetry data is valuable for data-driven decisions about:
- Removing unnecessary fallback strategies
- Optimizing the strategy execution order
- Identifying problematic input patterns
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ParsingTelemetry:
    """Track which parsing strategies succeed in production.

    This class provides lightweight telemetry for understanding JSON parsing
    behavior without performance overhead. All operations are simple
    dictionary updates and logging calls.

    Attributes:
        strategy_counts: Dictionary mapping strategy names to success counts

    Example:
        >>> telemetry = ParsingTelemetry()
        >>> telemetry.record_success("DirectJson", input_length=250)
        >>> telemetry.record_failure("RegexExtraction", "Pattern didn't match")
        >>> stats = telemetry.get_stats()
        >>> print(f"DirectJson used {stats['DirectJson']} times")
    """

    def __init__(self):
        """Initialize telemetry with empty counters."""
        self.strategy_counts: Dict[str, int] = {}

    def record_success(self, strategy_name: str, input_length: int) -> None:
        """Record successful parse via specific strategy.

        Args:
            strategy_name: Name of the strategy that succeeded
            input_length: Length of input text in characters

        Side Effects:
            - Increments counter for this strategy
            - Logs debug message with strategy name and input length
        """
        logger.debug(
            f"JSON parsing succeeded via {strategy_name} (input: {input_length} chars)"
        )
        self.strategy_counts[strategy_name] = (
            self.strategy_counts.get(strategy_name, 0) + 1
        )

    def record_failure(self, strategy_name: str, error: str) -> None:
        """Record parsing failure.

        Args:
            strategy_name: Name of the strategy that failed
            error: Description of the failure

        Side Effects:
            - Logs warning message
            - Does NOT increment counters (only successes are counted)

        Note:
            Failures are logged for debugging but not counted in statistics.
            This keeps stats focused on which strategies actually work.
        """
        logger.warning(f"JSON parsing failed at {strategy_name}: {error}")

    def get_stats(self) -> Dict[str, int]:
        """Get summary statistics of strategy usage.

        Returns:
            Dictionary with strategy names as keys, counts as values,
            plus a 'total' key with the sum of all counts.

        Example:
            >>> stats = telemetry.get_stats()
            >>> stats
            {'DirectJson': 85, 'LineByLine': 12, 'RegexExtraction': 3, 'total': 100}
        """
        stats = dict(self.strategy_counts)
        stats['total'] = sum(self.strategy_counts.values())
        return stats

    def reset(self) -> None:
        """Clear all strategy counts.

        Useful for:
        - Starting fresh telemetry collection
        - Testing
        - Periodic resets in long-running processes
        """
        self.strategy_counts.clear()
