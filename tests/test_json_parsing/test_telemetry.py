"""Tests for JSON parsing telemetry.

Following TDD: These tests are written BEFORE implementation.
They will fail until telemetry.py is created.
"""

import logging


class TestParsingTelemetry:
    """Test telemetry tracking for parsing strategy usage."""

    def test_telemetry_init_creates_empty_counts(self):
        """New telemetry should have empty strategy counts."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        assert hasattr(telemetry, 'strategy_counts')
        assert isinstance(telemetry.strategy_counts, dict)
        assert len(telemetry.strategy_counts) == 0

    def test_record_success_tracks_strategy_name(self):
        """Recording success should increment count for strategy."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)

        assert "DirectJson" in telemetry.strategy_counts
        assert telemetry.strategy_counts["DirectJson"] == 1

    def test_record_success_increments_existing_count(self):
        """Recording multiple successes should increment count."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)
        telemetry.record_success("DirectJson", 200)
        telemetry.record_success("DirectJson", 150)

        assert telemetry.strategy_counts["DirectJson"] == 3

    def test_record_success_tracks_multiple_strategies(self):
        """Should track different strategies separately."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)
        telemetry.record_success("LineByLine", 200)
        telemetry.record_success("DirectJson", 150)
        telemetry.record_success("RegexExtraction", 300)

        assert telemetry.strategy_counts["DirectJson"] == 2
        assert telemetry.strategy_counts["LineByLine"] == 1
        assert telemetry.strategy_counts["RegexExtraction"] == 1

    def test_record_success_logs_debug_message(self, caplog):
        """Should log debug message on successful parse."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()

        with caplog.at_level(logging.DEBUG):
            telemetry.record_success("DirectJson", 250)

        # Check that debug log was created
        assert len(caplog.records) > 0
        assert "DirectJson" in caplog.text
        assert "250" in caplog.text

    def test_record_failure_logs_warning(self, caplog):
        """Should log warning on parsing failure."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()

        with caplog.at_level(logging.WARNING):
            telemetry.record_failure("DirectJson", "Invalid JSON syntax")

        # Check that warning was logged
        assert len(caplog.records) > 0
        assert caplog.records[0].levelname == "WARNING"
        assert "DirectJson" in caplog.text
        assert "Invalid JSON syntax" in caplog.text

    def test_record_failure_does_not_increment_counts(self):
        """Failures should not be counted in strategy_counts."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)
        telemetry.record_failure("DirectJson", "Some error")

        # Count should still be 1 (only success counted)
        assert telemetry.strategy_counts["DirectJson"] == 1

    def test_get_stats_returns_strategy_summary(self):
        """Should provide summary statistics of strategy usage."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)
        telemetry.record_success("DirectJson", 150)
        telemetry.record_success("LineByLine", 200)

        stats = telemetry.get_stats()
        assert isinstance(stats, dict)
        assert stats["DirectJson"] == 2
        assert stats["LineByLine"] == 1
        assert stats["total"] == 3

    def test_get_stats_returns_empty_when_no_data(self):
        """Stats should be empty when no parsing has occurred."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        stats = telemetry.get_stats()

        assert isinstance(stats, dict)
        assert stats["total"] == 0

    def test_reset_clears_all_counts(self):
        """Reset should clear all strategy counts."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()
        telemetry.record_success("DirectJson", 100)
        telemetry.record_success("LineByLine", 200)

        telemetry.reset()

        assert len(telemetry.strategy_counts) == 0
        assert telemetry.get_stats()["total"] == 0


class TestTelemetryIntegration:
    """Integration tests for telemetry in parsing workflows."""

    def test_telemetry_tracks_fallback_chain_usage(self):
        """Should track which fallback strategies are actually used."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()

        # Simulate a parsing workflow that tries multiple strategies
        telemetry.record_failure("DirectJson", "Invalid JSON")
        telemetry.record_failure("JsonArrayExtraction", "No arrays found")
        telemetry.record_success("LineByLine", 500)

        # Only LineByLine should be in success counts
        assert "LineByLine" in telemetry.strategy_counts
        assert "DirectJson" not in telemetry.strategy_counts
        assert telemetry.strategy_counts["LineByLine"] == 1

    def test_telemetry_helps_identify_performance_bottlenecks(self):
        """Stats should reveal which strategies are most/least used."""
        from madspark.utils.json_parsing.telemetry import ParsingTelemetry

        telemetry = ParsingTelemetry()

        # Simulate pattern: DirectJson works 80% of the time, fallbacks 20%
        for _ in range(80):
            telemetry.record_success("DirectJson", 100)

        for _ in range(15):
            telemetry.record_success("LineByLine", 200)

        for _ in range(5):
            telemetry.record_success("RegexExtraction", 300)

        stats = telemetry.get_stats()

        # DirectJson should be the most common (hot path)
        assert stats["DirectJson"] == 80
        assert stats["LineByLine"] == 15
        assert stats["RegexExtraction"] == 5
        assert stats["total"] == 100

        # This data helps identify that DirectJson is working well
        # and RegexExtraction is rarely needed (potential dead code)
