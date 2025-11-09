"""Test to prevent regression of workflow_orchestrator export structure.

This test verifies that workflow_orchestrator correctly exports the functions
that test mocks depend on. This prevents future architectural changes from
breaking mock targets again (as happened post-PR#182).

Related PR: #188 - Fixed 40+ integration test failures due to mock target changes
"""


class TestWorkflowOrchestratorExports:
    """Verify workflow_orchestrator exports expected functions for test mocking."""

    def test_workflow_orchestrator_exports_retry_wrappers(self):
        """Verify workflow_orchestrator exports retry-wrapped agent functions.

        These exports are critical for test mocking. Tests must patch functions
        where they are imported (workflow_orchestrator), not where they're defined
        (agent_retry_wrappers).
        """
        from madspark.core import workflow_orchestrator

        # Critical retry wrapper exports that tests depend on
        assert hasattr(workflow_orchestrator, 'call_idea_generator_with_retry'), \
            "Missing call_idea_generator_with_retry export - tests will break"
        assert hasattr(workflow_orchestrator, 'call_critic_with_retry'), \
            "Missing call_critic_with_retry export - tests will break"

    def test_workflow_orchestrator_exports_batch_functions(self):
        """Verify workflow_orchestrator exports batch processing functions.

        These exports are critical for test mocking. Tests must patch batch functions
        where they are imported (workflow_orchestrator), not where they're defined
        (individual agent modules).
        """
        from madspark.core import workflow_orchestrator

        # Critical batch function exports that tests depend on
        assert hasattr(workflow_orchestrator, 'advocate_ideas_batch'), \
            "Missing advocate_ideas_batch export - tests will break"
        assert hasattr(workflow_orchestrator, 'criticize_ideas_batch'), \
            "Missing criticize_ideas_batch export - tests will break"
        assert hasattr(workflow_orchestrator, 'improve_ideas_batch'), \
            "Missing improve_ideas_batch export - tests will break"

    def test_workflow_orchestrator_exports_are_callable(self):
        """Verify exported functions are actually callable (not None or broken imports)."""
        from madspark.core import workflow_orchestrator

        # Verify functions are callable
        assert callable(workflow_orchestrator.call_idea_generator_with_retry), \
            "call_idea_generator_with_retry is not callable"
        assert callable(workflow_orchestrator.call_critic_with_retry), \
            "call_critic_with_retry is not callable"
        assert callable(workflow_orchestrator.advocate_ideas_batch), \
            "advocate_ideas_batch is not callable"
        assert callable(workflow_orchestrator.criticize_ideas_batch), \
            "criticize_ideas_batch is not callable"
        assert callable(workflow_orchestrator.improve_ideas_batch), \
            "improve_ideas_batch is not callable"

    def test_mock_target_pattern_documented(self):
        """Document the correct mock target pattern to prevent future regressions.

        This test serves as documentation for the correct mock pattern established
        in PR #182 and fixed in PR #188.
        """
        # CORRECT mock pattern (post-PR#182):
        # @patch('madspark.core.workflow_orchestrator.call_idea_generator_with_retry')

        # INCORRECT mock pattern (pre-PR#182, breaks after PR#182):
        # @patch('madspark.utils.agent_retry_wrappers.call_idea_generator_with_retry')

        # Why: PR #182 refactored workflow functions as module-level variables
        # in workflow_orchestrator.py, so mocks must target the import location,
        # not the definition location.

        # This test just documents the pattern - actual verification is in the
        # export tests above.
        assert True, "Mock target pattern documented"
