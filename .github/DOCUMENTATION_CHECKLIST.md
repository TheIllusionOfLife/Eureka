# Documentation Update Checklist

This checklist prevents documentation regression issues like outdated "Known Issues" being accidentally reintroduced.

## Before Updating README Session Handover

### ✅ Pre-Update Verification (MANDATORY)

1. **Check Current Known Issues Status**
   ```bash
   # Verify if listed issues are still open
   grep -A 10 "Known Issues" README.md

   # Cross-reference with recent PRs
   gh pr list --state merged --limit 20 --json number,title,mergedAt
   ```

2. **Verify Issue Resolution**
   - [ ] For each issue in "Known Issues" section, confirm it's NOT already fixed
   - [ ] Check if issue was resolved in recent PRs (last 30 days)
   - [ ] Review `docs/archive/completed-plans/` for fixed issues

3. **Review Template Source**
   - [ ] If copying from previous session handover, verify it's the MOST RECENT version
   - [ ] Check git history: `git log --oneline README.md | head -5`
   - [ ] Never copy from commits older than 1 week without verification

### ✅ Update Process

1. **Update Session Handover**
   - [ ] Add NEW content (Recently Completed, Session Learnings)
   - [ ] Update "Next Priority Tasks" based on current sprint
   - [ ] DO NOT copy "Known Issues" section blindly

2. **Known Issues Section Management**
   - [ ] If adding a new issue, verify it's not fixed in recent commits
   - [ ] If keeping an existing issue, verify it's still open
   - [ ] If removing an issue, note the PR number that fixed it
   - [ ] **Default**: If unsure, mark as "None currently" and investigate

3. **Testing Tasks Section**
   - [ ] Mark completed tests as ✅ COMPLETE
   - [ ] Remove "Blocker" references if bugs are fixed
   - [ ] Update status based on actual test results, not assumptions

### ✅ Post-Update Verification

1. **Cross-Reference Check**
   ```bash
   # Verify issues mentioned are real
   grep -E "PR #[0-9]+" README.md | sort -u

   # Check if mentioned PRs exist
   gh pr view <PR_NUMBER> --json state,title
   ```

2. **Archive Old Issues**
   - [ ] Move resolved issues to `docs/archive/completed-plans/`
   - [ ] Update references to point to archived location

## Common Mistakes to Avoid

### ❌ **NEVER Do This**
1. Copy entire "Known Issues" section from old session handover without verification
2. Reference PR numbers without checking if they're merged/closed
3. List bugs as "discovered in PR #X" without checking if fixed in PR #X+1
4. Keep "Blocker" or "prevents full testing" statements after blocker is removed

### ✅ **ALWAYS Do This**
1. Read the actual current README before updating
2. Verify each bullet point in "Known Issues" is still valid
3. Check recent PRs for fixes: `gh pr list --state merged --limit 10`
4. When in doubt, set "Known Issues" to "None currently" and investigate

## Automation Helpers

### Quick Validation Script
```bash
# Run before committing README changes
./scripts/validate_readme.sh

# This script checks:
# - No references to fixed bugs
# - All PR numbers exist
# - Known Issues section is up-to-date
```

## Issue Lifecycle

1. **Issue Discovered** → Add to "Known Issues" with discovery date
2. **Fix PR Created** → Note PR number in issue description
3. **Fix PR Merged** → Move issue to "Completed Testing Tasks" or remove entirely
4. **Next Session Update** → Archive to `docs/archive/completed-plans/`

## Session Handover Best Practices

### Template Structure
```markdown
## Session Handover

### Last Updated: [DATE]

### Recently Completed
- ✅ [Recent work with PR numbers and dates]

### Next Priority Tasks
1. [Task based on current state, not old template]

### Known Issues / Blockers
**None currently**: [Or list verified current issues]

### Session Learnings
##### From PR #XXX ([Title])
- [New learnings only]
```

## Emergency Checklist (If You Find a Documentation Bug)

1. [ ] Identify when the incorrect information was introduced: `git log -p README.md`
2. [ ] Check if it was a copy-paste from older version: `git diff <old> <new> README.md`
3. [ ] Fix the immediate issue in README
4. [ ] Create script/check to prevent recurrence
5. [ ] Update this checklist with new prevention measure

## References

- **Incident Report**: See PR #186 for the case study of outdated "Known Issues" reintroduction
- **Fix Example**: PR #161 (Aug 2025) fixed bug but was incorrectly listed as open in Nov 2025 docs
- **Root Cause**: Template copying during Phase 3 refactoring sessions (Nov 6-9, 2025)

---

**Last Updated**: November 9, 2025
**Next Review**: Every major documentation update
