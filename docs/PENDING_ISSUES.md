# Pending Issues from Code Reviews

This document tracks issues identified by automated reviewers that need to be addressed in future PRs.

## High Priority Issues

### 1. CLI Timeout Argument Not Utilized
- **Source**: cursor[bot] review on PR #78
- **Severity**: HIGH
- **Location**: `mad_spark_multiagent/cli.py#L245-L252`
- **Description**: The `--timeout` CLI argument is accepted by the parser but its value is not utilized during workflow execution
- **Impact**: Users can specify timeout values but they have no effect on execution
- **Proposed Fix**:
  ```python
  # In cli.py, pass timeout to workflow_kwargs
  workflow_kwargs = {
      'temperature': args.temperature,
      'timeout': args.timeout,  # Add this line
      # ... other kwargs
  }
  
  # In coordinator.py, implement timeout handling
  if timeout:
      result = await asyncio.wait_for(
          self._run_workflow_async(),
          timeout=timeout
      )
  ```

## Medium Priority Issues

### 2. TypeScript/Python Regex Pattern Divergence
- **Source**: cursor[bot] review on PR #78
- **Severity**: MEDIUM
- **Location**: `web/frontend/src/utils/ideaCleaner.ts#L41-L75`
- **Description**: Regex patterns are hardcoded in TypeScript while Python imports from constants
- **Impact**: Pattern updates in Python won't reflect in TypeScript, causing inconsistent cleaning
- **Proposed Fix**:
  1. Export patterns from `constants.ts`
  2. Import in `ideaCleaner.ts`
  3. Ensure pattern parity with Python implementation
  ```typescript
  // constants.ts
  export const CLEANER_REPLACEMENT_PATTERNS = [
    // ... patterns matching Python constants
  ];
  
  // ideaCleaner.ts
  import { CLEANER_REPLACEMENT_PATTERNS } from '../constants';
  ```

## Low Priority Issues

### 3. Absolute File Paths in Documentation
- **Source**: copilot-pull-request-reviewer[bot] on PR #78
- **Severity**: LOW
- **Location**: `CLEANER_CONSTANTS_REFACTOR_SUMMARY.md#L163`
- **Description**: Documentation contains absolute local file paths exposing developer environment
- **Impact**: Documentation quality, no functional impact
- **Fix**: Replace `/Users/yuyamukai/Eureka/mad_spark_multiagent/` with relative paths

### 4. Documentation Formatting Issues
- **Source**: copilot-pull-request-reviewer[bot] on PR #78
- **Severity**: LOW
- **Locations**: 
  - `web/test_ui_behavior.md:40` - Vague WebSocket error note
  - `README.md:540` - Inconsistent list formatting
  - `README.md:608` - Numbered list restart error
- **Fix**: Standardize formatting and clarify error descriptions

## Enhancement Suggestions

### From claude[bot] (PR #78):
1. **Type Safety**: Improve None handling in `clean_improved_idea()`
2. **Documentation**: Add performance benchmarks
3. **Web Optimization**: Consider batch cleaning for multiple results

## Tracking Information
- **Last Updated**: 2025-07-13 21:00 UTC
- **PRs Referenced**: #78
- **Next Review**: After addressing high priority issues

## Action Items for Next Session
1. Create bug fix PR addressing timeout and TypeScript issues
2. Update documentation formatting in a cleanup PR
3. Consider enhancement suggestions for future iterations