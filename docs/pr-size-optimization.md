# PR Size Optimization Guide

Guide for keeping pull requests within size limits while maintaining logical coherence.

## Size Limits

Current PR limits enforced by CI:
- **Maximum Files**: 20
- **Maximum Lines Added**: 500
- **Warning Threshold**: 300 lines

## Why Size Matters

Small PRs provide:
- **Faster Reviews**: Reviewers can thoroughly examine changes
- **Reduced Risk**: Smaller changes have fewer potential issues
- **Better Context**: Easier to understand the purpose
- **Quick Iterations**: Faster merge cycles
- **Clearer History**: Git history remains readable

## Strategies for Size Optimization

### 1. Single Responsibility
Each PR should have ONE clear purpose:
- ✅ "Fix authentication bug"
- ✅ "Add user profile feature"
- ❌ "Fix bugs and add features"

### 2. Incremental Changes
Break large features into steps:
```
PR #1: Add database schema
PR #2: Implement API endpoints
PR #3: Add frontend components
PR #4: Wire up integration
```

### 3. Separate Concerns
Split different types of changes:
- **Refactoring**: Separate PR from feature work
- **Tests**: Can be a dedicated PR
- **Documentation**: Often merits its own PR
- **Dependencies**: Update in isolated PR

## Techniques for Splitting PRs

### 1. Feature Flags
Implement partial features safely:
```python
if settings.FEATURE_NEW_DASHBOARD:
    # New implementation
else:
    # Existing implementation
```

### 2. Backend-First Approach
1. PR #1: API endpoints (can be tested with curl)
2. PR #2: Frontend implementation
3. PR #3: Integration and polish

### 3. Vertical Slicing
Complete thin slices of functionality:
- PR #1: Basic CRUD for one entity
- PR #2: Add validation and error handling
- PR #3: Add advanced features

### 4. Horizontal Slicing
Layer by layer approach:
- PR #1: Data models and migrations
- PR #2: Business logic layer
- PR #3: API layer
- PR #4: UI layer

## Managing Large Changes

### 1. Create a Tracking Issue
```markdown
## Feature: User Dashboard Redesign

- [ ] PR #1: Update data models (#101)
- [ ] PR #2: New API endpoints (#102)
- [ ] PR #3: React components (#103)
- [ ] PR #4: Integration & testing (#104)
```

### 2. Use Feature Branches
```bash
# Main feature branch
git checkout -b feature/dashboard-redesign

# Sub-feature branches
git checkout -b feature/dashboard-models
git checkout -b feature/dashboard-api
git checkout -b feature/dashboard-ui
```

### 3. Stacked PRs
Create PRs that build on each other:
```
main
  └── PR #1: Database changes
       └── PR #2: API changes (targets PR #1)
            └── PR #3: UI changes (targets PR #2)
```

## File Organization Tips

### 1. Group Related Files
Keep related changes together:
```
src/
  features/
    auth/
      models.py    # All auth changes
      views.py     # in one PR
      tests.py
```

### 2. Avoid Scatter
Don't touch unrelated files:
- ❌ Formatting changes in unrelated files
- ❌ "While I'm here" fixes
- ❌ Unrelated refactoring

### 3. Use .gitignore
Exclude generated or temporary files:
```gitignore
# Generated files
*.pyc
__pycache__/
build/
dist/

# IDE files
.vscode/
.idea/
```

## Measuring PR Size

### Check Before Pushing
```bash
# See what will be in the PR
git diff main... --stat

# Count files
git diff main... --name-only | wc -l

# Count lines
git diff main... --numstat | awk '{added+=$1; deleted+=$2} END {print "+" added " -" deleted}'
```

### Use Validation Script
```bash
./scripts/validate_pr.sh
```

## Common Patterns

### 1. The Setup PR
First PR establishes structure:
```
- Create directory structure
- Add configuration files
- Set up build process
- Add README
```

### 2. The Implementation PR
Core functionality:
```
- Business logic
- Main algorithms
- Core features
```

### 3. The Polish PR
Final touches:
```
- Error handling
- Logging
- Performance optimization
- Edge cases
```

### 4. The Test PR
Comprehensive testing:
```
- Unit tests
- Integration tests
- Test fixtures
- CI configuration
```

## PR Size Override

When size limits must be exceeded:

1. Add to PR description:
```markdown
SIZE_LIMIT_OVERRIDE: Importing vendored library

This PR imports the XYZ library which requires all files to be added together.
Files are all in `vendor/xyz/` and no review of individual lines is needed.
```

2. Justify the override:
- Large refactoring that must be atomic
- Vendored dependencies
- Generated code that must stay together
- Moving files (shows as add+delete)

## Review Considerations

### For Authors
- Make PR description comprehensive
- Add screenshots for UI changes
- Include testing instructions
- Link related issues/PRs
- Use draft PR for work-in-progress

### For Reviewers
- Focus on changes, not size
- Suggest further splitting if needed
- Approve logical chunks
- Don't penalize necessary size

## Examples

### Good PR Splits

**Authentication Feature**:
- PR #1: User model and migrations (50 lines)
- PR #2: Login/logout endpoints (150 lines)
- PR #3: JWT token handling (100 lines)
- PR #4: Frontend login form (200 lines)

**Bug Fix with Refactoring**:
- PR #1: Minimal bug fix (20 lines)
- PR #2: Refactor to prevent similar bugs (300 lines)
- PR #3: Add comprehensive tests (200 lines)

### Bad PR Examples

❌ **Kitchen Sink PR**:
- Bug fixes + new feature + refactoring + tests
- 50 files changed, 2000 lines

❌ **The Wanderer**:
- Started fixing one thing
- "Noticed" other issues
- Touched 30 unrelated files

❌ **The Monolith**:
- Entire feature in one PR
- 40 files, impossible to review

## Tooling

### Git Commands
```bash
# Interactive rebase to split commits
git rebase -i main

# Cherry-pick specific commits
git cherry-pick <commit-hash>

# Create patch files
git format-patch main
```

### GitHub CLI
```bash
# Create PR with specific base
gh pr create --base feature/main-feature

# Link PRs
gh pr edit --body "Depends on #123"
```

## Summary

Remember:
1. **Think Small**: Can this be smaller?
2. **Stay Focused**: One PR, one purpose
3. **Be Incremental**: Build in steps
4. **Consider Reviewers**: Make their job easy
5. **Document Well**: Explain your approach

Small PRs = Happy Reviewers = Fast Merges = Rapid Progress