# Workflow Improvements from PR #117 Postmortem

## Quick Reference: Preventing Long PR Cycles

### 1. Start Small, Stay Focused
- Define 3-5 acceptance criteria upfront
- Create "scope contract" in PR description
- Defer nice-to-haves to follow-up issues

### 2. Pre-Push Checklist
```bash
# Run before EVERY push
ruff check src/ tests/ web/backend/
mypy src/ --ignore-missing-imports  
PYTHONPATH=src pytest tests/ -x
cd web/frontend && npm run typecheck && cd ../..
```

### 3. Review Bot Patterns to Avoid
- **Security**: Exposed passwords → Use `read -s`
- **Shell**: Missing `-r` flag → Use `read -r`
- **Python**: Unused imports → Remove immediately
- **TypeScript**: Type errors → Run tsc after changes
- **Tests**: pytest.skip() → Use real assertions

### 4. TDD Best Practices
- Write minimal test that fails
- Implement minimal code to pass
- Refactor only after green
- Avoid placeholder tests

### 5. Integration Points Checklist
- [ ] Frontend/backend field names match
- [ ] CLI arguments have backward compatibility
- [ ] Documentation reflects actual behavior
- [ ] Mock mode works without API keys

## Metrics to Track
- Commits per PR (target: < 15)
- Fix commits ratio (target: < 30%)
- Review cycles (target: 1-2)
- Time to merge (target: < 1 day)

## Session Handover Template
```markdown
### PR #X Status
- Acceptance criteria: [list]
- Completed: [X/Y]
- Blocking issues: [list]
- Next action: [specific task]
```