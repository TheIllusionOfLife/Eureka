## Description
<!-- Provide a brief description of the changes in this PR -->

## Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧹 Code refactoring
- [ ] 🧪 Test improvements
- [ ] 🔧 Configuration changes

## Size Check
<!-- Our PR size limits help ensure quality reviews -->
- [ ] This PR has **20 or fewer files** changed
- [ ] This PR has **500 or fewer lines** changed
- [ ] If exceeding limits, I've explained why it cannot be split

## Pre-Submission Checklist
<!-- Ensure you've completed all items before submitting -->
- [ ] I've run `./scripts/validate_pr.sh` and all checks pass
- [ ] Mock mode works without API keys: `MADSPARK_MODE=mock python -m madspark.cli.cli "test" "test"`
- [ ] All tests pass: `PYTHONPATH=src pytest tests/`
- [ ] No deprecated syntax (e.g., `docker-compose` → `docker compose`)
- [ ] Pre-commit hooks pass: `pre-commit run --all-files`
- [ ] I've added tests for new functionality
- [ ] I've updated documentation if needed

## Testing
<!-- Describe the tests you ran to verify your changes -->
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Screenshots/recordings attached (for UI changes)

## Performance Impact
<!-- Describe any performance implications -->
- [ ] No performance impact expected
- [ ] Performance improved (provide metrics)
- [ ] Performance may degrade (explain why it's acceptable)

## Security Considerations
<!-- Have you considered security implications? -->
- [ ] No security implications
- [ ] Security review needed (explain why)
- [ ] Sensitive data handling reviewed

## Related Issues
<!-- Link any related issues -->
Closes #

## Additional Context
<!-- Add any other context or screenshots about the PR here -->

## Post-Merge Actions
<!-- What needs to happen after merge? -->
- [ ] No additional actions needed
- [ ] Update production configuration
- [ ] Run post-merge validation: `./scripts/post_merge_validation.sh`
- [ ] Other: <!-- specify -->

---
<!-- 
Remember: Large PRs are harder to review and more likely to introduce bugs.
If this PR is large, consider splitting it into smaller, focused changes.
-->